"""
1️⃣ ЕДИНСТВЕННЫЕ БАЗОВЫЕ КЛАССЫ
================================

📁 agent/fashion/cad/core/geometry.py

ТОЛЬКО ЗДЕСЬ разрешено:
- Point
- Segment  
- Arc (bulge)
- Contour

🚫 НИГДЕ в проекте больше нельзя создавать свои точки
"""

from dataclasses import dataclass
from typing import List, Optional, Union, Any
from enum import Enum
import math


class PointRole(Enum):
    """Роли точек в лекале"""
    WAIST_CENTER = "WAIST_CENTER"
    WAIST_SIDE = "WAIST_SIDE"
    HIP_SIDE = "HIP_SIDE"
    HEM_SIDE = "HEM_SIDE"
    HEM_CENTER = "HEM_CENTER"
    CENTER_LINE = "CENTER_LINE"
    UNKNOWN = "UNKNOWN"


class SegmentRole(Enum):
    """Роли сегментов в лекале"""
    WAIST = "WAIST"
    SIDE = "SIDE"
    HEM = "HEM"
    CENTER = "CENTER"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Point:
    """
    📍 ТОЧКА - ЕДИНСТВЕННЫЙ КЛАСС ТОЧЕК
    
    🚫 ЗАПРЕЩЕНО: создавать свои точки в других модулях
    ✅ РАЗРЕШЕНО: использовать только этот класс
    """
    x: float
    y: float
    role: Optional[PointRole] = None
    
    def distance_to(self, other: 'Point') -> float:
        """Расстояние до другой точки"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def __add__(self, other: Union['Point', float]) -> 'Point':
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y, self.role)
        else:
            return Point(self.x + other, self.y + other, self.role)
    
    def __sub__(self, other: Union['Point', float]) -> 'Point':
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y, self.role)
        else:
            return Point(self.x - other, self.y - other, self.role)
    
    def __mul__(self, scalar: float) -> 'Point':
        return Point(self.x * scalar, self.y * scalar, self.role)
    
    def __str__(self) -> str:
        role_str = f" ({self.role.value})" if self.role else ""
        return f"Point({self.x:.2f}, {self.y:.2f}{role_str})"
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'x': self.x,
            'y': self.y,
            'role': self.role.value if self.role else None
        }


@dataclass(frozen=True)
class Segment:
    """
    📏 СЕГМЕНТ - ЕДИНСТВЕННЫЙ КЛАСС СЕГМЕНТОВ
    
    🚫 ЗАПРЕЩЕНО: создавать свои сегменты в других модулях
    ✅ РАЗРЕШЕНО: использовать только этот класс
    """
    start: Point
    end: Point
    role: Optional[SegmentRole] = None
    bulge: float = 0.0
    
    def __post_init__(self):
        """Валидация после создания"""
        if self.start == self.end:
            raise ValueError("Сегмент не может иметь одинаковые начальную и конечную точки")
    
    @property
    def length(self) -> float:
        """Длина сегмента"""
        return self.start.distance_to(self.end)
    
    @property
    def is_arc(self) -> bool:
        """Является ли сегмент дугой"""
        return abs(self.bulge) > 1e-6
    
    @property
    def direction_vector(self) -> Point:
        """Вектор направления"""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return Point(dx, dy)
    
    @property
    def angle(self) -> float:
        """Угол сегмента в радианах"""
        return math.atan2(self.direction_vector.y, self.direction_vector.x)
    
    def get_midpoint(self) -> Point:
        """Середина сегмента"""
        return Point(
            (self.start.x + self.end.x) / 2,
            (self.start.y + self.end.y) / 2,
            self.start.role
        )
    
    def reverse(self) -> 'Segment':
        """Развернуть сегмент"""
        return Segment(
            start=self.end,
            end=self.start,
            role=self.role,
            bulge=-self.bulge  # Инвертируем bulge при реверсе
        )
    
    def __str__(self) -> str:
        role_str = f" ({self.role.value})" if self.role else ""
        bulge_str = f" bulge={self.bulge:.3f}" if self.is_arc else ""
        return f"Segment{self.start} → {self.end}{role_str}{bulge_str}"
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'start': self.start.to_dict(),
            'end': self.end.to_dict(),
            'role': self.role.value if self.role else None,
            'bulge': self.bulge
        }


@dataclass(frozen=True)
class Arc:
    """
    🌙 ДУГА - ЕДИНСТВЕННЫЙ КЛАСС ДУГ
    
    Представляет дугу через bulge параметр
    """
    center: Point
    radius: float
    start_angle: float
    end_angle: float
    bulge: float
    
    @property
    def start_point(self) -> Point:
        """Начальная точка дуги"""
        x = self.center.x + self.radius * math.cos(self.start_angle)
        y = self.center.y + self.radius * math.sin(self.start_angle)
        return Point(x, y)
    
    @property
    def end_point(self) -> Point:
        """Конечная точка дуги"""
        x = self.center.x + self.radius * math.cos(self.end_angle)
        y = self.center.y + self.radius * math.sin(self.end_angle)
        return Point(x, y)
    
    def to_segment(self, role: Optional[SegmentRole] = None) -> Segment:
        """Преобразовать в сегмент"""
        return Segment(
            start=self.start_point,
            end=self.end_point,
            role=role,
            bulge=self.bulge
        )


@dataclass
class Contour:
    """
    🔲 КОНТУР - ЕДИНСТВЕННЫЙ КЛАСС КОНТУРОВ
    
    🚫 ЗАПРЕЩЕНО: создавать свои контуры в других модулях
    ✅ РАЗРЕШЕНО: использовать только этот класс
    """
    segments: List[Segment]
    closed: bool = True
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.segments:
            raise ValueError("Контур не может быть пустым")
    
    @property
    def points(self) -> List[Point]:
        """Все точки контура"""
        points = [seg.start for seg in self.segments]
        if self.closed and self.segments:
            points.append(self.segments[-1].end)
        return points
    
    @property
    def length(self) -> float:
        """Длина контура"""
        return sum(seg.length for seg in self.segments)
    
    @property
    def arc_count(self) -> int:
        """Количество дуг в контуре"""
        return sum(1 for seg in self.segments if seg.is_arc)
    
    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Границы контура (xmin, ymin, xmax, ymax)"""
        if not self.points:
            return 0.0, 0.0, 0.0, 0.0
        
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        
        return min(xs), min(ys), max(xs), max(ys)
    
    @property
    def area(self) -> float:
        """Площадь контура (метод шнурков)"""
        if not self.closed:
            return 0.0
        
        area = 0.0
        n = len(self.segments)
        
        for i in range(n):
            p1 = self.segments[i].start
            p2 = self.segments[i].end
            area += (p1.x * p2.y) - (p2.x * p1.y)
        
        return abs(area) / 2.0
    
    def get_segments_by_role(self, role: SegmentRole) -> List[Segment]:
        """Получить сегменты по роли"""
        return [seg for seg in self.segments if seg.role == role]
    
    def get_points_by_role(self, role: PointRole) -> List[Point]:
        """Получить точки по роли"""
        return [p for p in self.points if p.role == role]
    
    def reverse(self) -> 'Contour':
        """Развернуть контур"""
        reversed_segments = [seg.reverse() for seg in reversed(self.segments)]
        return Contour(reversed_segments, self.closed)
    
    def __str__(self) -> str:
        closed_str = " (closed)" if self.closed else " (open)"
        return f"Contour{len(self.segments)} segments{closed_str}"
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'segments': [seg.to_dict() for seg in self.segments],
            'closed': self.closed,
            'length': self.length,
            'arc_count': self.arc_count,
            'area': self.area
        }


