"""
🧠 DERIVED GEOMETRY PROCESSOR — ПРОЦЕССОР ПРОИЗВОДНОЙ ГЕОМЕТРИИ
================================================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 4:
Превратить правила (manufacturing, grading) → в производную геометрию,
не меняя базовый контур, полностью воспроизводимо и объяснимо.

📌 PatternModel остаётся неизменяемым
📌 Base contour — священен
📌 Вся новая геометрия — ТОЛЬКО производная
"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import math

if TYPE_CHECKING:
    from ..pattern.model import PatternModel

from ..pattern.manufacturing import PatternManufacturing
from ..cad.core.geometry import Point, Segment
from ..cad.core.contour import Contour
from .model import DerivedGeometry, create_derived_geometry
from .allowance import SeamAllowanceGenerator
from .notches import NotchGenerator
from .stitch_lines import StitchLineGenerator
from .grainline import GrainlineGenerator


class DerivedGeometryProcessor:
    """
    🧠 ПРОЦЕССОР ПРОИЗВОДНОЙ ГЕОМЕТРИИ
    
    🔁 PatternModel + Rules → DerivedGeometry
    
    📌 Что он делает:
    - читает pattern.semantics
    - читает pattern.manufacturing
    - использует CAD Core
    - строит DerivedGeometry
    - возвращает НОВЫЙ PatternModel
    
    ❌ НЕ меняет:
    - contour
    - semantics
    - dimensions
    - grading
    - manufacturing
    """
    
    def __init__(self):
        """Инициализировать процессор"""
        self.allowance_generator = SeamAllowanceGenerator()
        self.notch_generator = NotchGenerator()
        self.stitch_generator = StitchLineGenerator()
        self.grainline_generator = GrainlineGenerator()
    
    def process(self, pattern: 'PatternModel') -> 'PatternModel':
        """
        Обработать паттерн и создать производную геометрию
        
        Args:
            pattern: исходный паттерн
            
        Returns:
            новый паттерн с производной геометрией
        """
        if pattern.semantics is None:
            raise ValueError("Semantics required for derived geometry")
        
        if pattern.manufacturing is None:
            # Нет manufacturing → пустая derived geometry
            empty_derived = create_derived_geometry()
            return pattern.with_derived_geometry(empty_derived)
        
        # Создаем производную геометрию
        derived = self._create_derived_geometry(pattern)
        
        # Возвращаем новый паттерн с производной геометрией
        return pattern.with_derived_geometry(derived)
    
    def _create_derived_geometry(self, pattern: 'PatternModel') -> DerivedGeometry:
        """
        Создать производную геометрию для паттерна
        
        Args:
            pattern: паттерн
            
        Returns:
            производная геометрия
        """
        contour = pattern.contour
        semantics = pattern.semantics
        manufacturing = pattern.manufacturing
        
        # Генерируем припуски
        allowance_contours = self.allowance_generator.generate_allowances(
            contour, semantics, manufacturing
        )
        
        # Генерируем надсечки
        notch_lines = self.notch_generator.generate_notches(
            contour, semantics, manufacturing
        )
        
        # Генерируем строчки
        stitch_lines = self.stitch_generator.generate_stitch_lines(
            contour, semantics, manufacturing
        )
        
        # Генерируем долевую линию
        grainline = self.grainline_generator.generate_grainline(
            contour, semantics, manufacturing
        )
        
        # Генерируем отверстия
        drill_holes = self._create_drill_holes(contour, semantics, manufacturing)
        
        # Создаем производную геометрию
        derived = create_derived_geometry(
            allowance_contours=allowance_contours,
            notch_lines=notch_lines,
            stitch_lines=stitch_lines,
            grainline=grainline,
            drill_holes=drill_holes
        )
        
        return derived
    
    def _create_drill_holes(self, contour: Contour, semantics, manufacturing) -> Dict[str, Point]:
        """
        Создать отверстия
        
        Args:
            contour: контур
            semantics: семантика паттерна
            manufacturing: производственные правила
            
        Returns:
            словарь отверстий по ролям
        """
        if not manufacturing.drill_holes:
            return {}
        
        drill_holes = {}
        
        for role, offset in manufacturing.drill_holes.items():
            # Получаем точки с этой ролью
            point_indices = semantics.points_by_role(role)
            
            for idx in point_indices:
                if idx < len(contour.points):
                    original_point = contour.points[idx]
                    
                    # Создаем отверстие со смещением
                    drill_point = Point(
                        original_point.x + offset[0],
                        original_point.y + offset[1]
                    )
                    
                    drill_holes[f"{role}_{idx}"] = drill_point
        
        return drill_holes
    
    def validate_derived_geometry(self, original_pattern: 'PatternModel', 
                                 derived_pattern: 'PatternModel') -> bool:
        """
        Валидировать результат создания производной геометрии
        
        Args:
            original_pattern: исходный паттерн
            derived_pattern: паттерн с производной геометрией
            
        Returns:
            True если результат валиден
        """
        try:
            # Проверяем, что базовые данные не изменились
            if original_pattern.contour != derived_pattern.contour:
                return False
            
            if original_pattern.semantics != derived_pattern.semantics:
                return False
            
            if original_pattern.dimensions != derived_pattern.dimensions:
                return False
            
            if original_pattern.grading != derived_pattern.grading:
                return False
            
            if original_pattern.manufacturing != derived_pattern.manufacturing:
                return False
            
            # Проверяем, что производная геометрия установлена
            if derived_pattern.derived_geometry is None:
                return False
            
            return True
        except Exception:
            return False
    
    def explain_derived_geometry(self, pattern: 'PatternModel') -> Dict[str, List[str]]:
        """
        Объяснить производную геометрию
        
        Args:
            pattern: паттерн с производной геометрией
            
        Returns:
            объяснение по типам элементов
        """
        if not pattern.derived_geometry:
            return {"empty": ["No derived geometry"]}
        
        explanation = {}
        derived = pattern.derived_geometry
        
        # Объясняем припуски
        if derived.allowance_contours:
            allowance_explanation = []
            for role, contour in derived.allowance_contours.items():
                allowance_explanation.append(
                    f"Припуск {role}: {len(contour.segments)} сегментов, "
                    f"длина {contour.length:.1f} мм"
                )
            explanation["allowances"] = allowance_explanation
        
        # Объясняем надсечки
        if derived.notch_lines:
            notch_explanation = []
            for segment in derived.notch_lines:
                role = getattr(segment, 'role', 'UNKNOWN')
                notch_type = getattr(segment, 'type', 'notch')
                notch_explanation.append(
                    f"Надсечка {role}: тип {notch_type}, "
                    f"длина {segment.length:.1f} мм"
                )
            explanation["notches"] = notch_explanation
        
        # Объясняем строчки
        if derived.stitch_lines:
            stitch_explanation = []
            for role, segments in derived.stitch_lines.items():
                total_length = sum(seg.length for seg in segments)
                stitch_explanation.append(
                    f"Строчки {role}: {len(segments)} сегментов, "
                    f"общая длина {total_length:.1f} мм"
                )
            explanation["stitch_lines"] = stitch_explanation
        
        # Объясняем долевую линию
        if derived.grainline:
            grainline_explanation = [
                f"Долевая линия: длина {derived.grainline.length:.1f} мм, "
                f"регион {getattr(derived.grainline, 'region', 'unknown')}"
            ]
            explanation["grainline"] = grainline_explanation
        
        # Объясняем отверстия
        if derived.drill_holes:
            hole_explanation = []
            for role, point in derived.drill_holes.items():
                hole_explanation.append(
                    f"Отверстие {role}: координаты ({point.x:.1f}, {point.y:.1f})"
                )
            explanation["drill_holes"] = hole_explanation
        
        return explanation
    
    def get_derived_geometry_stats(self, pattern: 'PatternModel') -> Dict[str, int]:
        """
        Получить статистику производной геометрии
        
        Args:
            pattern: паттерн с производной геометрией
            
        Returns:
            статистика по типам элементов
        """
        if not pattern.derived_geometry:
            return {"total": 0}
        
        derived = pattern.derived_geometry
        
        stats = {
            "allowance_contours": len(derived.allowance_contours),
            "notch_lines": len(derived.notch_lines),
            "stitch_line_groups": len(derived.stitch_lines),
            "grainline": 1 if derived.grainline else 0,
            "drill_holes": len(derived.drill_holes),
            "total_segments": derived.get_total_segments_count()
        }
        
        return stats


import logging
logger = logging.getLogger(__name__)

logger.debug("DerivedGeometryProcessor loaded")
