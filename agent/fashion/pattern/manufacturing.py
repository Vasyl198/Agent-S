"""
🏭 ФАЗА 3.4 — MANUFACTURING AS RULES
============================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 3.4:
До этого момента мы работали с конструкторской формой.
Теперь — производственная интерпретация.

❌ Старый подход (плохо):
припуски = «обвести контур»
надсечки = «нарисовать линии»
долевая = «стрелочка в DXF»

✅ Наш подход:
Производство = набор правил поверх PatternModel
Semantics → Manufacturing Rules → Derived Geometry

📌 геометрия остаётся чистой
📌 правила — отдельные данные
📌 результат всегда воспроизводим
"""

from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple


@dataclass(frozen=True)
class PatternManufacturing:
    """
    🏭 PATTERN MANUFACTURING — ПРАВИЛА ПРОИЗВОДСТВА
    
    📌 НЕ геометрия
    📌 НЕ DXF
    📌 только правила
    """
    seam_allowances: Dict[str, float]    # role → mm
    notches: Dict[str, int]             # role → count
    grainline: str                      # semantic region
    stitch_lines: Optional[Dict[str, List[str]]] = None  # role → [target_roles]
    drill_holes: Optional[Dict[str, Tuple[float, float]]] = None  # role → (dx, dy)
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.seam_allowances:
            raise ValueError("Seam allowances cannot be empty")
        
        if not self.grainline or not self.grainline.strip():
            raise ValueError("Grainline cannot be empty")
        
        # Проверяем, что припуски положительные
        for role, allowance in self.seam_allowances.items():
            if allowance <= 0:
                raise ValueError(f"Seam allowance for {role} must be positive")
        
        # Проверяем, что количество надсечек неотрицательное
        for role, count in self.notches.items():
            if count < 0:
                raise ValueError(f"Notch count for {role} cannot be negative")
    
    def get_seam_allowance(self, role: str) -> float:
        """
        Получить припуск для роли
        
        Args:
            role: роль сегмента
            
        Returns:
            припуск в мм
        """
        return self.seam_allowances.get(role, 0.0)
    
    def get_notch_count(self, role: str) -> int:
        """
        Получить количество надсечек для роли
        
        Args:
            role: роль точки
            
        Returns:
            количество надсечек
        """
        return self.notches.get(role, 0)
    
    def has_seam_allowance(self, role: str) -> bool:
        """
        Проверить наличие припуска для роли
        
        Args:
            role: роль сегмента
            
        Returns:
            True если припуск есть
        """
        return role in self.seam_allowances
    
    def has_notches(self, role: str) -> bool:
        """
        Проверить наличие надсечек для роли
        
        Args:
            role: роль точки
            
        Returns:
            True если надсечки есть
        """
        return role in self.notches
    
    def get_roles_with_allowances(self) -> List[str]:
        """
        Получить список ролей с припусками
        
        Returns:
            список ролей
        """
        return list(self.seam_allowances.keys())
    
    def get_roles_with_notches(self) -> List[str]:
        """
        Получить список ролей с надсечками
        
        Returns:
            список ролей
        """
        return list(self.notches.keys())
    
    def to_dict(self) -> dict:
        """
        Преобразовать в словарь
        
        Returns:
            словарное представление производственных правил
        """
        return {
            "seam_allowances": self.seam_allowances,
            "notches": self.notches,
            "grainline": self.grainline,
            "stitch_lines": self.stitch_lines,
            "drill_holes": self.drill_holes
        }
    
    def explain(self) -> dict:
        """
        Объяснить производственные правила как чистые данные
        
        Returns:
            словарное представление производственных правил
        """
        return {
            "type": "manufacturing",
            "seam_allowances": self.seam_allowances,
            "notches": self.notches,
            "grainline": self.grainline
        }
    
    def __str__(self) -> str:
        return f"PatternManufacturing({len(self.seam_allowances)} allowances, {len(self.notches)} notches, grainline={self.grainline})"
    
    def __repr__(self) -> str:
        return f"PatternManufacturing(allowances={len(self.seam_allowances)}, notches={len(self.notches)}, grainline='{self.grainline}')"


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_pattern_manufacturing(seam_allowances: Dict[str, float],
                             notches: Dict[str, int],
                             grainline: str,
                             stitch_lines: Optional[Dict[str, List[str]]] = None,
                             drill_holes: Optional[Dict[str, Tuple[float, float]]] = None) -> PatternManufacturing:
    """
    Создать производственные правила - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        seam_allowances: припуски по ролям (мм)
        notches: надсечки по ролям (количество)
        grainline: долевая линия (семантический регион)
        stitch_lines: строчки по ролям
        drill_holes: отверстия по ролям
        
    Returns:
        производственные правила
    """
    return PatternManufacturing(
        seam_allowances=seam_allowances,
        notches=notches,
        grainline=grainline,
        stitch_lines=stitch_lines,
        drill_holes=drill_holes
    )


def create_skirt_manufacturing_rules() -> PatternManufacturing:
    """
    Создать стандартные производственные правила для юбки
    
    Returns:
        производственные правила юбки
    """
    # Стандартные правила для юбки (производственные)
    seam_allowances = {
        "WAIST": 10.0,    # 1 см припуск на талии
        "SIDE": 15.0,      # 1.5 см припуск на боковых швах
        "HEM": 20.0,       # 2 см припуск на низу
        "CENTER": 10.0      # 1 см припуск на центральном шве
    }
    
    notches = {
        "WAIST_CENTER": 1,  # 1 надсечка на центре талии
        "WAIST_SIDE": 1,    # 1 надсечка на боку талии
        "HIP_SIDE": 2,      # 2 надсечки на боку бедра
        "HEM_SIDE": 1       # 1 надсечка на боку низа
    }
    
    return create_pattern_manufacturing(
        seam_allowances=seam_allowances,
        notches=notches,
        grainline="CENTER_LINE"
    )


def validate_manufacturing(manufacturing: PatternManufacturing) -> bool:
    """
    Валидировать производственные правила - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        manufacturing: производственные правила
        
    Returns:
        True если правила валидны
    """
    try:
        if not manufacturing.seam_allowances:
            return False
        
        if not manufacturing.grainline:
            return False
        
        # Проверяем припуски
        for role, allowance in manufacturing.seam_allowances.items():
            if allowance <= 0:
                return False
        
        # Проверяем надсечки
        for role, count in manufacturing.notches.items():
            if count < 0:
                return False
        
        return True
    except Exception:
        return False


import logging
logger = logging.getLogger(__name__)

logger.debug("PatternManufacturing loaded")
