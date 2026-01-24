"""
🪡 STITCH LINE GENERATOR — ГЕНЕРАТОР СТРОЧЕК
===============================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 4:
Строчки создаются на основе правил stitch_lines в manufacturing
"""

from typing import Dict, List, Tuple
import math

from ..cad.core.geometry import Point, Segment
from ..cad.core.contour import Contour


class StitchLineGenerator:
    """
    🪡 ГЕНЕРАТОР СТРОЧЕК
    
    📌 Создает строчки на основе правил manufacturing
    📌 Base contour — священен
    📌 Вся новая геометрия — ТОЛЬКО производная
    """
    
    def __init__(self, stitch_offset: float = 2.0):
        """
        Инициализировать генератор строчек
        
        Args:
            stitch_offset: смещение строчки от края в мм
        """
        self.stitch_offset = stitch_offset
    
    def generate_stitch_lines(self, contour: Contour, semantics, manufacturing) -> Dict[str, List[Segment]]:
        """
        Сгенерировать строчки для всех ролей
        
        Args:
            contour: базовый контур
            semantics: семантика паттерна
            manufacturing: производственные правила
            
        Returns:
            словарь строчек по ролям
        """
        if not manufacturing or not manufacturing.stitch_lines:
            return {}
        
        stitch_lines = {}
        
        # Генерируем строчки для каждой роли
        for role, target_roles in manufacturing.stitch_lines.items():
            role_stitches = self._create_stitches_for_role(
                contour, semantics, role, target_roles
            )
            if role_stitches:
                stitch_lines[role] = role_stitches
        
        return stitch_lines
    
    def _create_stitches_for_role(self, contour: Contour, semantics, 
                                 role: str, target_roles: List[str]) -> List[Segment]:
        """
        Создать строчки для роли
        
        Args:
            contour: контур
            semantics: семантика паттерна
            role: исходная роль
            target_roles: целевые роли для строчек
            
        Returns:
            список строчек
        """
        stitch_lines = []
        
        # Получаем сегменты исходной роли
        source_indices = semantics.segments_by_role(role)
        
        # Получаем сегменты целевых ролей
        target_indices = []
        for target_role in target_roles:
            target_indices.extend(semantics.segments_by_role(target_role))
        
        if not source_indices or not target_indices:
            return []
        
        # Создаем строчки между исходными и целевыми сегментами
        for source_idx in source_indices:
            if source_idx >= len(contour.segments):
                continue
            
            source_segment = contour.segments[source_idx]
            
            # Находим ближайшие целевые сегменты
            for target_idx in target_indices:
                if target_idx >= len(contour.segments):
                    continue
                
                target_segment = contour.segments[target_idx]
                
                # Создаем строчку
                stitch_line = self._create_stitch_between_segments(
                    source_segment, target_segment, role
                )
                if stitch_line:
                    stitch_lines.append(stitch_line)
        
        return stitch_lines
    
    def _create_stitch_between_segments(self, source_segment: Segment, 
                                       target_segment: Segment, role: str) -> Segment:
        """
        Создать строчку между двумя сегментами
        
        Args:
            source_segment: исходный сегмент
            target_segment: целевой сегмент
            role: роль строчки
            
        Returns:
            строчка или None
        """
        # Находим ближайшие точки между сегментами
        source_point = self._find_closest_point_on_segment(
            source_segment, target_segment
        )
        target_point = self._find_closest_point_on_segment(
            target_segment, source_segment
        )
        
        if not source_point or not target_point:
            return None
        
        # Создаем строчку
        stitch_line = Segment(source_point, target_point)
        
        # Сохраняем роль и тип для объяснимости
        setattr(stitch_line, 'role', role)
        setattr(stitch_line, 'type', 'stitch_line')
        
        return stitch_line
    
    def _find_closest_point_on_segment(self, segment: Segment, other_segment: Segment) -> Point:
        """
        Найти ближайшую точку на сегменте к другому сегменту
        
        Args:
            segment: сегмент для поиска точки
            other_segment: другой сегмент
            
        Returns:
            ближайшая точка
        """
        # Простой подход: проверяем концы и середину
        candidates = [
            segment.start,
            segment.end,
            Point((segment.start.x + segment.end.x) / 2, (segment.start.y + segment.end.y) / 2)
        ]
        
        closest_point = None
        min_distance = float('inf')
        
        for candidate in candidates:
            distance = self._point_to_segment_distance(candidate, other_segment)
            if distance < min_distance:
                min_distance = distance
                closest_point = candidate
        
        return closest_point
    
    def _point_to_segment_distance(self, point: Point, segment: Segment) -> float:
        """
        Вычислить расстояние от точки до сегмента
        
        Args:
            point: точка
            segment: сегмент
            
        Returns:
            расстояние
        """
        # Расстояние до прямой через векторное произведение
        dx = segment.end.x - segment.start.x
        dy = segment.end.y - segment.start.y
        
        if dx == 0 and dy == 0:
            # Сегмент вырожден в точку
            return math.sqrt((point.x - segment.start.x)**2 + (point.y - segment.start.y)**2)
        
        t = max(0, min(1, ((point.x - segment.start.x) * dx + (point.y - segment.start.y) * dy) / (dx * dx + dy * dy)))
        
        projection = Point(
            segment.start.x + t * dx,
            segment.start.y + t * dy
        )
        
        return math.sqrt((point.x - projection.x)**2 + (point.y - projection.y)**2)
    
    def create_parallel_stitches(self, contour: Contour, segment_indices: List[int], 
                               offset: float, role: str) -> List[Segment]:
        """
        Создать параллельные строчки для сегментов
        
        Args:
            contour: контур
            segment_indices: индексы сегментов
            offset: смещение строчки
            role: роль
            
        Returns:
            список строчек
        """
        stitch_lines = []
        
        for idx in segment_indices:
            if idx >= len(contour.segments):
                continue
            
            segment = contour.segments[idx]
            
            # Создаем параллельную строчку
            parallel_stitch = self._create_parallel_segment(segment, offset)
            
            # Сохраняем роль и тип
            setattr(parallel_stitch, 'role', role)
            setattr(parallel_stitch, 'type', 'parallel_stitch')
            
            stitch_lines.append(parallel_stitch)
        
        return stitch_lines
    
    def _create_parallel_segment(self, segment: Segment, offset: float) -> Segment:
        """
        Создать параллельный сегмент со смещением
        
        Args:
            segment: исходный сегмент
            offset: смещение
            
        Returns:
            параллельный сегмент
        """
        # Вычисляем нормаль к сегменту
        dx = segment.end.x - segment.start.x
        dy = segment.end.y - segment.start.y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return segment
        
        # Нормаль (перпендикуляр)
        nx = -dy / length
        ny = dx / length
        
        # Смещаем точки
        offset_start = Point(
            segment.start.x + nx * offset,
            segment.start.y + ny * offset
        )
        
        offset_end = Point(
            segment.end.x + nx * offset,
            segment.end.y + ny * offset
        )
        
        return Segment(offset_start, offset_end, bulge=segment.bulge)


import logging
logger = logging.getLogger(__name__)

logger.debug("StitchLineGenerator loaded")
