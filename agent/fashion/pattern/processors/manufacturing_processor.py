"""
🏭 MANUFACTURING PROCESSOR — ПРАВИЛА → ГЕОМЕТРИЯ
==================================================

📌 ВАЖНО:
- НЕ МЕНЯЕТ основной контур
- создаёт ПРОИЗВОДНЫЕ контуры
- применяет правила поверх PatternModel
"""

from typing import Dict, List, Tuple, Optional
import math

from agent.fashion.cad.core.geometry import Point, Segment
from agent.fashion.cad.core.contour import Contour
from ..model import PatternModel
from ..manufacturing import PatternManufacturing


class ManufacturingProcessor:
    """
    🏭 ПРОЦЕССОР ПРОИЗВОДСТВА - ПРИМЕНЯЕТ ПРАВИЛА К МОДЕЛИ
    
    🔁 PatternModel + Manufacturing Rules → Derived Geometry
    """
    
    def process(self, pattern_model: PatternModel, manufacturing: PatternManufacturing) -> PatternModel:
        """
        Применить производственные правила к модели паттерна
        
        Args:
            pattern_model: модель паттерна
            manufacturing: производственные правила
            
        Returns:
            новая модель с производственными правилами
        """
        if pattern_model.semantics is None:
            raise ValueError("Semantics required for manufacturing")
        
        if pattern_model.manufacturing is not None:
            raise ValueError("Manufacturing already applied")
        
        # ⛔ ВАЖНО: этот процессор НЕ МЕНЯЕТ основной контур
        # Он только сохраняет производственные правила в модели
        
        # Возвращаем новую модель с производственными правилами
        return pattern_model.with_manufacturing(manufacturing)
    
    def generate_seam_allowance_contours(self, pattern_model: PatternModel) -> Dict[str, Contour]:
        """
        Сгенерировать контуры припусков (derived geometry)
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            словарь контуров припусков по ролям
        """
        if pattern_model.manufacturing is None:
            raise ValueError("Manufacturing rules required")
        
        if pattern_model.semantics is None:
            raise ValueError("Semantics required")
        
        manufacturing = pattern_model.manufacturing
        semantics = pattern_model.semantics
        contour = pattern_model.contour
        
        allowance_contours = {}
        
        # Генерируем припуски для каждой роли
        for role in manufacturing.get_roles_with_allowances():
            allowance = manufacturing.get_seam_allowance(role)
            segments = semantics.segments_by_role(role)
            
            if segments:
                allowance_contour = self._create_allowance_contour(
                    contour, segments, allowance
                )
                allowance_contours[f"allowance_{role}"] = allowance_contour
        
        return allowance_contours
    
    def generate_notch_points(self, pattern_model: PatternModel) -> Dict[str, List[Point]]:
        """
        Сгенерировать точки надсечек (derived geometry)
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            словарь точек надсечек по ролям
        """
        if pattern_model.manufacturing is None:
            raise ValueError("Manufacturing rules required")
        
        if pattern_model.semantics is None:
            raise ValueError("Semantics required")
        
        manufacturing = pattern_model.manufacturing
        semantics = pattern_model.semantics
        contour = pattern_model.contour
        
        notch_points = {}
        
        # Генерируем надсечки для каждой роли
        for role in manufacturing.get_roles_with_notches():
            count = manufacturing.get_notch_count(role)
            point_indices = semantics.points_by_role(role)
            
            if point_indices:
                points = self._create_notch_points(
                    contour, point_indices, count
                )
                notch_points[f"notches_{role}"] = points
        
        return notch_points
    
    def generate_grainline_points(self, pattern_model: PatternModel) -> Tuple[Point, Point]:
        """
        Сгенерировать точки долевой линии (derived geometry)
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            две точки долевой линии
        """
        if pattern_model.manufacturing is None:
            raise ValueError("Manufacturing rules required")
        
        if pattern_model.semantics is None:
            raise ValueError("Semantics required")
        
        manufacturing = pattern_model.manufacturing
        semantics = pattern_model.semantics
        contour = pattern_model.contour
        
        # Находим регион для долевой линии
        grainline_region = manufacturing.grainline
        point_indices = semantics.points_by_role(grainline_region)
        
        if len(point_indices) >= 2:
            # Берем крайние точки региона
            start_idx = point_indices[0]
            end_idx = point_indices[-1]
            
            start_point = contour.points[start_idx]
            end_point = contour.points[end_idx]
            
            return start_point, end_point
        
        # Если регион не найден, используем границы контура
        bounds = contour.bounds
        return Point(bounds[0], bounds[1]), Point(bounds[2], bounds[3])
    
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
    
    def _create_notch_points(self, contour: Contour, point_indices: List[int], count: int) -> List[Point]:
        """
        Создать точки надсечек
        
        Args:
            contour: контур
            point_indices: индексы точек
            count: количество надсечек
            
        Returns:
            список точек надсечек
        """
        notch_points = []
        
        for idx in point_indices:
            if idx < len(contour.points):
                original_point = contour.points[idx]
                
                # Создаем надсечку как небольшую линию перпендикулярно контуру
                notch_length = 5.0  # 5 мм длина надсечки
                
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
                    dx1 = prev_segment.end.x - prev_segment.start.x
                    dy1 = prev_segment.end.y - prev_segment.start.y
                    dx2 = next_segment.end.x - next_segment.start.x
                    dy2 = next_segment.end.y - next_segment.start.y
                    
                    # Нормаль к усредненному направлению
                    avg_dx = (dx1 + dx2) / 2
                    avg_dy = (dy1 + dy2) / 2
                    length = math.sqrt(avg_dx*avg_dx + avg_dy*avg_dy)
                    
                    if length > 0:
                        nx = -avg_dy / length
                        ny = avg_dx / length
                        
                        notch_point = Point(
                            original_point.x + nx * notch_length,
                            original_point.y + ny * notch_length
                        )
                        notch_points.append(notch_point)
        
        return notch_points
    
    def validate_manufacturing_result(self, original_model: PatternModel, 
                                   manufacturing_model: PatternModel) -> bool:
        """
        Валидировать результат применения производственных правил
        
        Args:
            original_model: исходная модель
            manufacturing_model: модель с производственными правилами
            
        Returns:
            True если результат валиден
        """
        try:
            # Проверяем, что контуры одинаковые (не должны измениться)
            if original_model.contour != manufacturing_model.contour:
                return False
            
            # Проверяем, что семантика не изменилась
            if original_model.semantics != manufacturing_model.semantics:
                return False
            
            # Проверяем, что производственные правила установлены
            if manufacturing_model.manufacturing is None:
                return False
            
            return True
        except Exception:
            return False


print("🏭 ManufacturingProcessor загружен")
print("📌 НЕ МЕНЯЕТ основной контур")
print("📌 создаёт ПРОИЗВОДНЫЕ контуры")
print("📌 применяет правила поверх PatternModel")
