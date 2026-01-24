"""
🟡 MARKER PROCESSOR - АДАПТИРОВАННЫЙ ПОД CAD CORE
==================================================

🚫 НЕ создает геометрию
✅ Использует CAD Core
✅ Возвращает Contour в CAD Core

Адаптированная версия marker_engine_fixed.py для работы с CAD Core
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

from ..core.geometry import Point, Segment, Contour, PointRole, SegmentRole
from ..core.validation import is_valid_geometry, validate_geometry


class GrainAngle(Enum):
    """Угол долевой"""
    DEG_0 = 0
    DEG_180 = 180


@dataclass
class BoundingBox:
    """Ограничивающая рамка"""
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    
    @property
    def width(self) -> float:
        return self.xmax - self.xmin
    
    @property
    def height(self) -> float:
        return self.ymax - self.ymin
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    @property
    def center(self) -> Point:
        from ..core.geometry import create_point
        return create_point(
            (self.xmin + self.xmax) / 2,
            (self.ymin + self.ymax) / 2
        )


@dataclass
class MarkerPiece:
    """Элемент раскладки"""
    contour: Contour
    size: str
    grain_angle: GrainAngle
    bbox: BoundingBox
    position: Optional[Point] = None
    
    def __post_init__(self):
        if self.position is None:
            # Начальная позиция в нуле
            from ..core.geometry import create_point
            self.position = create_point(0, 0)
    
    def move_to(self, x: float, y: float):
        """Переместить элемент"""
        dx = x - self.position.x
        dy = y - self.position.y
        
        # Создаем новые сегменты через CAD Core
        new_segments = []
        for segment in self.contour.segments:
            from ..core.geometry import create_point, create_segment
            start = create_point(
                segment.start.x + dx,
                segment.start.y + dy,
                segment.start.role
            )
            end = create_point(
                segment.end.x + dx,
                segment.end.y + dy,
                segment.end.role
            )
            new_segment = create_segment(start, end, segment.role, segment.bulge)
            new_segments.append(new_segment)
        
        from ..core.geometry import create_contour
        self.contour = create_contour(new_segments, self.contour.closed)
        
        from ..core.geometry import create_point
        self.position = create_point(x, y)
        
        # Обновляем bbox
        self.bbox = BoundingBox(
            xmin=self.bbox.xmin + dx,
            ymin=self.bbox.ymin + dy,
            xmax=self.bbox.xmax + dx,
            ymax=self.bbox.ymax + dy
        )


@dataclass
class MarkerSheet:
    """Лист раскладки"""
    fabric_width: float
    pieces: List[MarkerPiece]
    height: float = 0.0
    
    def __post_init__(self):
        self.height = self.calculate_height()
    
    def calculate_height(self) -> float:
        """Вычислить высоту листа"""
        if not self.pieces:
            return 0.0
        
        max_y = max(piece.bbox.ymax for piece in self.pieces)
        return max_y


class MarkerProcessor:
    """
    🔧 ПРОЦЕССОР РАСКЛАДКИ - РАБОТАЕТ С CAD CORE
    
    Принимает Contour из CAD Core, создает раскладку,
    возвращает новые Contour в CAD Core
    """
    
    def __init__(self, fabric_width: float = 1400.0):
        self.fabric_width = fabric_width
        self.tolerance = 1e-6
    
    def create_bounding_box(self, contour: Contour) -> BoundingBox:
        """
        Создать ограничивающую рамку
        
        Args:
            contour: контур из CAD Core
            
        Returns:
            ограничивающая рамка
        """
        bounds = contour.bounds
        return BoundingBox(
            xmin=bounds[0],
            ymin=bounds[1],
            xmax=bounds[2],
            ymax=bounds[3]
        )
    
    def create_marker_piece(self, contour: Contour, size: str, 
                        grain_angle: GrainAngle = GrainAngle.DEG_0) -> MarkerPiece:
        """
        Создать элемент раскладки
        
        Args:
            contour: контур из CAD Core
            size: размер
            grain_angle: угол долевой
            
        Returns:
            элемент раскладки
        """
        # Валидация входа
        if not is_valid_geometry(contour):
            raise ValueError(f"Invalid input contour: {validate_geometry(contour)}")
        
        bbox = self.create_bounding_box(contour)
        
        return MarkerPiece(
            contour=contour,
            size=size,
            grain_angle=grain_angle,
            bbox=bbox
        )
    
    def check_intersection(self, piece1: MarkerPiece, piece2: MarkerPiece) -> bool:
        """
        Проверить пересечение элементов
        
        Args:
            piece1, piece2: элементы раскладки
            
        Returns:
            True если пересекаются
        """
        # Простая проверка AABB (Axis-Aligned Bounding Box)
        return not (
            piece1.bbox.xmax <= piece2.bbox.xmin or
            piece1.bbox.xmin >= piece2.bbox.xmax or
            piece1.bbox.ymax <= piece2.bbox.ymin or
            piece1.bbox.ymin >= piece2.bbox.ymax
        )
    
    def step_1_sorting(self, pieces: List[MarkerPiece]) -> List[MarkerPiece]:
        """
        ШАГ 1: Сортировка элементов
        
        Сортируем по высоте, затем по ширине (убывание)
        """
        return sorted(pieces, key=lambda p: (p.bbox.height, p.bbox.width), reverse=True)
    
    def step_2_strip_packing(self, pieces: List[MarkerPiece]) -> MarkerSheet:
        """
        ШАГ 2: Strip Packing алгоритм
        
        Раскладываем элементы слева направо, затем новая строка
        """
        if not pieces:
            return MarkerSheet(self.fabric_width, [])
        
        placed_pieces = []
        current_x = 0.0
        current_y = 0.0
        current_row_height = 0.0
        
        for piece in pieces:
            # Проверяем, помещается ли в текущую строку
            if current_x + piece.bbox.width > self.fabric_width:
                # Новая строка
                current_x = 0.0
                current_y += current_row_height
                current_row_height = 0.0
            
            # Размещаем элемент
            piece.move_to(current_x, current_y)
            placed_pieces.append(piece)
            
            # Обновляем позицию
            current_x += piece.bbox.width
            current_row_height = max(current_row_height, piece.bbox.height)
        
        return MarkerSheet(self.fabric_width, placed_pieces)
    
    def calculate_waste(self, sheet: MarkerSheet) -> Dict[str, float]:
        """
        Рассчитать отходы
        
        Args:
            sheet: лист раскладки
            
        Returns:
            статистика отходов
        """
        total_area = sheet.fabric_width * sheet.height
        pieces_area = sum(piece.bbox.area for piece in sheet.pieces)
        waste_area = total_area - pieces_area
        
        return {
            'total_area': total_area,
            'pieces_area': pieces_area,
            'waste_area': waste_area,
            'waste_percentage': (waste_area / total_area) * 100 if total_area > 0 else 0
        }
    
    def create_marker(self, contours: Dict[str, Contour]) -> MarkerSheet:
        """
        Создать раскладку из контуров
        
        Args:
            contours: словарь {имя: контур} из CAD Core
            
        Returns:
            лист раскладки
        """
        # Валидация входов
        for name, contour in contours.items():
            if not is_valid_geometry(contour):
                raise ValueError(f"Invalid contour {name}: {validate_geometry(contour)}")
        
        # Создаем элементы раскладки
        pieces = []
        for name, contour in contours.items():
            piece = self.create_marker_piece(contour, name)
            pieces.append(piece)
        
        # Сортируем элементы
        sorted_pieces = self.step_1_sorting(pieces)
        
        # Создаем раскладку
        sheet = self.step_2_strip_packing(sorted_pieces)
        
        return sheet
    
    def get_marker_statistics(self, sheet: MarkerSheet) -> Dict:
        """
        Получить статистику раскладки
        
        Args:
            sheet: лист раскладки
            
        Returns:
            статистика
        """
        waste_stats = self.calculate_waste(sheet)
        
        return {
            'fabric_width': sheet.fabric_width,
            'marker_height': sheet.height,
            'pieces_count': len(sheet.pieces),
            'total_area': waste_stats['total_area'],
            'pieces_area': waste_stats['pieces_area'],
            'waste_area': waste_stats['waste_area'],
            'waste_percentage': waste_stats['waste_percentage'],
            'efficiency': 100 - waste_stats['waste_percentage']
        }


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_marker_from_contours(contours: Dict[str, Contour], 
                             fabric_width: float = 1400.0) -> MarkerSheet:
    """
    Создать раскладку из контуров - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        contours: словарь контуров из CAD Core
        fabric_width: ширина ткани
        
    Returns:
        лист раскладки
    """
    processor = MarkerProcessor(fabric_width)
    return processor.create_marker(contours)


def get_marker_statistics(sheet: MarkerSheet) -> Dict:
    """
    Получить статистику раскладки - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        sheet: лист раскладки
        
    Returns:
        статистика
    """
    processor = MarkerProcessor()
    return processor.get_marker_statistics(sheet)


print("🔧 Marker Processor загружен")
print("📐 Работает с CAD Core")
print("🚫 НЕ создает геометрию")
print("✅ Возвращает Contour в CAD Core")
