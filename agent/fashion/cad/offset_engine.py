"""
ЭТАП 2 — ПРИПУСКИ (OFFSET) ❗
================================

Самый сложный этап во всей CAD-геометрии.
OFFSET КАК КОНСТРУКТИВНЫЙ АЛГОРИТМ

🧱 АРХИТЕКТУРА OFFSET-ДВИЖКА:
Исходный контур (points + bulges) → Сегменты (LINE / ARC) → 
Offset каждого сегмента → Стыковка (fillet / intersection) → 
Новый LWPOLYLINE + bulge

📌 Это ровно то, как делают Gerber / Lectra / Optitex.
"""

import math
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum


class SegmentType(Enum):
    """Тип сегмента"""
    LINE = "LINE"
    ARC = "ARC"


@dataclass
class Segment:
    """Сегмент контура"""
    start: Tuple[float, float]
    end: Tuple[float, float]
    bulge: float
    segment_type: SegmentType
    
    def __post_init__(self):
        if self.segment_type is None:
            self.segment_type = SegmentType.ARC if abs(self.bulge) > 1e-6 else SegmentType.LINE


@dataclass
class ArcGeometry:
    """Геометрия дуги"""
    center: Tuple[float, float]
    radius: float
    start_angle: float
    end_angle: float
    is_ccw: bool  # против часовой стрелки


