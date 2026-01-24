"""
🌾 GRAINLINE GENERATOR — ГЕНЕРАТОР ДОЛЕВОЙ ЛИНИИ
=================================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 4:
Долевая линия создается на основе semantic region
"""

from typing import Optional, Tuple, List
import math

from ..cad.core.geometry import Point, Segment
from ..cad.core.contour import Contour


class GrainlineGenerator:
    """
    🌾 ГЕНЕРАТОР ДОЛЕВОЙ ЛИНИИ
    
    📌 Создает долевую линию на основе правил manufacturing
    📌 Base contour — священен
    📌 Вся новая геометрия — ТОЛЬКО производная
    """
    
    def __init__(self, grainline_length: float = 150.0):
        """
        Инициализировать генератор долевой линии
        
        Args:
            grainline_length: длина долевой линии в мм
        """
        self.grainline_length = grainline_length
    
    def generate_grainline(self, contour: Contour, semantics, manufacturing) -> Optional[Segment]:
        """
        Сгенерировать долевую линию
        
        Args:
            contour: базовый контур
            semantics: семантика паттерна
            manufacturing: производственные правила
            
        Returns:
            долевая линия или None
        """
        if not manufacturing or not manufacturing.grainline:
            return None
        
        grainline_region = manufacturing.grainline
        
        # Находим регион для долевой линии
        grainline_segment = self._create_grainline_for_region(
            contour, semantics, grainline_region
        )
        
        return grainline_segment
    
    def _create_grainline_for_region(self, contour: Contour, semantics, region: str) -> Optional[Segment]:
        """
        Создать долевую линию для региона
        
        Args:
            contour: контур
            semantics: семантика паттерна
            region: регион для долевой линии
            
        Returns:
            долевая линия или None
        """
        # Получаем точки региона
        point_indices = semantics.points_by_role(region)
        
        if len(point_indices) >= 2:
            # Берем крайние точки региона
            start_idx = point_indices[0]
            end_idx = point_indices[-1]
            
            if start_idx < len(contour.points) and end_idx < len(contour.points):
                start_point = contour.points[start_idx]
                end_point = contour.points[end_idx]
                
                # Создаем долевую линию
                grainline = self._create_optimized_grainline(start_point, end_point)
                return grainline
        
        # Если регион не найден, используем границы контура
        return self._create_grainline_from_bounds(contour)
    
    def _create_optimized_grainline(self, start_point: Point, end_point: Point) -> Segment:
        """
        Создать оптимизированную долевую линию между двумя точками
        
        Args:
            start_point: начальная точка
            end_point: конечная точка
            
        Returns:
            долевая линия
        """
        # Вычисляем центр и направление
        center_x = (start_point.x + end_point.x) / 2
        center_y = (start_point.y + end_point.y) / 2
        
        dx = end_point.x - start_point.x
        dy = end_point.y - start_point.y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            # Если точки совпадают, используем вертикальную линию
            return Segment(
                Point(center_x, center_y - self.grainline_length / 2),
                Point(center_x, center_y + self.grainline_length / 2)
            )
        
        # Нормализуем направление
        nx = dx / length
        ny = dy / length
        
        # Создаем долевую линию нужной длины
        half_length = self.grainline_length / 2
        
        grainline_start = Point(
            center_x - nx * half_length,
            center_y - ny * half_length
        )
        
        grainline_end = Point(
            center_x + nx * half_length,
            center_y + ny * half_length
        )
        
        grainline = Segment(grainline_start, grainline_end)
        
        # Сохраняем тип для объяснимости
        setattr(grainline, 'type', 'grainline')
        setattr(grainline, 'region', 'derived')
        
        return grainline
    
    def _create_grainline_from_bounds(self, contour: Contour) -> Segment:
        """
        Создать долевую линию на основе границ контура
        
        Args:
            contour: контур
            
        Returns:
            долевая линия
        """
        bounds = contour.bounds
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        
        # Создаем вертикальную долевую линию (стандарт для одежды)
        grainline_start = Point(center_x, center_y - self.grainline_length / 2)
        grainline_end = Point(center_x, center_y + self.grainline_length / 2)
        
        grainline = Segment(grainline_start, grainline_end)
        
        # Сохраняем тип для объяснимости
        setattr(grainline, 'type', 'grainline')
        setattr(grainline, 'region', 'bounds')
        
        return grainline
    
    def create_grainline_with_arrows(self, contour: Contour, semantics, 
                                   manufacturing) -> Tuple[Segment, List[Segment]]:
        """
        Создать долевую линию с.arrowами
        
        Args:
            contour: контур
            semantics: семантика паттерна
            manufacturing: производственные правила
            
        Returns:
            кортеж (долевая линия, список стрелок)
        """
        grainline = self.generate_grainline(contour, semantics, manufacturing)
        
        if not grainline:
            return None, []
        
        # Создаем стрелки на концах долевой линии
        arrows = self._create_arrows_for_grainline(grainline)
        
        return grainline, arrows
    
    def _create_arrows_for_grainline(self, grainline: Segment) -> List[Segment]:
        """
        Создать стрелки для долевой линии
        
        Args:
            grainline: долевая линия
            
        Returns:
            список сегментов стрелок
        """
        arrows = []
        arrow_length = 10.0  # 10 мм длина стрелки
        arrow_angle = math.pi / 6  # 30 градусов угол стрелки
        
        # Вычисляем направление
        dx = grainline.end.x - grainline.start.x
        dy = grainline.end.y - grainline.start.y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return arrows
        
        # Нормализуем направление
        nx = dx / length
        ny = dy / length
        
        # Стрелка в начале
        start_arrow = self._create_arrow_at_point(
            grainline.start, nx, ny, arrow_length, arrow_angle, True
        )
        arrows.extend(start_arrow)
        
        # Стрелка в конце
        end_arrow = self._create_arrow_at_point(
            grainline.end, nx, ny, arrow_length, arrow_angle, False
        )
        arrows.extend(end_arrow)
        
        return arrows
    
    def _create_arrow_at_point(self, point: Point, nx: float, ny: float, 
                              length: float, angle: float, is_start: bool) -> List[Segment]:
        """
        Создать стрелку в точке
        
        Args:
            point: точка
            nx, ny: направление
            length: длина стрелки
            angle: угол стрелки
            is_start: True если стрелка в начале
            
        Returns:
            список сегментов стрелки
        """
        arrows = []
        
        # Направление стрелки (обратное основному направлению для начала)
        if is_start:
            nx = -nx
            ny = -ny
        
        # Вычисляем концы стрелки
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        
        # Левая сторона стрелки
        left_x = point.x - nx * length * cos_angle + ny * length * sin_angle
        left_y = point.y - ny * length * cos_angle - nx * length * sin_angle
        left_point = Point(left_x, left_y)
        
        # Правая сторона стрелки
        right_x = point.x - nx * length * cos_angle - ny * length * sin_angle
        right_y = point.y - ny * length * cos_angle + nx * length * sin_angle
        right_point = Point(right_x, right_y)
        
        # Создаем сегменты стрелки
        arrows.append(Segment(point, left_point))
        arrows.append(Segment(point, right_point))
        
        return arrows


import logging
logger = logging.getLogger(__name__)

logger.debug("GrainlineGenerator loaded")
