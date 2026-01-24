"""
ЭТАП 3 — СЕМАНТИКА, РОЛИ, СЛОИ
==================================

🎯 ЦЕЛЬ: Сделать так, чтобы система понимала, что она чертит.
Не «набор линий», а:
- где талия
- где бок
- где низ
- где середина
- где конструктивные точки

Это обязательный шаг перед:
- размерами
- градацией
- ML
- производством
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class PointRole(Enum):
    """Роли точек лекала"""
    WAIST_CENTER = "WAIST_CENTER"
    WAIST_SIDE = "WAIST_SIDE"
    HIP_SIDE = "HIP_SIDE"
    HEM_SIDE = "HEM_SIDE"
    HEM_CENTER = "HEM_CENTER"
    CENTER_LINE = "CENTER_LINE"
    UNKNOWN = "UNKNOWN"


class SegmentRole(Enum):
    """Роли сегментов лекала"""
    WAIST = "WAIST"
    SIDE = "SIDE"
    HEM = "HEM"
    CENTER = "CENTER"
    UNKNOWN = "UNKNOWN"


@dataclass
class PatternPoint:
    """
    📍 Точка с ролью
    
    1️⃣ ВВОДИМ СТРУКТУРЫ ДАННЫХ (МИНИМУМ, НО ПРАВИЛЬНО)
    """
    name: str
    role: str
    x: float
    y: float
    
    def xy(self) -> tuple[float, float]:
        """Координаты точки"""
        return (self.x, self.y)
    
    def is_waist(self) -> bool:
        """Точка на талии"""
        return self.role in [PointRole.WAIST_CENTER.value, PointRole.WAIST_SIDE.value]
    
    def is_hem(self) -> bool:
        """Точка на низу"""
        return self.role in [PointRole.HEM_SIDE.value, PointRole.HEM_CENTER.value]
    
    def is_side(self) -> bool:
        """Точка на боку"""
        return self.role in [PointRole.WAIST_SIDE.value, PointRole.HIP_SIDE.value, PointRole.HEM_SIDE.value]
    
    def is_center(self) -> bool:
        """Точка на середине"""
        return self.role in [PointRole.WAIST_CENTER.value, PointRole.HEM_CENTER.value, PointRole.CENTER_LINE.value]


@dataclass
class PatternSegment:
    """
    📐 Сегмент с ролью
    
    2️⃣ СОБИРАЕМ КОНТУР С РОЛЯМИ
    """
    start: PatternPoint
    end: PatternPoint
    bulge: float = 0.0
    role: str = SegmentRole.UNKNOWN.value
    
    def is_arc(self) -> bool:
        """Это дуга?"""
        return abs(self.bulge) > 1e-6
    
    def is_line(self) -> bool:
        """Это линия?"""
        return not self.is_arc()
    
    def is_waist(self) -> bool:
        """Сегмент талии"""
        return self.role == SegmentRole.WAIST.value
    
    def is_side(self) -> bool:
        """Сегмент бока"""
        return self.role == SegmentRole.SIDE.value
    
    def is_hem(self) -> bool:
        """Сегмент низа"""
        return self.role == SegmentRole.HEM.value
    
    def is_center(self) -> bool:
        """Сегмент середины"""
        return self.role == SegmentRole.CENTER.value
    
    def length(self) -> float:
        """Длина сегмента"""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return (dx * dx + dy * dy) ** 0.5


@dataclass
class PatternModel:
    """
    🏗️ МОДЕЛЬ ЛЕКАЛА (PatternModel)
    
    3️⃣ ВВОДИМ МОДЕЛЬ ЛЕКАЛА
    📌 Это сердце системы.
    """
    points: List[PatternPoint]
    segments: List[PatternSegment]
    
    def get_segments_by_role(self, role: str) -> List[PatternSegment]:
        """Получить сегменты по роли"""
        return [s for s in self.segments if s.role == role]
    
    def get_points_by_role(self, role: str) -> List[PatternPoint]:
        """Получить точки по роли"""
        return [p for p in self.points if p.role == role]
    
    def get_waist_segments(self) -> List[PatternSegment]:
        """Сегменты талии"""
        return self.get_segments_by_role(SegmentRole.WAIST.value)
    
    def get_side_segments(self) -> List[PatternSegment]:
        """Сегменты бока"""
        return self.get_segments_by_role(SegmentRole.SIDE.value)
    
    def get_hem_segments(self) -> List[PatternSegment]:
        """Сегменты низа"""
        return self.get_segments_by_role(SegmentRole.HEM.value)
    
    def get_center_segments(self) -> List[PatternSegment]:
        """Сегменты середины"""
        return self.get_segments_by_role(SegmentRole.CENTER.value)
    
    def get_waist_points(self) -> List[PatternPoint]:
        """Точки талии"""
        return [p for p in self.points if p.is_waist()]
    
    def get_hem_points(self) -> List[PatternPoint]:
        """Точки низа"""
        return [p for p in self.points if p.is_hem()]
    
    def get_side_points(self) -> List[PatternPoint]:
        """Точки бока"""
        return [p for p in self.points if p.is_side()]
    
    def get_center_points(self) -> List[PatternPoint]:
        """Точки середины"""
        return [p for p in self.points if p.is_center()]
    
    def get_total_length(self) -> float:
        """Общая длина контура"""
        return sum(seg.length() for seg in self.segments)
    
    def get_arc_count(self) -> int:
        """Количество дуг"""
        return sum(1 for seg in self.segments if seg.is_arc())
    
    def get_line_count(self) -> int:
        """Количество линий"""
        return sum(1 for seg in self.segments if seg.is_line())


class PatternSemanticsBuilder:
    """
    🔧 СТРОИТЕЛЬ СЕМАНТИЧЕСКОЙ МОДЕЛИ
    
    На базе уже работающего конструктора юбки:
    """
    
    def __init__(self):
        self.point_counter = 0
        self.segment_counter = 0
    
    def create_point(self, name: str, role: str, x: float, y: float) -> PatternPoint:
        """Создать точку с ролью"""
        self.point_counter += 1
        return PatternPoint(
            name=name,
            role=role,
            x=x,
            y=y
        )
    
    def create_segment(self, start: PatternPoint, end: PatternPoint, 
                     bulge: float = 0.0, role: str = SegmentRole.UNKNOWN.value) -> PatternSegment:
        """Создать сегмент с ролью"""
        self.segment_counter += 1
        return PatternSegment(
            start=start,
            end=end,
            bulge=bulge,
            role=role
        )
    
    def build_pattern_segments(self, points: List[tuple[float, float]], 
                           bulges: List[float]) -> List[PatternSegment]:
        """
        📐 СОБИРАЕМ КОНТУР С РОЛЯМИ
        
        📌 Важно: мы не меняем геометрию, только добавляем смысл.
        """
        # Создаем точки с ролями
        pattern_points = []
        point_names = ['A', 'M1', 'B', 'M2', 'F', 'H_mid', 'E', 'C_mid', 'A']
        point_roles = [
            PointRole.WAIST_CENTER.value,  # A
            PointRole.WAIST_CENTER.value,  # M1
            PointRole.WAIST_SIDE.value,    # B
            PointRole.HIP_SIDE.value,      # M2
            PointRole.HEM_SIDE.value,      # F
            PointRole.HEM_CENTER.value,    # H_mid
            PointRole.HEM_CENTER.value,    # E
            PointRole.CENTER_LINE.value,    # C_mid
            PointRole.WAIST_CENTER.value   # A (замыкание)
        ]
        
        for i, ((x, y), name, role) in enumerate(zip(points, point_names, point_roles)):
            pattern_points.append(
                self.create_point(f"{name}_{i}", role, x, y)
            )
        
        # Создаем сегменты с ролями
        segments = []
        
        for i in range(len(points) - 1):
            role = SegmentRole.UNKNOWN.value
            
            # Определяем роль сегмента
            if i in (0, 1):  # A → M1 → B
                role = SegmentRole.WAIST.value
            elif i in (2, 3):  # B → M2 → F
                role = SegmentRole.SIDE.value
            elif i in (4, 5):  # F → H_mid → E
                role = SegmentRole.HEM.value
            else:  # E → C_mid → A
                role = SegmentRole.CENTER.value
            
            bulge = bulges[i] if i < len(bulges) else 0.0
            
            segments.append(
                self.create_segment(
                    start=pattern_points[i],
                    end=pattern_points[i + 1],
                    bulge=bulge,
                    role=role
                )
            )
        
        return segments
    
    def build_pattern_model(self, points: List[tuple[float, float]], 
                          bulges: List[float]) -> PatternModel:
        """
        Построить полную семантическую модель
        
        Args:
            points: List[tuple[float, float]] - точки контура
            bulges: List[float] - bulge значения
            
        Returns:
            PatternModel - семантическая модель
        """
        # Создаем точки с ролями
        pattern_points = []
        point_names = ['A', 'M1', 'B', 'M2', 'F', 'H_mid', 'E', 'C_mid', 'A']
        point_roles = [
            PointRole.WAIST_CENTER.value,  # A
            PointRole.WAIST_CENTER.value,  # M1
            PointRole.WAIST_SIDE.value,    # B
            PointRole.HIP_SIDE.value,      # M2
            PointRole.HEM_SIDE.value,      # F
            PointRole.HEM_CENTER.value,    # H_mid
            PointRole.HEM_CENTER.value,    # E
            PointRole.CENTER_LINE.value,    # C_mid
            PointRole.WAIST_CENTER.value   # A (замыкание)
        ]
        
        for i, ((x, y), name, role) in enumerate(zip(points, point_names, point_roles)):
            pattern_points.append(
                self.create_point(f"{name}_{i}", role, x, y)
            )
        
        # Создаем сегменты с ролями
        segments = self.build_pattern_segments(points, bulges)
        
        return PatternModel(
            points=pattern_points,
            segments=segments
        )


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ PATTERN SEMANTICS")
    print("=" * 50)
    
    # Тестовый контур (юбка с клёшом)
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
    
    # Создаем семантическую модель
    builder = PatternSemanticsBuilder()
    model = builder.build_pattern_model(points, bulges)
    
    print(f"\n🏗️ Семантическая модель:")
    print(f"   Точек: {len(model.points)}")
    print(f"   Сегментов: {len(model.segments)}")
    print(f"   Дуг: {model.get_arc_count()}")
    print(f"   Линий: {model.get_line_count()}")
    print(f"   Общая длина: {model.get_total_length():.1f} мм")
    
    # Анализ по ролям
    print(f"\n📍 Точки по ролям:")
    for role in [PointRole.WAIST_CENTER.value, PointRole.WAIST_SIDE.value, 
                PointRole.HEM_SIDE.value, PointRole.HEM_CENTER.value]:
        role_points = model.get_points_by_role(role)
        print(f"   {role}: {len(role_points)} точек")
        for point in role_points:
            print(f"      {point.name}: ({point.x:.1f}, {point.y:.1f})")
    
    print(f"\n📐 Сегменты по ролям:")
    for role in [SegmentRole.WAIST.value, SegmentRole.SIDE.value, 
                SegmentRole.HEM.value, SegmentRole.CENTER.value]:
        role_segments = model.get_segments_by_role(role)
        print(f"   {role}: {len(role_segments)} сегментов")
        for seg in role_segments:
            seg_type = "дуга" if seg.is_arc() else "линия"
            print(f"      {seg.start.name} → {seg.end.name}: {seg_type} (bulge={seg.bulge:.3f})")
    
    print(f"\n✅ Pattern Semantics готов!")