# 🚫 ГЛОБАЛЬНЫЕ ЗАПРЕТЫ
def __forbid_geometry_creation():
    """Запрет создания геометрии вне этого модуля"""
    import sys
    from types import ModuleType
    
    class GeometryGuard:
        def __init__(self):
            self.allowed_modules = {
                'agent.fashion.cad.core.geometry',
                'agent.fashion.cad.core.contour',
                'agent.fashion.cad.core.validation',
                'agent.fashion.cad.core.curves'
            }
        
        def __call__(self, frame_info):
            module_name = frame_info.f_globals.get('__name__', '')
            if module_name not in self.allowed_modules:
                raise PermissionError(
                    f"🚫 ЗАПРЕЩЕНО: Создание геометрии вне CAD Core!\n"
                    f"Модуль: {module_name}\n"
                    f"Используйте только классы из agent.fashion.cad.core.geometry"
                )
    
    # Устанавливаем guard (в реальной системе)
    # sys.settrace(GeometryGuard())


# 📋 ПРОВЕРКА ИСПОЛЬЗОВАНИЯ
def validate_geometry_usage():
    """Проверить, что геометрия используется правильно"""
    import inspect
    import sys
    
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    caller_module = caller_frame.f_globals.get('__name__', '')
    
    allowed_callers = [
        'agent.fashion.cad.core.geometry',
        'agent.fashion.cad.core.contour', 
        'agent.fashion.cad.core.validation',
        'agent.fashion.cad.core.curves',
        '__main__'  # Для тестов
    ]
    
    if caller_module not in allowed_callers:
        print(f"⚠️ ВНИМАНИЕ: Использование геометрии из модуля {caller_module}")
        print(f"   Рекомендуется использовать только CAD Core классы")


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_point(x: float, y: float, role: Optional[PointRole] = None) -> Point:
    """Создать точку - ЕДИНСТВЕННЫЙ СПОСОБ"""
    validate_geometry_usage()
    return Point(x, y, role)


def create_segment(start: Point, end: Point, role: Optional[SegmentRole] = None, bulge: float = 0.0) -> Segment:
    """Создать сегмент - ЕДИНСТВЕННЫЙ СПОСОБ"""
    validate_geometry_usage()
    return Segment(start, end, role, bulge)


def create_contour(segments: List[Segment], closed: bool = True) -> Contour:
    """Создать контур - ЕДИНСТВЕННЫЙ СПОСОБ"""
    validate_geometry_usage()
    return Contour(segments, closed)


import logging
logger = logging.getLogger(__name__)

logger.debug("CAD Core Geometry loaded")
