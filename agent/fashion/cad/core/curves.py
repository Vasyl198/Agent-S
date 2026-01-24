"""
4️⃣ CURVES = НЕ ЭКСПОРТ, А МАТЕМАТИКА
========================================

📁 agent/fashion/cad/core/curves.py

Сюда:
- curve_reconstruction.py
- сглаживание
- аппроксимация
- spline → bulge

📌 Экспортёры НЕ ВОССТАНАВЛИВАЮТ КРИВЫЕ
"""

from typing import List, Tuple, Optional
import math
import numpy as np

from .geometry import Point, Segment, Contour, SegmentRole


class CurveProcessor:
    """
    🌊 ОБРАБОТЧИК КРИВЫХ - ЕДИНСТВЕННЫЙ
    
    🚫 ЗАПРЕЩЕНО: обрабатывать кривые в других модулях
    ✅ РАЗРЕШЕНО: использовать только этот класс
    """
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
    
    def smooth_contour(self, contour: Contour, smoothing_factor: float = 0.1) -> Contour:
        """
        Сгладить контур
        
        Args:
            contour: исходный контур
            smoothing_factor: фактор сглаживания (0-1)
            
        Returns:
            сглаженный контур
        """
        if smoothing_factor <= 0:
            return contour
        
        points = contour.points
        if len(points) < 3:
            return contour
        
        smoothed_points = []
        
        for i in range(len(points)):
            prev_point = points[i - 1]
            current_point = points[i]
            next_point = points[(i + 1) % len(points)]
            
            # Простое сглаживание скользящим средним
            smoothed_x = (prev_point.x + 2 * current_point.x + next_point.x) / 4
            smoothed_y = (prev_point.y + 2 * current_point.y + next_point.y) / 4
            
            # Интерполяция между исходной и сглаженной точкой
            final_x = current_point.x + (smoothed_x - current_point.x) * smoothing_factor
            final_y = current_point.y + (smoothed_y - current_point.y) * smoothing_factor
            
            smoothed_points.append(Point(final_x, final_y, current_point.role))
        
        # Создаем новые сегменты
        smoothed_segments = []
        for i in range(len(smoothed_points)):
            start = smoothed_points[i]
            end = smoothed_points[(i + 1) % len(smoothed_points)]
            
            # Находим исходный сегмент для сохранения роли и bulge
            original_seg = contour.segments[i]
            smoothed_segments.append(Segment(
                start=start,
                end=end,
                role=original_seg.role,
                bulge=original_seg.bulge
            ))
        
        return Contour(smoothed_segments, contour.closed)
    
    def approximate_curve(self, points: List[Point], tolerance: float = None) -> List[Segment]:
        """
        Аппроксимировать кривую отрезками
        
        Args:
            points: точки кривой
            tolerance: допуск аппроксимации
            
        Returns:
            аппроксимирующие сегменты
        """
        if tolerance is None:
            tolerance = self.tolerance
        
        if len(points) < 2:
            return []
        
        # Алгоритм Дугласа-Пекера
        if len(points) <= 2:
            return [Segment(points[0], points[-1])]
        
        # Рекурсивная аппроксимация
        def douglas_peucker(point_list, start_idx, end_idx):
            if end_idx <= start_idx + 1:
                return [start_idx, end_idx]
            
            # Находим точку с максимальным расстоянием
            max_distance = 0
            max_index = start_idx
            
            start_point = point_list[start_idx]
            end_point = point_list[end_idx]
            
            for i in range(start_idx + 1, end_idx):
                distance = self._point_to_line_distance(point_list[i], start_point, end_point)
                if distance > max_distance:
                    max_distance = distance
                    max_index = i
            
            # Если расстояние больше допуска, рекурсивно делим
            if max_distance > tolerance:
                left_result = douglas_peucker(point_list, start_idx, max_index)
                right_result = douglas_peucker(point_list, max_index, end_idx)
                
                # Объединяем результаты (избегая дублирования)
                return left_result[:-1] + right_result
            else:
                return [start_idx, end_idx]
        
        # Применяем алгоритм
        result_indices = douglas_peucker(points, 0, len(points) - 1)
        
        # Создаем сегменты
        segments = []
        for i in range(len(result_indices) - 1):
            start_idx = result_indices[i]
            end_idx = result_indices[i + 1]
            segments.append(Segment(points[start_idx], points[end_idx]))
        
        return segments
    
    def spline_to_bulge(self, spline_points: List[Point], num_segments: int = 4) -> List[Segment]:
        """
        Преобразовать сплайн в сегменты с bulge
        
        Args:
            spline_points: точки сплайна
            num_segments: количество сегментов на сплайн
            
        Returns:
            сегменты с bulge
        """
        if len(spline_points) < 2:
            return []
        
        if len(spline_points) == 2:
            return [Segment(spline_points[0], spline_points[1])]
        
        # Разбиваем сплайн на сегменты
        segments = []
        points_per_segment = max(2, len(spline_points) // num_segments)
        
        for i in range(0, len(spline_points) - 1, points_per_segment - 1):
            start_idx = i
            end_idx = min(i + points_per_segment - 1, len(spline_points) - 1)
            
            start_point = spline_points[start_idx]
            end_point = spline_points[end_idx]
            
            # Вычисляем bulge по промежуточным точкам
            if end_idx - start_idx > 1:
                # Используем среднюю точку для вычисления bulge
                mid_idx = (start_idx + end_idx) // 2
                mid_point = spline_points[mid_idx]
                
                bulge = self._calculate_bulge_from_three_points(
                    start_point, mid_point, end_point
                )
            else:
                bulge = 0.0
            
            segments.append(Segment(start_point, end_point, bulge=bulge))
        
        return segments
    
    def reconstruct_curve_from_segments(self, segments: List[Segment], 
                                   resolution: int = 20) -> List[Point]:
        """
        Реконструировать кривую из сегментов
        
        Args:
            segments: сегменты (включая дуги)
            resolution: разрешение на каждый сегмент
            
        Returns:
            точки реконструированной кривой
        """
        curve_points = []
        
        for i, segment in enumerate(segments):
            if segment.is_arc:
                # Реконструируем дугу
                arc_points = self._reconstruct_arc(segment, resolution)
                curve_points.extend(arc_points[:-1])  # Исключаем последнюю точку
            else:
                # Прямой сегмент
                curve_points.append(segment.start)
            
            # Добавляем конечную точку последнего сегмента
            if i == len(segments) - 1:
                curve_points.append(segment.end)
        
        return curve_points
    
    def optimize_bulge_values(self, contour: Contour) -> Contour:
        """
        Оптимизировать значения bulge для лучшего представления дуг
        
        Args:
            contour: контур с дугами
            
        Returns:
            контур с оптимизированными bulge
        """
        optimized_segments = []
        
        for segment in contour.segments:
            if segment.is_arc:
                # Реконструируем дугу
                arc_points = self._reconstruct_arc(segment, 10)
                
                if len(arc_points) >= 3:
                    # Вычисляем новый bulge по трем точкам
                    start = arc_points[0]
                    mid = arc_points[len(arc_points) // 2]
                    end = arc_points[-1]
                    
                    new_bulge = self._calculate_bulge_from_three_points(start, mid, end)
                    
                    optimized_segment = Segment(
                        start=segment.start,
                        end=segment.end,
                        role=segment.role,
                        bulge=new_bulge
                    )
                    optimized_segments.append(optimized_segment)
                else:
                    optimized_segments.append(segment)
            else:
                optimized_segments.append(segment)
        
        return Contour(optimized_segments, contour.closed)
    
    def _point_to_line_distance(self, point: Point, line_start: Point, line_end: Point) -> float:
        """Расстояние от точки до отрезка"""
        # Вектор отрезка
        dx = line_end.x - line_start.x
        dy = line_end.y - line_start.y
        
        # Длина отрезка
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return point.distance_to(line_start)
        
        # Параметр точки на отрезке
        t = max(0, min(1, ((point.x - line_start.x) * dx + 
                           (point.y - line_start.y) * dy) / (length * length)))
        
        # Ближайшая точка на отрезке
        projection = Point(
            line_start.x + t * dx,
            line_start.y + t * dy
        )
        
        return point.distance_to(projection)
    
    def _calculate_bulge_from_three_points(self, start: Point, mid: Point, end: Point) -> float:
        """Вычислить bulge по трем точкам"""
        # Вектор отрезка
        dx = end.x - start.x
        dy = end.y - start.y
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return 0.0
        
        # Перпендикулярное расстояние средней точки до отрезка
        distance = self._point_to_line_distance(mid, start, end)
        
        # Определяем знак bulge по направлению изгиба
        cross_product = (mid.x - start.x) * dy - (mid.y - start.y) * dx
        
        if cross_product < 0:
            distance = -distance
        
        # Bulge = 2 * distance / length
        bulge = 2 * distance / length
        
        return bulge
    
    def _reconstruct_arc(self, segment: Segment, resolution: int) -> List[Point]:
        """Реконструировать дугу из сегмента с bulge"""
        if not segment.is_arc:
            return [segment.start, segment.end]
        
        # Параметры дуги
        start = segment.start
        end = segment.end
        bulge = segment.bulge
        
        # Вычисляем центр и радиус дуги
        center, radius, start_angle, end_angle = self._arc_parameters(start, end, bulge)
        
        # Генерируем точки дуги
        points = []
        angle_step = (end_angle - start_angle) / resolution
        
        for i in range(resolution + 1):
            angle = start_angle + i * angle_step
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            points.append(Point(x, y))
        
        return points
    
    def _arc_parameters(self, start: Point, end: Point, bulge: float) -> Tuple[Point, float, float, float]:
        """Вычислить параметры дуги: центр, радиус, начальный и конечный углы"""
        # Середина отрезка
        mid_x = (start.x + end.x) / 2
        mid_y = (start.y + end.y) / 2
        
        # Вектор отрезка
        dx = end.x - start.x
        dy = end.y - start.y
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return Point(start.x, start.y), 0, 0, 0
        
        # Перпендикуляр к отрезку
        perp_x = -dy / length
        perp_y = dx / length
        
        # Радиус дуги
        radius = abs(length * (bulge * bulge + 1) / (4 * bulge)) if bulge != 0 else float('inf')
        
        # Центр дуги
        if radius != float('inf'):
            center_distance = radius - length * bulge / 2
            center_x = mid_x + perp_x * center_distance
            center_y = mid_y + perp_y * center_distance
            center = Point(center_x, center_y)
        else:
            center = Point(mid_x, mid_y)
            radius = 0
        
        # Углы
        start_angle = math.atan2(start.y - center.y, start.x - center.x)
        end_angle = math.atan2(end.y - center.y, end.x - center.x)
        
        return center, radius, start_angle, end_angle


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def smooth_contour(contour: Contour, smoothing_factor: float = 0.1, 
                 tolerance: float = 1e-6) -> Contour:
    """Сгладить контур - ЕДИНСТВЕННЫЙ СПОСОБ"""
    processor = CurveProcessor(tolerance)
    return processor.smooth_contour(contour, smoothing_factor)


def approximate_curve(points: List[Point], tolerance: float = 1e-6) -> List[Segment]:
    """Аппроксимировать кривую - ЕДИНСТВЕННЫЙ СПОСОБ"""
    processor = CurveProcessor(tolerance)
    return processor.approximate_curve(points, tolerance)


def spline_to_bulge(spline_points: List[Point], num_segments: int = 4) -> List[Segment]:
    """Преобразовать сплайн в bulge - ЕДИНСТВЕННЫЙ СПОСОБ"""
    processor = CurveProcessor()
    return processor.spline_to_bulge(spline_points, num_segments)


def optimize_bulge_values(contour: Contour, tolerance: float = 1e-6) -> Contour:
    """Оптимизировать bulge значения - ЕДИНСТВЕННЫЙ СПОСОБ"""
    processor = CurveProcessor(tolerance)
    return processor.optimize_bulge_values(contour)


import logging
logger = logging.getLogger(__name__)

logger.debug("CAD Core Curves loaded")
