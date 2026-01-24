"""
✂️ SEAM ALLOWANCE GENERATOR — ГЕНЕРАТОР ПРИПУСКОВ
==================================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 4:
Припуск HEM → offset сегментов с ролью HEM
"""

from typing import Dict, List, Tuple
import math

from ..cad.core.geometry import Point, Segment
from ..cad.core.contour import Contour


class SeamAllowanceGenerator:
    """
    ✂️ ГЕНЕРАТОР ПРИПУСКОВ
    
    📌 Создает контуры припусков на основе правил manufacturing
    📌 Base contour — священен
    📌 Вся новая геометрия — ТОЛЬКО производная
    """
    
    def generate_allowances(self, contour: Contour, semantics, manufacturing) -> Dict[str, Contour]:
        """
        Сгенерировать припуски для всех ролей
        
        Args:
            contour: базовый контур
            semantics: семантика паттерна
            manufacturing: производственные правила
            
        Returns:
            словарь контуров припусков по ролям
        """
        if not manufacturing:
            return {}
        
        allowance_contours = {}
        
        # Генерируем припуски для каждой роли
        for role in manufacturing.get_roles_with_allowances():
            allowance = manufacturing.get_seam_allowance(role)
            
            # Получаем сегменты с этой ролью
            segment_indices = semantics.segments_by_role(role)
            
            if segment_indices:
                allowance_contour = self._create_allowance_contour(
                    contour, segment_indices, allowance
                )
                allowance_contours[role] = allowance_contour
        
        return allowance_contours
    
    def _create_allowance_contour(self, contour: Contour, segment_indices: List[int], allowance: float) -> Contour:
        """
        Создать контур припуска для сегментов
        
        Args:
            contour: исходный контур
            segment_indices: индексы сегментов
            allowance: припуск в мм
            
        Returns:
            контур припуска
        """
        allowance_segments = []
        
        for idx in segment_indices:
            if idx < len(contour.segments):
                original_segment = contour.segments[idx]
                
                # Создаем параллельный сегмент с припуском
                allowance_segment = self._create_parallel_segment(
                    original_segment, allowance
                )
                allowance_segments.append(allowance_segment)
        
        return Contour(allowance_segments, closed=False)
    
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
    
    def create_continuous_allowance(self, contour: Contour, segment_indices: List[int], allowance: float) -> Contour:
        """
        Создать непрерывный контур припуска для связанных сегментов
        
        Args:
            contour: исходный контур
            segment_indices: индексы сегментов
            allowance: припуск в мм
            
        Returns:
            непрерывный контур припуска
        """
        # Сначала создаем смещенные сегменты
        offset_segments = []
        for idx in segment_indices:
            if idx < len(contour.segments):
                original_segment = contour.segments[idx]
                offset_segment = self._create_parallel_segment(original_segment, allowance)
                offset_segments.append(offset_segment)
        
        # Соединяем сегменты в непрерывный контур
        if len(offset_segments) < 2:
            return Contour(offset_segments, closed=False)
        
        # Добавляем соединительные сегменты
        connected_segments = []
        
        for i, segment in enumerate(offset_segments):
            connected_segments.append(segment)
            
            # Добавляем соединительный сегмент к следующему
            if i < len(offset_segments) - 1:
                next_segment = offset_segments[i + 1]
                connector = Segment(segment.end, next_segment.start)
                connected_segments.append(connector)
        
        return Contour(connected_segments, closed=False)


import logging
logger = logging.getLogger(__name__)

logger.debug("SeamAllowanceGenerator loaded")
