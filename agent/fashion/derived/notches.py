"""
🔖 NOTCH GENERATOR — ГЕНЕРАТОР НАДСЕЧЕК
==========================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 4:
Надсечка WAIST → midpoints сегментов WAIST
"""

from typing import Dict, List, Tuple
import math

from ..cad.core.geometry import Point, Segment
from ..cad.core.contour import Contour


class NotchGenerator:
    """
    🔖 ГЕНЕРАТОР НАДСЕЧЕК
    
    📌 Создает линии надсечек на основе правил manufacturing
    📌 Base contour — священен
    📌 Вся новая геометрия — ТОЛЬКО производная
    """
    
    def __init__(self, notch_length: float = 5.0):
        """
        Инициализировать генератор надсечек
        
        Args:
            notch_length: длина надсечки в мм
        """
        self.notch_length = notch_length
    
    def generate_notches(self, contour: Contour, semantics, manufacturing) -> List[Segment]:
        """
        Сгенерировать надсечки для всех ролей
        
        Args:
            contour: базовый контур
            semantics: семантика паттерна
            manufacturing: производственные правила
            
        Returns:
            список линий надсечек
        """
        if not manufacturing:
            return []
        
        notch_lines = []
        
        # Генерируем надсечки для каждой роли
        for role in manufacturing.get_roles_with_notches():
            count = manufacturing.get_notch_count(role)
            
            # Получаем точки с этой ролью
            point_indices = semantics.points_by_role(role)
            
            if point_indices:
                role_notches = self._create_notches_for_role(
                    contour, point_indices, count, role
                )
                notch_lines.extend(role_notches)
        
        return notch_lines
    
    def _create_notches_for_role(self, contour: Contour, point_indices: List[int], 
                               count: int, role: str) -> List[Segment]:
        """
        Создать надсечки для роли
        
        Args:
            contour: контур
            point_indices: индексы точек
            count: количество надсечек
            role: роль точки
            
        Returns:
            список линий надсечек
        """
        notch_lines = []
        
        for idx in point_indices:
            if idx < len(contour.points):
                original_point = contour.points[idx]
                
                # Создаем надсечку как небольшую линию перпендикулярно контуру
                notch_line = self._create_notch_at_point(contour, idx, role)
                if notch_line:
                    notch_lines.append(notch_line)
        
        return notch_lines
    
    def _create_notch_at_point(self, contour: Contour, point_index: int, role: str) -> Segment:
        """
        Создать надсечку в точке
        
        Args:
            contour: контур
            point_index: индекс точки
            role: роль точки
            
        Returns:
            линия надсечки или None
        """
        if point_index >= len(contour.points):
            return None
        
        original_point = contour.points[point_index]
        
        # Находим соседние сегменты для определения направления
        prev_segment = None
        next_segment = None
        
        for i, segment in enumerate(contour.segments):
            if segment.end == original_point:
                prev_segment = segment
            elif segment.start == original_point:
                next_segment = segment
                break
        
        # Вычисляем направление надсечки
        if prev_segment and next_segment:
            # Усредняем направления соседних сегментов
            notch_direction = self._calculate_notch_direction(prev_segment, next_segment)
        elif prev_segment:
            notch_direction = self._calculate_perpendicular(prev_segment)
        elif next_segment:
            notch_direction = self._calculate_perpendicular(next_segment)
        else:
            # Если нет соседних сегментов, используем вертикальную надсечку
            notch_direction = Point(0, 1)
        
        # Создаем надсечку
        notch_end = Point(
            original_point.x + notch_direction.x * self.notch_length,
            original_point.y + notch_direction.y * self.notch_length
        )
        
        notch_line = Segment(original_point, notch_end)
        
        # Сохраняем роль в сегменте для объяснимости
        setattr(notch_line, 'role', role)
        setattr(notch_line, 'type', 'notch')
        
        return notch_line
    
    def _calculate_notch_direction(self, prev_segment: Segment, next_segment: Segment) -> Point:
        """
        Вычислить направление надсечки как усреднение нормалей соседних сегментов
        
        Args:
            prev_segment: предыдущий сегмент
            next_segment: следующий сегмент
            
        Returns:
            направление надсечки как Point
        """
        # Вычисляем нормали к сегментам
        prev_normal = self._calculate_perpendicular(prev_segment)
        next_normal = self._calculate_perpendicular(next_segment)
        
        # Усредняем нормали
        avg_x = (prev_normal.x + next_normal.x) / 2
        avg_y = (prev_normal.y + next_normal.y) / 2
        
        # Нормализуем
        length = math.sqrt(avg_x * avg_x + avg_y * avg_y)
        if length > 0:
            avg_x /= length
            avg_y /= length
        
        return Point(avg_x, avg_y)
    
    def _calculate_perpendicular(self, segment: Segment) -> Point:
        """
        Вычислить перпендикуляр к сегменту
        
        Args:
            segment: сегмент
            
        Returns:
            перпендикуляр как Point
        """
        dx = segment.end.x - segment.start.x
        dy = segment.end.y - segment.start.y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return Point(0, 1)
        
        # Перпендикуляр (поворот на 90 градусов)
        nx = -dy / length
        ny = dx / length
        
        return Point(nx, ny)
    
    def create_notches_at_midpoints(self, contour: Contour, segment_indices: List[int], 
                                  count: int, role: str) -> List[Segment]:
        """
        Создать надсечки в серединах сегментов
        
        Args:
            contour: контур
            segment_indices: индексы сегментов
            count: количество надсечек
            role: роль
            
        Returns:
            список линий надсечек
        """
        notch_lines = []
        
        for idx in segment_indices:
            if idx < len(contour.segments):
                segment = contour.segments[idx]
                midpoint = Point(
                    (segment.start.x + segment.end.x) / 2,
                    (segment.start.y + segment.end.y) / 2
                )
                
                # Создаем надсечку в середине
                notch_direction = self._calculate_perpendicular(segment)
                notch_end = Point(
                    midpoint.x + notch_direction.x * self.notch_length,
                    midpoint.y + notch_direction.y * self.notch_length
                )
                
                notch_line = Segment(midpoint, notch_end)
                setattr(notch_line, 'role', role)
                setattr(notch_line, 'type', 'midpoint_notch')
                
                notch_lines.append(notch_line)
        
        return notch_lines


import logging
logger = logging.getLogger(__name__)

logger.debug("NotchGenerator loaded")
