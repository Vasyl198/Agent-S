"""
🟡 GRADING PROCESSOR - АДАПТИРОВАННЫЙ ПОД CAD CORE
====================================================

🚫 НЕ создает геометрию
✅ Использует CAD Core
✅ Возвращает Contour из CAD Core

Адаптированная версия grading_engine_fixed.py для работы с CAD Core
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.geometry import Point, Segment, Contour, PointRole, SegmentRole
from ..core.validation import is_valid_geometry, validate_geometry
from ..core.curves import optimize_bulge_values


class Size(Enum):
    """Размеры одежды"""
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


@dataclass
class GradeRule:
    """Правило градации"""
    x_increment: float
    y_increment: float
    x_factor: float = 1.0
    y_factor: float = 1.0


@dataclass
class PointGradeBehavior:
    """Поведение точки при градации"""
    x_factor: float = 1.0
    y_factor: float = 1.0


class GradingProcessor:
    """
    🔧 ПРОЦЕССОР ГРАДАЦИИ - РАБОТАЕТ С CAD CORE
    
    Принимает Contour из CAD Core, выполняет градацию,
    возвращает новые Contour в CAD Core
    """
    
    def __init__(self):
        # Стандартные правила градации
        self.grade_rules = {
            PointRole.WAIST_CENTER: GradeRule(0.0, 3.0),
            PointRole.WAIST_SIDE: GradeRule(5.0, 3.0),
            PointRole.HIP_SIDE: GradeRule(6.0, 3.0),
            PointRole.HEM_SIDE: GradeRule(7.0, 3.0),
            PointRole.HEM_CENTER: GradeRule(0.0, 3.0),
            PointRole.CENTER_LINE: GradeRule(0.0, 3.0),
        }
        
        # Размерные шаги
        self.size_steps = {
            Size.XS: -2,
            Size.S: -1,
            Size.M: 0,
            Size.L: 1,
            Size.XL: 2
        }
    
    def grade_point(self, point: Point, size_step: int) -> Point:
        """
        Градировать точку
        
        Args:
            point: исходная точка из CAD Core
            size_step: шаг размера (-2, -1, 0, 1, 2)
            
        Returns:
            градированная точка в CAD Core
        """
        if point.role is None:
            # Без роли - не градируем
            return point
        
        rule = self.grade_rules.get(point.role)
        if rule is None:
            # Нет правила - не градируем
            return point
        
        # Вычисляем приращение
        dx = rule.x_increment * size_step * rule.x_factor
        dy = rule.y_increment * size_step * rule.y_factor
        
        # Создаем новую точку через CAD Core
        from ..core.geometry import create_point
        return create_point(
            point.x + dx,
            point.y + dy,
            point.role
        )
    
    def grade_segment(self, segment: Segment, size_step: int) -> Segment:
        """
        Градировать сегмент
        
        Args:
            segment: исходный сегмент из CAD Core
            size_step: шаг размера
            
        Returns:
            градированный сегмент в CAD Core
        """
        # Градируем точки
        start = self.grade_point(segment.start, size_step)
        end = self.grade_point(segment.end, size_step)
        
        # Сохраняем bulge (дуги градируются пропорционально)
        bulge = segment.bulge
        
        # Создаем новый сегмент через CAD Core
        from ..core.geometry import create_segment
        return create_segment(start, end, segment.role, bulge)
    
    def grade_contour(self, contour: Contour, size_step: int) -> Contour:
        """
        Градировать контур
        
        Args:
            contour: исходный контур из CAD Core
            size_step: шаг размера
            
        Returns:
            градированный контур в CAD Core
        """
        # Валидация входа
        if not is_valid_geometry(contour):
            raise ValueError(f"Invalid input contour: {validate_geometry(contour)}")
        
        # Градируем все сегменты
        graded_segments = []
        for segment in contour.segments:
            graded_segment = self.grade_segment(segment, size_step)
            graded_segments.append(graded_segment)
        
        # Создаем новый контур через CAD Core
        from ..core.geometry import create_contour
        graded_contour = create_contour(graded_segments, contour.closed)
        
        # Оптимизируем bulge значения
        graded_contour = optimize_bulge_values(graded_contour)
        
        # Финальная валидация
        if not is_valid_geometry(graded_contour):
            raise ValueError(f"Invalid graded contour: {validate_geometry(graded_contour)}")
        
        return graded_contour
    
    def grade_all_sizes(self, base_contour: Contour) -> Dict[Size, Contour]:
        """
        Создать все размеры
        
        Args:
            base_contour: базовый контур (размер M)
            
        Returns:
            словарь {размер: контур}
        """
        graded_contours = {}
        
        for size, step in self.size_steps.items():
            if step == 0:
                # Базовый размер
                graded_contours[size] = base_contour
            else:
                # Градированный размер
                try:
                    graded_contour = self.grade_contour(base_contour, step)
                    graded_contours[size] = graded_contour
                except Exception as e:
                    print(f"⚠️ Ошибка градации размера {size}: {e}")
                    continue
        
        return graded_contours
    
    def get_size_statistics(self, graded_contours: Dict[Size, Contour]) -> Dict:
        """
        Получить статистику по градации
        
        Args:
            graded_contours: словарь градированных контуров
            
        Returns:
            статистика градации
        """
        stats = {}
        
        for size, contour in graded_contours.items():
            stats[size.value] = {
                'segments': len(contour.segments),
                'arcs': contour.arc_count,
                'length': contour.length,
                'area': contour.area,
                'bounds': contour.bounds
            }
        
        return stats


# 🎯 ЕДИНСТВЕННАЯ ТОЧКА ВХОДА
def grade_contour_to_all_sizes(contour: Contour) -> Dict[Size, Contour]:
    """
    Градировать контур во все размеры - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        contour: базовый контур из CAD Core
        
    Returns:
        словарь {размер: градированный контур}
    """
    processor = GradingProcessor()
    return processor.grade_all_sizes(contour)


def get_grading_statistics(graded_contours: Dict[Size, Contour]) -> Dict:
    """
    Получить статистику градации - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        graded_contours: градированные контуры
        
    Returns:
        статистика
    """
    processor = GradingProcessor()
    return processor.get_size_statistics(graded_contours)


print("🔧 Grading Processor загружен")
print("📏 Работает с CAD Core")
print("🚫 НЕ создает геометрию")
print("✅ Возвращает Contour в CAD Core")
