"""
3️⃣ ВАЛИДАЦИЯ = ЧАСТЬ ЯДРА (НЕ DXF)
========================================

📁 agent/fashion/cad/core/validation.py

Сюда переносим ВСЁ из:
- validate_dxf.py
- проверки из exporters

Проверки:
- разрывы
- самопересечения
- дубли точек
- нулевые сегменты
- инвертированные bulge

📛 Если validation падает → DXF НЕ создаётся
"""

from typing import List, Tuple, Optional
import math

from .geometry import Point, Segment, Contour, SegmentRole, PointRole


class ValidationError:
    """Ошибка валидации"""
    def __init__(self, error_type: str, message: str, location: Optional[str] = None):
        self.error_type = error_type
        self.message = message
        self.location = location
    
    def __str__(self) -> str:
        location_str = f" ({self.location})" if self.location else ""
        return f"[{self.error_type}]{location_str}: {self.message}"


class GeometryValidator:
    """
    🔍 ВАЛИДАТОР ГЕОМЕТРИИ - ЕДИНСТВЕННЫЙ
    
    🚫 ЗАПРЕЩЕНО: валидировать геометрию в других модулях
    ✅ РАЗРЕШЕНО: использовать только этот класс
    """
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.errors: List[ValidationError] = []
    
    def validate_point(self, point: Point) -> List[ValidationError]:
        """Валидировать точку"""
        errors = []
        
        # Проверка на NaN
        if math.isnan(point.x) or math.isnan(point.y):
            errors.append(ValidationError(
                "INVALID_COORDINATES",
                f"Координаты содержат NaN: ({point.x}, {point.y})",
                f"Point({point.x}, {point.y})"
            ))
        
        # Проверка на бесконечность
        if math.isinf(point.x) or math.isinf(point.y):
            errors.append(ValidationError(
                "INVALID_COORDINATES", 
                f"Координаты содержат Inf: ({point.x}, {point.y})",
                f"Point({point.x}, {point.y})"
            ))
        
        return errors
    
    def validate_segment(self, segment: Segment) -> List[ValidationError]:
        """Валидировать сегмент"""
        errors = []
        
        # Валидация точек
        errors.extend(self.validate_point(segment.start))
        errors.extend(self.validate_point(segment.end))
        
        # Проверка на нулевую длину
        if segment.length <= self.tolerance:
            errors.append(ValidationError(
                "ZERO_LENGTH_SEGMENT",
                f"Сегмент имеет нулевую длину: {segment.length:.6f}",
                str(segment)
            ))
        
        # Проверка bulge
        if abs(segment.bulge) > 1e6:
            errors.append(ValidationError(
                "INVALID_BULGE",
                f"Bulge слишком большой: {segment.bulge}",
                str(segment)
            ))
        
        # Проверка на инвертированный bulge
        if segment.is_arc:
            # Проверяем, что bulge соответствует направлению дуги
            mid_point = segment.get_midpoint()
            expected_arc_mid = self._calculate_arc_midpoint(segment)
            
            if mid_point.distance_to(expected_arc_mid) > segment.length * 0.1:
                errors.append(ValidationError(
                    "INVERTED_BULGE",
                    f"Bulge не соответствует геометрии дуги: {segment.bulge}",
                    str(segment)
                ))
        
        return errors
    
    def validate_contour(self, contour: Contour) -> List[ValidationError]:
        """Валидировать контур"""
        errors = []
        
        # Проверка на пустой контур
        if not contour.segments:
            errors.append(ValidationError(
                "EMPTY_CONTOUR",
                "Контур не содержит сегментов",
                "Contour"
            ))
            return errors
        
        # Валидация всех сегментов
        for i, segment in enumerate(contour.segments):
            segment_errors = self.validate_segment(segment)
            for error in segment_errors:
                error.location = f"Segment[{i}]"
                errors.append(error)
        
        # Проверка замыкания
        if contour.closed:
            is_closed, gap = self._check_closure(contour)
            if not is_closed:
                errors.append(ValidationError(
                    "OPEN_CONTOUR",
                    f"Контур не замкнут, разрыв: {gap:.6f}",
                    "Contour closure"
                ))
        
        # Проверка на дублирующиеся точки
        duplicate_errors = self._check_duplicate_points(contour)
        errors.extend(duplicate_errors)
        
        # Проверка на самопересечения
        intersection_errors = self._check_self_intersections(contour)
        errors.extend(intersection_errors)
        
        # Проверка направления
        direction_errors = self._check_direction_consistency(contour)
        errors.extend(direction_errors)
        
        return errors
    
    def _check_closure(self, contour: Contour) -> Tuple[bool, float]:
        """Проверить замыкание контура"""
        first_point = contour.segments[0].start
        last_point = contour.segments[-1].end
        
        gap_distance = first_point.distance_to(last_point)
        is_closed = gap_distance <= self.tolerance
        
        return is_closed, gap_distance
    
    def _check_duplicate_points(self, contour: Contour) -> List[ValidationError]:
        """Проверить дублирующиеся точки"""
        errors = []
        seen_points = {}
        
        for i, point in enumerate(contour.points):
            point_key = (round(point.x, 6), round(point.y, 6))
            
            if point_key in seen_points:
                errors.append(ValidationError(
                    "DUPLICATE_POINT",
                    f"Дублирующаяся точка: ({point.x:.6f}, {point.y:.6f})",
                    f"Point[{i}]"
                ))
            else:
                seen_points[point_key] = i
        
        return errors
    
    def _check_self_intersections(self, contour: Contour) -> List[ValidationError]:
        """Проверить самопересечения контура"""
        errors = []
        
        for i in range(len(contour.segments)):
            for j in range(i + 1, len(contour.segments)):
                # Пропускаем соседние сегменты
                if abs(i - j) <= 1:
                    continue
                
                # Пропускаем первый и последний сегменты для замкнутого контура
                if contour.closed and ((i == 0 and j == len(contour.segments) - 1) or 
                                   (j == 0 and i == len(contour.segments) - 1)):
                    continue
                
                seg1 = contour.segments[i]
                seg2 = contour.segments[j]
                
                intersection = self._segment_intersection(seg1, seg2)
                if intersection:
                    errors.append(ValidationError(
                        "SELF_INTERSECTION",
                        f"Самопересечение сегментов {i} и {j}",
                        f"Segments[{i}, {j}]"
                    ))
        
        return errors
    
    def _check_direction_consistency(self, contour: Contour) -> List[ValidationError]:
        """Проверить согласованность направления"""
        errors = []
        
        # Проверяем, что конец каждого сегмента совпадает с началом следующего
        for i in range(len(contour.segments) - 1):
            current_end = contour.segments[i].end
            next_start = contour.segments[i + 1].start
            
            if current_end.distance_to(next_start) > self.tolerance:
                errors.append(ValidationError(
                    "DIRECTION_INCONSISTENCY",
                    f"Разрыв между сегментами {i} и {i+1}: {current_end.distance_to(next_start):.6f}",
                    f"Segments[{i}, {i+1}]"
                ))
        
        return errors
    
    def _segment_intersection(self, seg1: Segment, seg2: Segment) -> Optional[Point]:
        """Проверить пересечение двух сегментов"""
        # Для простоты используем проверку пересечения отрезков
        # В реальной системе здесь должна быть проверка пересечения дуг
        
        x1, y1 = seg1.start.x, seg1.start.y
        x2, y2 = seg1.end.x, seg1.end.y
        x3, y3 = seg2.start.x, seg2.start.y
        x4, y4 = seg2.end.x, seg2.end.y
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        
        if abs(denom) < self.tolerance:
            return None  # Параллельные или совпадающие
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        if 0 <= t <= 1 and 0 <= u <= 1:
            intersection_x = x1 + t * (x2 - x1)
            intersection_y = y1 + t * (y2 - y1)
            return Point(intersection_x, intersection_y)
        
        return None
    
    def _calculate_arc_midpoint(self, segment: Segment) -> Point:
        """Вычислить середину дуги по bulge"""
        if not segment.is_arc:
            return segment.get_midpoint()
        
        # Упрощенный расчет середины дуги
        mid = segment.get_midpoint()
        
        # Вычисляем перпендикулярное смещение
        dx = segment.end.x - segment.start.x
        dy = segment.end.y - segment.start.y
        length = segment.length
        
        if length > 0:
            # Нормаль к сегменту
            nx = -dy / length
            ny = dx / length
            
            # Смещение пропорционально bulge
            offset = length * segment.bulge / 4
            
            return Point(
                mid.x + nx * offset,
                mid.y + ny * offset
            )
        
        return mid
    
    def validate_geometry(self, geometry) -> List[ValidationError]:
        """Валидировать любую геометрию"""
        errors = []
        
        if isinstance(geometry, Point):
            errors.extend(self.validate_point(geometry))
        elif isinstance(geometry, Segment):
            errors.extend(self.validate_segment(geometry))
        elif isinstance(geometry, Contour):
            errors.extend(self.validate_contour(geometry))
        else:
            errors.append(ValidationError(
                "UNKNOWN_GEOMETRY_TYPE",
                f"Неизвестный тип геометрии: {type(geometry)}",
                str(geometry)
            ))
        
        return errors
    
    def is_valid(self, geometry) -> bool:
        """Проверить валидность геометрии"""
        errors = self.validate_geometry(geometry)
        return len(errors) == 0
    
    def get_validation_report(self, geometry) -> str:
        """Получить отчет валидации"""
        errors = self.validate_geometry(geometry)
        
        if not errors:
            return "✅ Геометрия валидна"
        
        report = f"❌ Найдено {len(errors)} ошибок:\n"
        for error in errors:
            report += f"  {error}\n"
        
        return report


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def validate_geometry(geometry, tolerance: float = 1e-6) -> List[ValidationError]:
    """Валидировать геометрию - ЕДИНСТВЕННЫЙ СПОСОБ"""
    validator = GeometryValidator(tolerance)
    return validator.validate_geometry(geometry)


def is_valid_geometry(geometry, tolerance: float = 1e-6) -> bool:
    """Проверить валидность геометрии - ЕДИНСТВЕННЫЙ СПОСОБ"""
    validator = GeometryValidator(tolerance)
    return validator.is_valid(geometry)


def get_validation_report(geometry, tolerance: float = 1e-6) -> str:
    """Получить отчет валидации - ЕДИНСТВЕННЫЙ СПОСОБ"""
    validator = GeometryValidator(tolerance)
    return validator.get_validation_report(geometry)


import logging
logger = logging.getLogger(__name__)

logger.debug("CAD Core Validation loaded")
