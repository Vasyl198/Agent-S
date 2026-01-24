"""
🟡 MANUFACTURING PROCESSOR - АДАПТИРОВАННЫЙ ПОД CAD CORE
========================================================

🚫 НЕ создает геометрию
✅ Использует CAD Core
✅ Возвращает Contour в CAD Core

Адаптированная версия manufacturing_layer_fixed.py для работы с CAD Core
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

from ..core.geometry import Point, Segment, Contour, PointRole, SegmentRole
from ..core.validation import is_valid_geometry, validate_geometry
from ..core.curves import optimize_bulge_values


class NotchType(Enum):
    """Типы надсечек"""
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    SLASH = "SLASH"
    BRIDGE = "BRIDGE"


@dataclass
class Notch:
    """Надсечка"""
    position: Point
    angle: float
    length: float
    notch_type: NotchType
    role: Optional[PointRole] = None


@dataclass
class GrainLine:
    """Долевая линия"""
    start: Point
    end: Point
    angle: float


@dataclass
class PatternLabel:
    """Подпись лекала"""
    position: Point
    text: str
    height: float
    angle: float = 0.0


@dataclass
class ManufacturingAllowance:
    """Припуск на шов"""
    role: SegmentRole
    offset: float


class ManufacturingProcessor:
    """
    🔧 ПРОЦЕССОР ПРОИЗВОДСТВЕННЫХ ЭЛЕМЕНТОВ - РАБОТАЕТ С CAD CORE
    
    Принимает Contour из CAD Core, добавляет производственные элементы,
    возвращает новые Contour в CAD Core
    """
    
    def __init__(self):
        # Стандартные припуски
        self.allowances = {
            SegmentRole.WAIST: 10.0,
            SegmentRole.SIDE: 15.0,
            SegmentRole.HEM: 30.0,
            SegmentRole.CENTER: 0.0,
        }
        
        # Параметры надсечек
        self.notch_length = 4.0
        self.grainline_length = 120.0
    
    def create_notch_on_segment(self, segment: Segment, position: float = 0.5) -> Notch:
        """
        Создать надсечку на сегменте
        
        Args:
            segment: сегмент из CAD Core
            position: позиция на сегменте (0-1)
            
        Returns:
            надсечка
        """
        # Вычисляем точку на сегменте
        x = segment.start.x + position * (segment.end.x - segment.start.x)
        y = segment.start.y + position * (segment.end.y - segment.start.y)
        
        # Угол сегмента
        angle = math.atan2(segment.end.y - segment.start.y, segment.end.x - segment.start.x)
        
        # Перпендикулярный угол для надсечки
        notch_angle = angle + math.pi / 2
        
        # Создаем точку надсечки через CAD Core
        from ..core.geometry import create_point
        notch_point = create_point(x, y, segment.start.role)
        
        return Notch(
            position=notch_point,
            angle=notch_angle,
            length=self.notch_length,
            notch_type=NotchType.SINGLE,
            role=segment.start.role
        )
    
    def create_grainline(self, contour: Contour) -> GrainLine:
        """
        Создать долевую линию
        
        Args:
            contour: контур из CAD Core
            
        Returns:
            долевая линия
        """
        # Ищем центральные точки для долевой
        center_points = contour.get_points_by_role(PointRole.CENTER_LINE)
        
        if len(center_points) >= 2:
            # Используем центральные точки
            start = center_points[0]
            end = center_points[1]
        else:
            # Создаем вертикальную долевую по центру
            xmin, ymin, xmax, ymax = contour.bounds
            center_x = (xmin + xmax) / 2
            
            from ..core.geometry import create_point
            start = create_point(center_x, ymin)
            end = create_point(center_x, ymax)
        
        angle = math.atan2(end.y - start.y, end.x - start.x)
        
        return GrainLine(start=start, end=end, angle=angle)
    
    def create_pattern_label(self, contour: Contour, text: str) -> PatternLabel:
        """
        Создать подпись лекала
        
        Args:
            contour: контур из CAD Core
            text: текст подписи
            
        Returns:
            подпись лекала
        """
        # Центр контура
        xmin, ymin, xmax, ymax = contour.bounds
        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2
        
        from ..core.geometry import create_point
        position = create_point(center_x, center_y)
        
        return PatternLabel(
            position=position,
            text=text,
            height=10.0,
            angle=0.0
        )
    
    def apply_allowance(self, segment: Segment, allowance: float) -> Segment:
        """
        Применить припуск к сегменту
        
        Args:
            segment: исходный сегмент из CAD Core
            allowance: величина припуска
            
        Returns:
            сегмент с припуском
        """
        if allowance <= 0:
            return segment
        
        # Вычисляем смещение перпендикулярно сегменту
        dx = segment.end.x - segment.start.x
        dy = segment.end.y - segment.start.y
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return segment
        
        # Нормаль к сегменту
        nx = -dy / length
        ny = dx / length
        
        # Смещаем точки
        offset_start_x = segment.start.x + nx * allowance
        offset_start_y = segment.start.y + ny * allowance
        offset_end_x = segment.end.x + nx * allowance
        offset_end_y = segment.end.y + ny * allowance
        
        # Создаем новые точки через CAD Core
        from ..core.geometry import create_point, create_segment
        start_point = create_point(offset_start_x, offset_start_y, segment.start.role)
        end_point = create_point(offset_end_x, offset_end_y, segment.end.role)
        
        return create_segment(start_point, end_point, segment.role, segment.bulge)
    
    def apply_allowances(self, contour: Contour) -> Contour:
        """
        Применить припуски ко всему контуру
        
        Args:
            contour: исходный контур из CAD Core
            
        Returns:
            контур с припусками
        """
        # Валидация входа
        if not is_valid_geometry(contour):
            raise ValueError(f"Invalid input contour: {validate_geometry(contour)}")
        
        # Применяем припуски к сегментам
        allowance_segments = []
        for segment in contour.segments:
            allowance = self.allowances.get(segment.role, 0.0)
            allowance_segment = self.apply_allowance(segment, allowance)
            allowance_segments.append(allowance_segment)
        
        # Создаем новый контур через CAD Core
        from ..core.geometry import create_contour
        allowance_contour = create_contour(allowance_segments, contour.closed)
        
        # Оптимизируем bulge значения
        allowance_contour = optimize_bulge_values(allowance_contour)
        
        # Финальная валидация
        if not is_valid_geometry(allowance_contour):
            raise ValueError(f"Invalid allowance contour: {validate_geometry(allowance_contour)}")
        
        return allowance_contour
    
    def create_manufacturing_elements(self, contour: Contour) -> Dict:
        """
        Создать все производственные элементы
        
        Args:
            contour: исходный контур из CAD Core
            
        Returns:
            словарь производственных элементов
        """
        elements = {}
        
        # Надсечки
        notches = []
        for i, segment in enumerate(contour.segments):
            # Надсечки на ключевых точках
            if segment.role in [SegmentRole.WAIST, SegmentRole.HEM]:
                notch = self.create_notch_on_segment(segment, 0.5)
                notches.append(notch)
        
        elements['notches'] = notches
        
        # Долевая
        elements['grainline'] = self.create_grainline(contour)
        
        # Подпись
        elements['label'] = self.create_pattern_label(contour, "FRONT")
        
        return elements
    
    def process_manufacturing(self, contour: Contour) -> Tuple[Contour, Dict]:
        """
        Полная обработка производственных элементов
        
        Args:
            contour: исходный контур из CAD Core
            
        Returns:
            (контур с припусками, производственные элементы)
        """
        # Валидация входа
        if not is_valid_geometry(contour):
            raise ValueError(f"Invalid input contour: {validate_geometry(contour)}")
        
        # 1. Применяем припуски
        allowance_contour = self.apply_allowances(contour)
        
        # 2. Создаем производственные элементы
        elements = self.create_manufacturing_elements(allowance_contour)
        
        return allowance_contour, elements


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def apply_manufacturing_allowances(contour: Contour) -> Contour:
    """
    Применить припуски к контуру - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        contour: исходный контур из CAD Core
        
    Returns:
        контур с припусками
    """
    processor = ManufacturingProcessor()
    return processor.apply_allowances(contour)


def create_manufacturing_elements(contour: Contour) -> Dict:
    """
    Создать производственные элементы - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        contour: контур из CAD Core
        
    Returns:
        производственные элементы
    """
    processor = ManufacturingProcessor()
    return processor.create_manufacturing_elements(contour)


def process_manufacturing_complete(contour: Contour) -> Tuple[Contour, Dict]:
    """
    Полная производственная обработка - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        contour: исходный контур из CAD Core
        
    Returns:
        (контур с припусками, производственные элементы)
    """
    processor = ManufacturingProcessor()
    return processor.process_manufacturing(contour)


print("🔧 Manufacturing Processor загружен")
print("📐 Работает с CAD Core")
print("🚫 НЕ создает геометрию")
print("✅ Возвращает Contour в CAD Core")
