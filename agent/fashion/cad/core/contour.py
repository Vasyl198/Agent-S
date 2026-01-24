"""
2️⃣ ЕДИНСТВЕННЫЙ МОДУЛЬ КОНТУРА
=================================

📁 agent/fashion/cad/core/contour.py

Сюда сливаются:
- contour_builder.py ❌
- куски proper_dxf_exporter ❌
- логика замыкания ✅

Функции:
- сортировка сегментов
- проверка замыкания
- устранение разрывов
- нормализация направления (CW / CCW)

📌 DXF-экспортёр НЕ ИМЕЕТ ПРАВА это делать
"""

from typing import List, Optional, Tuple
import math

from .geometry import Point, Segment, Contour, SegmentRole, PointRole


class ContourBuilder:
    """
    🔧 СТРОИТЕЛЬ КОНТУРОВ - ЕДИНСТВЕННЫЙ
    
    🚫 ЗАПРЕЩЕНО: создавать контуры в других модулях
    ✅ РАЗРЕШЕНО: использовать только этот класс
    """
    
    def __init__(self):
        self.segments: List[Segment] = []
        self.tolerance: float = 1e-6
    
    def add_segment(self, segment: Segment) -> 'ContourBuilder':
        """Добавить сегмент"""
        self.segments.append(segment)
        return self
    
    def add_point(self, point: Point, role: Optional[SegmentRole] = None, bulge: float = 0.0) -> 'ContourBuilder':
        """Добавить точку (создаст сегмент от последней точки)"""
        if self.segments:
            last_segment = self.segments[-1]
            segment = Segment(last_segment.end, point, role, bulge)
            self.segments.append(segment)
        else:
            # Первый сегмент - создаем фиктивную начальную точку
            start = Point(0, 0)  # Будет заменена при замыкании
            segment = Segment(start, point, role, bulge)
            self.segments.append(segment)
        
        return self
    
    def close(self) -> 'ContourBuilder':
        """Замкнуть контур"""
        if len(self.segments) < 2:
            raise ValueError("Нужно минимум 2 сегмента для замыкания")
        
        first_point = self.segments[0].start
        last_point = self.segments[-1].end
        
        if first_point.distance_to(last_point) > self.tolerance:
            # Добавляем замыкающий сегмент
            closing_segment = Segment(last_point, first_point, SegmentRole.UNKNOWN)
            self.segments.append(closing_segment)
        
        return self
    
    def build(self, closed: bool = True) -> Contour:
        """Построить контур"""
        if closed:
            self.close()
        
        return Contour(self.segments.copy(), closed)
    
    def clear(self) -> 'ContourBuilder':
        """Очистить строителя"""
        self.segments.clear()
        return self


