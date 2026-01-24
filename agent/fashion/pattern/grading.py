"""
📐 ФАЗА 3.3 — GRADING AS RULES
===================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 3.3:
❌ Старый мир CAD: scale contour by 1.05
✅ Новый мир: Градация = набор правил:
- какие точки двигаются
- в каком направлении
- на сколько
- относительно каких осей

📌 НЕ масштаб
📌 НЕ математика ради математики
📌 А КОНСТРУКТОРСКИЕ ПРАВИЛА
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional


@dataclass(frozen=True)
class PatternGrading:
    """
    📐 PATTERN GRADING — ПРАВИЛА, А НЕ РЕЗУЛЬТАТ
    
    📌 правила по ролям, а не по координатам
    📌 ML-friendly
    📌 сериализуемо
    """
    size_from: str
    size_to: str
    
    # rules: role → (dx, dy)
    point_rules: Dict[str, Tuple[float, float]]
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.size_from or not self.size_from.strip():
            raise ValueError("Size from cannot be empty")
        
        if not self.size_to or not self.size_to.strip():
            raise ValueError("Size to cannot be empty")
        
        if not self.point_rules:
            raise ValueError("Point rules cannot be empty")
        
        # Проверяем, что все правила имеют корректный формат
        for role, (dx, dy) in self.point_rules.items():
            if not isinstance(dx, (int, float)) or not isinstance(dy, (int, float)):
                raise ValueError(f"Invalid rule format for role {role}: ({dx}, {dy})")
    
    def get_rule(self, role: str) -> Tuple[float, float]:
        """
        Получить правило для роли
        
        Args:
            role: роль точки
            
        Returns:
            (dx, dy) смещение
        """
        return self.point_rules.get(role, (0.0, 0.0))
    
    def has_rule(self, role: str) -> bool:
        """
        Проверить наличие правила для роли
        
        Args:
            role: роль точки
            
        Returns:
            True если правило есть
        """
        return role in self.point_rules
    
    def get_roles_with_rules(self) -> list[str]:
        """
        Получить список ролей с правилами
        
        Returns:
            список ролей
        """
        return list(self.point_rules.keys())
    
    def to_dict(self) -> dict:
        """
        Преобразовать в словарь
        
        Returns:
            словарное представление градации
        """
        return {
            "size_from": self.size_from,
            "size_to": self.size_to,
            "point_rules": {role: [dx, dy] for role, (dx, dy) in self.point_rules.items()}
        }
    
    def explain(self) -> dict:
        """
        Объяснить градацию как чистые данные
        
        Returns:
            словарное представление правил градации
        """
        return {
            "type": "grading",
            "size_from": self.size_from,
            "size_to": self.size_to,
            "rules": {
                role: {"dx": dx, "dy": dy}
                for role, (dx, dy) in self.point_rules.items()
            }
        }
    
    def __str__(self) -> str:
        return f"PatternGrading({self.size_from} → {self.size_to}, {len(self.point_rules)} rules)"
    
    def __repr__(self) -> str:
        return f"PatternGrading(size_from='{self.size_from}', size_to='{self.size_to}', rules_count={len(self.point_rules)})"


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_pattern_grading(size_from: str, size_to: str,
                          point_rules: Dict[str, Tuple[float, float]]) -> PatternGrading:
    """
    Создать градацию паттерна - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        size_from: исходный размер
        size_to: целевой размер
        point_rules: правила для точек по ролям
        
    Returns:
        градация паттерна
    """
    return PatternGrading(
        size_from=size_from,
        size_to=size_to,
        point_rules=point_rules
    )


def create_skirt_grading_rules(size_from: str, size_to: str) -> PatternGrading:
    """
    Создать стандартные правила градации для юбки
    
    Args:
        size_from: исходный размер
        size_to: целевой размер
        
    Returns:
        градация юбки
    """
    # Стандартные правила для юбки (конструкторские правила)
    rules = {
        "WAIST_CENTER": (0.0, 0.0),      # Центр талии не двигается
        "WAIST_SIDE": (2.5, 0.0),        # Бок талии расширяется
        "HIP_SIDE": (3.0, 0.0),          # Бок бедра расширяется
        "HEM_SIDE": (5.0, 0.0),          # Низ расширяется сильнее
        "HEM_CENTER": (0.0, 2.0),        # Центр низа удлиняется
        "CENTER_LINE": (0.0, 0.0)         # Линия центра не двигается
    }
    
    return create_pattern_grading(size_from, size_to, rules)


def validate_grading(grading: PatternGrading) -> bool:
    """
    Валидировать градацию - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        grading: градация паттерна
        
    Returns:
        True если градация валидна
    """
    try:
        if not grading.size_from or not grading.size_to:
            return False
        
        if not grading.point_rules:
            return False
        
        # Проверяем формат правил
        for role, (dx, dy) in grading.point_rules.items():
            if not isinstance(dx, (int, float)) or not isinstance(dy, (int, float)):
                return False
        
        return True
    except Exception:
        return False


import logging
logger = logging.getLogger(__name__)

logger.debug("PatternGrading loaded")