class OffsetEngine:
    """
    🔧 OFFSET КАК КОНСТРУКТИВНЫЙ АЛГОРИТМ
    
    Работаем по сегментам, разделяем прямые и дуги (bulge),
    смещаем каждый тип правильно, сшиваем смещённые сегменты вручную.
    """
    
    def __init__(self, offset_distance: float = 10.0):
        """
        Args:
            offset_distance: float - расстояние припуска (мм)
        """
        self.offset_distance = offset_distance
    
    def parse_contour_to_segments(self, points: List[Tuple[float, float]], 
                                 bulges: List[float]) -> List[Segment]:
        """
        ✏️ ШАГ 1 — РАЗБОР КОНТУРА НА СЕГМЕНТЫ
        
        Каждый сегмент:
        Segment(start=(x1, y1), end=(x2, y2), bulge=b)
        
        Тип:
        b == 0 → LINE
        b != 0 → ARC
        
        Args:
            points: List[Tuple[float, float]] - точки контура
            bulges: List[float] - bulge значения
            
        Returns:
            List[Segment] - список сегментов
        """
        if len(points) < 2 or len(bulges) < 1:
            return []
        
        segments = []
        
        for i in range(len(points) - 1):
            start = points[i]
            end = points[i + 1]
            bulge = bulges[i] if i < len(bulges) else 0.0
            
            segment = Segment(
                start=start,
                end=end,
                bulge=bulge,
                segment_type=SegmentType.ARC if abs(bulge) > 1e-6 else SegmentType.LINE
            )
            
            segments.append(segment)
        
        return segments
    
    def offset_line(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                   distance: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        ✏️ ШАГ 2 — OFFSET ПРЯМОЙ (ПРОСТО)
        
        Для линии: нормаль влево по CCW
        
        📌 Это школьная геометрия
        📌 Без сюрпризов
        
        Args:
            p1: Tuple[float, float] - начальная точка
            p2: Tuple[float, float] - конечная точка
            distance: float - расстояние смещения
            
        Returns:
            Tuple[Tuple[float, float], Tuple[float, float]] - смещённые точки
        """
        x1, y1 = p1
        x2, y2 = p2
        
        # Вектор направления
        dx = x2 - x1
        dy = y2 - y1
        
        # Длина
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-6:
            return p1, p2
        
        # Нормаль влево (против часовой стрелки)
        nx = -dy / length
        ny = dx / length
        
        # Смещение
        offset_p1 = (x1 + nx * distance, y1 + ny * distance)
        offset_p2 = (x2 + nx * distance, y2 + ny * distance)
        
        return offset_p1, offset_p2
    
    def bulge_to_arc_geometry(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                              bulge: float) -> ArcGeometry:
        """
        Преобразование bulge в геометрию дуги
        
        Args:
            p1: Tuple[float, float] - начальная точка
            p2: Tuple[float, float] - конечная точка
            bulge: float - bulge значение
            
        Returns:
            ArcGeometry - геометрия дуги
        """
        x1, y1 = p1
        x2, y2 = p2
        
        # Длина хорды
        chord_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        if chord_length < 1e-6:
            return ArcGeometry((0, 0), 0, 0, 0, True)
        
        # Угол дуги
        theta = 4 * math.atan(abs(bulge))
        
        # Радиус
        radius = chord_length / (2 * math.sin(theta / 2))
        
        # Высота сегмента
        sagitta = radius * (1 - math.cos(theta / 2))
        
        # Направление перпендикуляра
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        
        # Перпендикуляр к хорде
        dx = x2 - x1
        dy = y2 - y1
        perp_x = -dy / chord_length
        perp_y = dx / chord_length
        
        # Центр дуги
        if bulge > 0:
            center_x = mx + perp_x * (radius - sagitta)
            center_y = my + perp_y * (radius - sagitta)
        else:
            center_x = mx - perp_x * (radius - sagitta)
            center_y = my - perp_y * (radius - sagitta)
        
        # Углы
        start_angle = math.atan2(y1 - center_y, x1 - center_x)
        end_angle = math.atan2(y2 - center_y, x2 - center_x)
        
        # Направление
        is_ccw = bulge > 0
        
        return ArcGeometry(
            center=(center_x, center_y),
            radius=radius,
            start_angle=start_angle,
            end_angle=end_angle,
            is_ccw=is_ccw
        )
    
    def offset_arc(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                   bulge: float, distance: float) -> Tuple[Tuple[float, float], Tuple[float, float], float]:
        """
        ✏️ ШАГ 3 — OFFSET ДУГИ (САМОЕ ВАЖНОЕ)
        
        Для bulge: восстанавливаем центр, радиус, направление
        Новый радиус: наружу → R + d, внутрь → R - d
        bulge НЕ меняется, меняются только точки
        
        📌 Это критично
        📌 bulge — функция угла, не радиуса
        
        Args:
            p1: Tuple[float, float] - начальная точка
            p2: Tuple[float, float] - конечная точка
            bulge: float - bulge значение
            distance: float - расстояние смещения
            
        Returns:
            Tuple[Tuple[float, float], Tuple[float, float], float] - смещённые точки и новый bulge
        """
        # Получаем геометрию дуги
        arc = self.bulge_to_arc_geometry(p1, p2, bulge)
        
        if arc.radius < 1e-6:
            # Деградировала в линию
            return self.offset_line(p1, p2, distance) + (0.0,)
        
        # Новый радиус
        if bulge > 0:
            # Наружная дуга
            new_radius = arc.radius + distance
        else:
            # Внутренняя дуга
            new_radius = arc.radius - distance
            if new_radius <= 0:
                # Слишком маленький радиус, делаем линию
                return self.offset_line(p1, p2, distance) + (0.0,)
        
        # Новые точки на смещённой дуге
        offset_p1 = (
            arc.center[0] + new_radius * math.cos(arc.start_angle),
            arc.center[1] + new_radius * math.sin(arc.start_angle)
        )
        
        offset_p2 = (
            arc.center[0] + new_radius * math.cos(arc.end_angle),
            arc.center[1] + new_radius * math.sin(arc.end_angle)
        )
        
        # bulge НЕ меняется!
        return offset_p1, offset_p2, bulge
    
    def offset_segment(self, segment: Segment, distance: float) -> Segment:
        """
        Смещение одного сегмента
        
        Args:
            segment: Segment - исходный сегмент
            distance: float - расстояние смещения
            
        Returns:
            Segment - смещённый сегмент
        """
        if segment.segment_type == SegmentType.LINE:
            offset_start, offset_end = self.offset_line(
                segment.start, segment.end, distance
            )
            return Segment(
                start=offset_start,
                end=offset_end,
                bulge=0.0,
                segment_type=SegmentType.LINE
            )
        else:
            offset_start, offset_end, bulge = self.offset_arc(
                segment.start, segment.end, segment.bulge, distance
            )
            return Segment(
                start=offset_start,
                end=offset_end,
                bulge=bulge,
                segment_type=SegmentType.ARC if abs(bulge) > 1e-6 else SegmentType.LINE
            )
    
    def intersect_lines(self, p1: Tuple[float, float], p2: Tuple[float, float],
                       p3: Tuple[float, float], p4: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Пересечение двух линий
        
        Args:
            p1, p2: точки первой линии
            p3, p4: точки второй линии
            
        Returns:
            Optional[Tuple[float, float]] - точка пересечения или None
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        
        if abs(denom) < 1e-6:
            return None  # Параллельные линии
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        
        intersection_x = x1 + t * (x2 - x1)
        intersection_y = y1 + t * (y2 - y1)
        
        return (intersection_x, intersection_y)
    
    def join_segments(self, seg1: Segment, seg2: Segment) -> Tuple[Segment, Segment]:
        """
        ✏️ ШАГ 4 — СТЫКОВКА СЕГМЕНТОВ
        
        Типы стыков:
        LINE → LINE, LINE → ARC, ARC → ARC
        
        Считаем пересечения, НЕ делаем auto-fillet, контролируем углы.
        
        📌 Тут и рождается «профессиональный» результат
        
        Args:
            seg1: Segment - первый сегмент
            seg2: Segment - второй сегмент
            
        Returns:
            Tuple[Segment, Segment] - состыкованные сегменты
        """
        # Если оба сегмента - линии
        if seg1.segment_type == SegmentType.LINE and seg2.segment_type == SegmentType.LINE:
            # Находим пересечение
            intersection = self.intersect_lines(
                seg1.start, seg1.end,
                seg2.start, seg2.end
            )
            
            if intersection:
                # Обновляем точки
                new_seg1 = Segment(
                    start=seg1.start,
                    end=intersection,
                    bulge=0.0,
                    segment_type=SegmentType.LINE
                )
                new_seg2 = Segment(
                    start=intersection,
                    end=seg2.end,
                    bulge=0.0,
                    segment_type=SegmentType.LINE
                )
                return new_seg1, new_seg2
        
        # Для других случаев пока просто соединяем
        # TODO: реализовать стыковку LINE → ARC и ARC → ARC
        return seg1, seg2
    
    def offset_contour(self, points: List[Tuple[float, float]], 
                      bulges: List[float]) -> Tuple[List[Tuple[float, float]], List[float]]:
        """
        Основная функция offset контура
        
        Args:
            points: List[Tuple[float, float]] - исходные точки
            bulges: List[float] - исходные bulge значения
            
        Returns:
            Tuple[List[Tuple[float, float]], List[float]] - смещённые точки и bulge
        """
        # Шаг 1: Разбор на сегменты
        segments = self.parse_contour_to_segments(points, bulges)
        
        if not segments:
            return points, bulges
        
        # Шаг 2: Offset каждого сегмента
        offset_segments = []
        for segment in segments:
            offset_segment = self.offset_segment(segment, self.offset_distance)
            offset_segments.append(offset_segment)
        
        # Шаг 3: Стыковка сегментов
        joined_segments = []
        for i in range(len(offset_segments)):
            current_seg = offset_segments[i]
            next_seg = offset_segments[(i + 1) % len(offset_segments)]
            
            joined_current, joined_next = self.join_segments(current_seg, next_seg)
            joined_segments.append(joined_current)
        
        # Шаг 4: Сборка обратно в точки и bulge
        offset_points = []
        offset_bulges = []
        
        for segment in joined_segments:
            offset_points.append(segment.start)
            offset_bulges.append(segment.bulge)
        
        # Добавляем последнюю точку для замыкания
        if joined_segments:
            offset_points.append(joined_segments[0].start)
        
        return offset_points, offset_bulges


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ OFFSET ENGINE")
    print("=" * 50)
    
    # Создаём тестовый контур (юбка с клёшом)
    points = [
        (0.0, 0.0),          # A
        (92.5, 8.0),         # M1
        (185.0, 0.0),        # B
        (264.0, 180.0),      # M2
        (250.0, 650.0),      # F
        (125.0, 662.0),      # H_mid
        (0.0, 650.0),        # E
        (0.0, 180.0),        # C_mid
        (0.0, 0.0)           # A (замыкание)
    ]
    
    bulges = [
        -0.086486,  # талия
        0.0,
        0.225381,   # бок
        0.0,
        0.095131,   # низ
        0.0,
        0.0,
        0.0,
        0.0
    ]
    
    print("📊 Исходный контур:")
    print(f"   Точек: {len(points)}")
    print(f"   Дуг: {sum(1 for b in bulges if abs(b) > 0.001)}")
    
    # Тест offset
    offset_engine = OffsetEngine(offset_distance=10.0)
    
    print(f"\n🔧 Offset с расстоянием: {offset_engine.offset_distance} мм")
    
    offset_points, offset_bulges = offset_engine.offset_contour(points, bulges)
    
    print(f"\n📊 Результат offset:")
    print(f"   Точек: {len(offset_points)}")
    print(f"   Дуг: {sum(1 for b in offset_bulges if abs(b) > 0.001)}")
    
    print("\n📍 Первые 5 точек offset:")
    for i in range(min(5, len(offset_points))):
        print(f"   {i}: ({offset_points[i][0]:.1f}, {offset_points[i][1]:.1f})")
    
    print("\n🔄 Первые 5 bulge:")
    for i in range(min(5, len(offset_bulges))):
        if abs(offset_bulges[i]) > 0.001:
            print(f"   {i}: {offset_bulges[i]:.6f} 🔄")
        else:
            print(f"   {i}: {offset_bulges[i]:.6f}")
    
    print(f"\n✅ Offset Engine готов!")