class ContourProcessor:
    """
    🔧 ОБРАБОТЧИК КОНТУРОВ
    
    Функции:
    - сортировка сегментов
    - проверка замыкания
    - устранение разрывов
    - нормализация направления (CW / CCW)
    """
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
    
    def sort_segments_by_connection(self, segments: List[Segment]) -> List[Segment]:
        """
        Сортировать сегменты по последовательному соединению
        
        Args:
            segments: список сегментов
            
        Returns:
            отсортированные сегменты
        """
        if not segments:
            return []
        
        if len(segments) == 1:
            return segments
        
        sorted_segments = [segments[0]]
        remaining_segments = segments[1:]
        
        while remaining_segments:
            current_end = sorted_segments[-1].end
            next_segment = None
            next_index = None
            
            # Ищем сегмент, который начинается с текущей конечной точки
            for i, seg in enumerate(remaining_segments):
                if seg.start.distance_to(current_end) <= self.tolerance:
                    next_segment = seg
                    next_index = i
                    break
            
            if next_segment is None:
                # Пробуем развернуть сегменты
                for i, seg in enumerate(remaining_segments):
                    if seg.end.distance_to(current_end) <= self.tolerance:
                        next_segment = seg.reverse()
                        next_index = i
                        break
            
            if next_segment is None:
                raise ValueError("Не удалось найти соединяющий сегмент. Контур разорван.")
            
            sorted_segments.append(next_segment)
            remaining_segments.pop(next_index)
        
        return sorted_segments
    
    def check_closure(self, contour: Contour) -> Tuple[bool, float]:
        """
        Проверить замыкание контура
        
        Args:
            contour: контур для проверки
            
        Returns:
            (замкнут, расстояние_разрыва)
        """
        if not contour.segments:
            return True, 0.0
        
        first_point = contour.segments[0].start
        last_point = contour.segments[-1].end
        
        gap_distance = first_point.distance_to(last_point)
        is_closed = gap_distance <= self.tolerance
        
        return is_closed, gap_distance
    
    def fix_gaps(self, contour: Contour) -> Contour:
        """
        Устранить разрывы в контуре
        
        Args:
            contour: контур с разрывами
            
        Returns:
            исправленный контур
        """
        segments = contour.segments.copy()
        
        for i in range(len(segments)):
            current_end = segments[i].end
            next_start = segments[(i + 1) % len(segments)].start
            
            if current_end.distance_to(next_start) > self.tolerance:
                # Создаем соединительный сегмент
                bridge_segment = Segment(current_end, next_start, SegmentRole.UNKNOWN)
                segments.insert(i + 1, bridge_segment)
        
        return Contour(segments, contour.closed)
    
    def normalize_direction(self, contour: Contour, clockwise: bool = True) -> Contour:
        """
        Нормализовать направление контура (CW / CCW)
        
        Args:
            contour: контур
            clockwise: True для CW, False для CCW
            
        Returns:
            контур с нормализованным направлением
        """
        # Вычисляем площадь со знаком
        signed_area = 0.0
        n = len(contour.segments)
        
        for i in range(n):
            p1 = contour.segments[i].start
            p2 = contour.segments[i].end
            signed_area += (p1.x * p2.y) - (p2.x * p1.y)
        
        signed_area /= 2.0
        
        # Если направление не совпадает с требуемым, разворачиваем
        if (clockwise and signed_area > 0) or (not clockwise and signed_area < 0):
            return contour.reverse()
        
        return contour
    
    def remove_duplicate_points(self, contour: Contour) -> Contour:
        """
        Удалить дублирующиеся точки
        
        Args:
            contour: контур с дубликатами
            
        Returns:
            контур без дубликатов
        """
        filtered_segments = []
        
        for segment in contour.segments:
            # Проверяем, что начальная точка не совпадает с конечной предыдущего сегмента
            if not filtered_segments:
                filtered_segments.append(segment)
            else:
                last_segment = filtered_segments[-1]
                if segment.start.distance_to(last_segment.end) > self.tolerance:
                    filtered_segments.append(segment)
                else:
                    # Заменяем последний сегмент
                    filtered_segments[-1] = Segment(
                        last_segment.start,
                        segment.end,
                        segment.role,
                        segment.bulge
                    )
        
        return Contour(filtered_segments, contour.closed)
    
    def remove_zero_length_segments(self, contour: Contour) -> Contour:
        """
        Удалить сегменты нулевой длины
        
        Args:
            contour: контур с нулевыми сегментами
            
        Returns:
            контур без нулевых сегментов
        """
        filtered_segments = [
            seg for seg in contour.segments 
            if seg.length > self.tolerance
        ]
        
        return Contour(filtered_segments, contour.closed)
    
    def process_contour(self, contour: Contour, clockwise: bool = True) -> Contour:
        """
        Полная обработка контура
        
        Args:
            contour: исходный контур
            clockwise: направление (True для CW)
            
        Returns:
            обработанный контур
        """
        # 1. Сортировка сегментов
        sorted_segments = self.sort_segments_by_connection(contour.segments)
        temp_contour = Contour(sorted_segments, contour.closed)
        
        # 2. Удаление дубликатов
        temp_contour = self.remove_duplicate_points(temp_contour)
        
        # 3. Удаление нулевых сегментов
        temp_contour = self.remove_zero_length_segments(temp_contour)
        
        # 4. Исправление разрывов
        temp_contour = self.fix_gaps(temp_contour)
        
        # 5. Нормализация направления
        temp_contour = self.normalize_direction(temp_contour, clockwise)
        
        # 6. Финальная проверка замыкания
        is_closed, gap = self.check_closure(temp_contour)
        if not is_closed:
            print(f"⚠️ ВНИМАНИЕ: Контур не замкнут, разрыв = {gap:.6f}")
        
        return temp_contour
    
    def merge_contours(self, contours: List[Contour]) -> Contour:
        """
        Объединить несколько контуров в один
        
        Args:
            contours: список контуров
            
        Returns:
            объединенный контур
        """
        if not contours:
            raise ValueError("Список контуров пуст")
        
        if len(contours) == 1:
            return contours[0]
        
        all_segments = []
        for contour in contours:
            all_segments.extend(contour.segments)
        
        # Сортируем все сегменты
        sorted_segments = self.sort_segments_by_connection(all_segments)
        
        return Contour(sorted_segments, True)


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_contour_builder() -> ContourBuilder:
    """Создать строителя контура - ЕДИНСТВЕННЫЙ СПОСОБ"""
    return ContourBuilder()


def process_contour(contour: Contour, clockwise: bool = True, tolerance: float = 1e-6) -> Contour:
    """Обработать контур - ЕДИНСТВЕННЫЙ СПОСОБ"""
    processor = ContourProcessor(tolerance)
    return processor.process_contour(contour, clockwise)


def merge_contours(contours: List[Contour]) -> Contour:
    """Объединить контуры - ЕДИНСТВЕННЫЙ СПОСОБ"""
    processor = ContourProcessor()
    return processor.merge_contours(contours)


import logging
logger = logging.getLogger(__name__)

logger.debug("CAD Core Contour loaded")
