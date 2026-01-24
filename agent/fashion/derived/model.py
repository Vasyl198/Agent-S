"""
🧪 DERIVED GEOMETRY MODEL — ПРОИЗВОДНАЯ ГЕОМЕТРИЯ
================================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 4:
Только геометрия. Никаких правил.

"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from agent.fashion.cad.core.geometry import Point, Segment
from agent.fashion.cad.core.contour import Contour
from .grainline_model import Grainline

@dataclass(frozen=True)
class DerivedGeometry:
    """
    Производная геометрия паттерна.
    
    Содержит всю геометрию, которая генерируется на основе:
    - manufacturing rules (припуски, надсечки)
    - semantics (роли сегментов и точек)
    - grading rules (градация)
    
    Важно: это чистая геометрия, без бизнес-логики.
    """
    allowance_contours: Dict[str, Any] = field(default_factory=dict)
    notches: Dict[str, List[Any]] = field(default_factory=dict)
    stitch_lines: Dict[str, List[Any]] = field(default_factory=dict)
    grainlines: List[Grainline] = field(default_factory=list)
    """список линий надсечек"""
    
    def get_stitch_lines_for_role(self, role: str) -> List[Segment]:
        """
        Получить строчки для роль
        
        Args:
            role: роль сегмента
            
        Returns:
            список строчек
        """
        return self.stitch_lines.get(role, [])
    
    def has_allowances(self) -> bool:
        """
        Проверить наличие припусков
        
        Returns:
            True если есть припуски
        """
        return len(self.allowance_contours) > 0
    
    def has_notches(self) -> bool:
        """
        Проверить наличие надсечек
        
        Returns:
            True если есть надсечки
        """
        return len(self.notch_lines) > 0
    
    def has_stitch_lines(self) -> bool:
        """
        Проверить наличие строчек
        
        Returns:
            True если есть строчки
        """
        return len(self.stitch_lines) > 0
    
    def has_grainline(self) -> bool:
        """
        Проверить наличие долевой линии
        
        Returns:
            True если есть долевая линия
        """
        return self.grainline is not None
    
    def get_total_segments_count(self) -> int:
        """
        Получить общее количество сегментов в производной геометрии
        
        Returns:
            общее количество сегментов
        """
        count = len(self.notch_lines)
        
        if self.grainline:
            count += 1
        
        for stitch_segments in self.stitch_lines.values():
            count += len(stitch_segments)
        
        for contour in self.allowance_contours.values():
            count += len(contour.segments)
        
        return count
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Получить границы всей производной геометрии
        
        Returns:
            (xmin, ymin, xmax, ymax)
        """
        all_points = []
        
        # Собираем все точки из припусков
        for contour in self.allowance_contours.values():
            all_points.extend(contour.points)
        
        # Собираем точки из надсечек
        for segment in self.notch_lines:
            all_points.append(segment.start)
            all_points.append(segment.end)
        
        # Собираем точки из строчек
        for stitch_segments in self.stitch_lines.values():
            for segment in stitch_segments:
                all_points.append(segment.start)
                all_points.append(segment.end)
        
        # Добавляем долевую линию
        if self.grainline:
            all_points.append(self.grainline.start)
            all_points.append(self.grainline.end)
        
        # Добавляем отверстия
        for point in self.drill_holes.values():
            all_points.append(point)
        
        if not all_points:
            return 0.0, 0.0, 0.0, 0.0
        
        xs = [p.x for p in all_points]
        ys = [p.y for p in all_points]
        
        return min(xs), min(ys), max(xs), max(ys)
    
    def to_dict(self) -> dict:
        """
        Преобразовать в словарь
        
        Returns:
            словарное представление производной геометрии
        """
        return {
            "allowance_contours": {
                role: {
                    "segments_count": len(contour.segments),
                    "points_count": len(contour.points),
                    "length": contour.length,
                    "area": contour.area,
                    "closed": contour.closed
                }
                for role, contour in self.allowance_contours.items()
            },
            "notch_lines": [
                {
                    "start": [seg.start.x, seg.start.y],
                    "end": [seg.end.x, seg.end.y],
                    "length": seg.length
                }
                for seg in self.notch_lines
            ],
            "stitch_lines": {
                role: [
                    {
                        "start": [seg.start.x, seg.start.y],
                        "end": [seg.end.x, seg.end.y],
                        "length": seg.length
                    }
                    for seg in segments
                ]
                for role, segments in self.stitch_lines.items()
            },
            "grainline": {
                "start": [self.grainline.start.x, self.grainline.start.y],
                "end": [self.grainline.end.x, self.grainline.end.y],
                "length": self.grainline.length
            } if self.grainline else None,
            "drill_holes": {
                role: [point.x, point.y]
                for role, point in self.drill_holes.items()
            },
            "total_segments_count": self.get_total_segments_count(),
            "bounds": self.get_bounds()
        }
    
    def __str__(self) -> str:
        parts = []
        
        if self.allowance_contours:
            parts.append(f"{len(self.allowance_contours)} allowances")
        
        if self.notch_lines:
            parts.append(f"{len(self.notch_lines)} notches")
        
        if self.stitch_lines:
            total_stitches = sum(len(segs) for segs in self.stitch_lines.values())
            parts.append(f"{total_stitches} stitches")
        
        if self.grainline:
            parts.append("grainline")
        
        if self.drill_holes:
            parts.append(f"{len(self.drill_holes)} holes")
        
        if not parts:
            return "DerivedGeometry(empty)"
        
        return f"DerivedGeometry({', '.join(parts)})"
    
    def __repr__(self) -> str:
        return f"DerivedGeometry(allowances={len(self.allowance_contours)}, notches={len(self.notch_lines)}, stitches={len(self.stitch_lines)}, grainline={self.has_grainline()})"


# 🎯 ЕДИНСТВЕННАЯ ТОЧКА ВХОДА
def create_derived_geometry(allowance_contours: Optional[Dict[str, Contour]] = None,
                          notch_lines: Optional[List[Segment]] = None,
                          stitch_lines: Optional[Dict[str, List[Segment]]] = None,
                          grainline: Optional[Segment] = None,
                          drill_holes: Optional[Dict[str, Point]] = None) -> DerivedGeometry:
    """
    Создать производную геометрию - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        allowance_contours: припуски по ролям
        notch_lines: линии надсечек
        stitch_lines: строчки по ролям
        grainline: долевая линия
        drill_holes: отверстия по ролям
        
    Returns:
        производная геометрия
    """
    return DerivedGeometry(
        allowance_contours=allowance_contours or {},
        notch_lines=notch_lines or [],
        stitch_lines=stitch_lines or {},
        grainline=grainline,
        drill_holes=drill_holes or {}
    )


def validate_derived_geometry(derived: DerivedGeometry) -> bool:
    """
    Валидировать производную геометрию - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        derived: производная геометрия
        
    Returns:
        True если геометрия валидна
    """
    try:
        # Проверяем припуски
        for role, contour in derived.allowance_contours.items():
            if not contour.segments:
                return False
        
        # Проверяем надсечки
        for segment in derived.notch_lines:
            if segment.start == segment.end:
                return False
        
        # Проверяем строчки
        for role, segments in derived.stitch_lines.items():
            for segment in segments:
                if segment.start == segment.end:
                    return False
        
        # Проверяем долевую линию
        if derived.grainline:
            if derived.grainline.start == derived.grainline.end:
                return False
        
        return True
    except Exception:
        return False


import logging
logger = logging.getLogger(__name__)

logger.debug("DerivedGeometry loaded")
