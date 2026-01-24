"""
🧪 DERIVED GEOMETRY MODEL — ПРОИЗВОДНАЯ ГЕОМЕТРИЯ (ФАЗА 4.4)
=========================================================

Модель производной геометрии паттерна.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from .grainline_model import Grainline


@dataclass(frozen=True)
class DerivedGeometry:
    """
    Производная геометрия паттерна.
    
    Содержит всю геометрию, которая генерируется на основе:
    - manufacturing rules (припуски, надсечки)
    - semantics (роли сегментов и точек)
    - grading rules (градация)
    
    ⚠️ Важно: это чистая геометрия, без бизнес-логики.
    """
    allowance_contours: Dict[str, Any] = field(default_factory=dict)
    notches: Dict[str, List[Any]] = field(default_factory=dict)
    stitch_lines: Dict[str, List[Any]] = field(default_factory=dict)
    grainlines: List[Grainline] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'allowance_contours': self.allowance_contours,
            'notches': self.notches,
            'stitch_lines': self.stitch_lines,
            'grainlines': [gl.to_dict() for gl in self.grainlines]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DerivedGeometry':
        """Создать из словаря"""
        grainlines = []
        for gl_data in data.get('grainlines', []):
            grainlines.append(Grainline.from_dict(gl_data))
        
        return cls(
            allowance_contours=data.get('allowance_contours', {}),
            notches=data.get('notches', {}),
            stitch_lines=data.get('stitch_lines', {}),
            grainlines=grainlines
        )
    
    def is_empty(self) -> bool:
        """Проверить, пуста ли производная геометрия"""
        return (
            not self.allowance_contours and
            not self.notches and
            not self.stitch_lines and
            not self.grainlines
        )
    
    def explain(self) -> dict:
        """
        Объяснить производную геометрию как ссылки на правила
        
        Returns:
            словарное представление источников производной геометрии
        """
        result = {
            "type": "derived_geometry",
            "seam_allowances": [],
            "notches": [],
            "grainline": None
        }
        
        # Объясняем припуски
        for role in self.allowance_contours.keys():
            result["seam_allowances"].append({
                "role": role,
                "source": f"manufacturing.seam_allowances.{role}"
            })
        
        # Объясняем надсечки
        for role, notch_list in self.notches.items():
            if notch_list:  # Только если есть надсечки
                result["notches"].append({
                    "role": role,
                    "count": len(notch_list),
                    "source": f"manufacturing.notches.{role}"
                })
        
        # Объясняем долевую линию
        if self.grainlines:
            # Берем первую долевую линию (обычно она одна)
            grainline = self.grainlines[0]
            result["grainline"] = {
                "region": grainline.role,
                "source": f"manufacturing.grainline"
            }
        
        return result
    
    def __eq__(self, other) -> bool:
        """Сравнение производной геометрии"""
        if not isinstance(other, DerivedGeometry):
            return False
        return (
            self.allowance_contours == other.allowance_contours and
            self.notches == other.notches and
            self.stitch_lines == other.stitch_lines and
            self.grainlines == other.grainlines
        )
