"""
🎯 TARGET SPEC — ЕДИНАЯ МОДЕЛЬ ЦЕЛИ
====================================

🎯 TargetSpec — стандартизированная модель цели оптимизации

❌ НЕ импортирует cad_core/derived
✅ Только данные и валидация
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Union
import json


@dataclass(frozen=True)
class TargetSpec:
    """
    Спецификация цели оптимизации
    
    📌 Стандартизированное описание того, что нужно оптимизировать
    """
    goal: str  # "reduce_seam_allowance", "increase_notches", "relax_fit"
    role: str  # "HEM", "WAIST", "WAIST_CENTER"
    by: Union[float, int]  # величина изменения
    mode: str = "delta"  # пока только delta
    constraints: Dict[str, Any] = field(default_factory=dict)  # min/max, запрет отрицательных
    
    def __post_init__(self):
        """Валидация после создания"""
        self.validate()
    
    def validate(self) -> None:
        """
        Валидировать спецификацию
        
        Raises:
            ValueError: если спецификация невалидна
        """
        # Проверяем цель
        if not self.goal or not isinstance(self.goal, str):
            raise ValueError(f"Goal must be non-empty string, got {self.goal}")
        
        # Проверяем роль
        if not self.role or not isinstance(self.role, str):
            raise ValueError(f"Role must be non-empty string, got {self.role}")
        
        # Проверяем величину
        if not isinstance(self.by, (int, float)):
            raise ValueError(f"By must be int or float, got {type(self.by)}")
        
        # Проверяем режим
        if self.mode != "delta":
            raise ValueError(f"Only 'delta' mode is supported, got {self.mode}")
        
        # Проверяем ограничения
        if not isinstance(self.constraints, dict):
            raise ValueError(f"Constraints must be dict, got {type(self.constraints)}")
        
        # Проверяем, что величина не отрицательная для некоторых целей
        if self.goal in ["reduce_seam_allowance", "reduce_notches"] and self.by < 0:
            raise ValueError(f"Goal '{self.goal}' requires positive 'by' value, got {self.by}")
        
        if self.goal in ["increase_seam_allowance", "increase_notches"] and self.by < 0:
            raise ValueError(f"Goal '{self.goal}' requires positive 'by' value, got {self.by}")
        
        # Проверяем min/max ограничения
        if "min" in self.constraints and self.by < self.constraints["min"]:
            raise ValueError(f"By value {self.by} is less than min constraint {self.constraints['min']}")
        
        if "max" in self.constraints and self.by > self.constraints["max"]:
            raise ValueError(f"By value {self.by} is greater than max constraint {self.constraints['max']}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразовать в словарь
        
        Returns:
            словарное представление
        """
        return {
            "goal": self.goal,
            "role": self.role,
            "by": self.by,
            "mode": self.mode,
            "constraints": self.constraints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TargetSpec':
        """
        Создать из словаря
        
        Args:
            data: словарное представление
            
        Returns:
            спецификация цели
        """
        return cls(
            goal=data["goal"],
            role=data["role"],
            by=data["by"],
            mode=data.get("mode", "delta"),
            constraints=data.get("constraints", {})
        )
    
    def to_json(self) -> str:
        """
        Преобразовать в JSON
        
        Returns:
            JSON строка
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TargetSpec':
        """
        Создать из JSON
        
        Args:
            json_str: JSON строка
            
        Returns:
            спецификация цели
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def with_constraints(self, **constraints) -> 'TargetSpec':
        """
        Создать новую спецификацию с дополнительными ограничениями
        
        Args:
            **constraints: новые ограничения
            
        Returns:
            новая спецификация
        """
        new_constraints = dict(self.constraints)
        new_constraints.update(constraints)
        
        return TargetSpec(
            goal=self.goal,
            role=self.role,
            by=self.by,
            mode=self.mode,
            constraints=new_constraints
        )
    
    def is_compatible_with(self, other: 'TargetSpec') -> bool:
        """
        Проверить совместимость с другой спецификацией
        
        Args:
            other: другая спецификация
            
        Returns:
            True если совместимы
        """
        return (
            self.goal == other.goal and
            self.role == other.role and
            self.mode == other.mode
        )
    
    def __str__(self) -> str:
        """Строковое представление"""
        return f"TargetSpec(goal={self.goal}, role={self.role}, by={self.by})"
    
    def __repr__(self) -> str:
        """Полное строковое представление"""
        return f"TargetSpec(goal={self.goal!r}, role={self.role!r}, by={self.by!r}, mode={self.mode!r}, constraints={self.constraints!r})"


import logging
logger = logging.getLogger(__name__)

logger.debug("TargetSpec loaded")
