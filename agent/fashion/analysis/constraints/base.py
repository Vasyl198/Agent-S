"""
🛡️ BASE CONSTRAINT — ОСНОВА ОГРАНИЧЕНИЙ
========================================

🎯 Базовые классы для Constraint Engine
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


@dataclass(frozen=True)
class ConstraintViolation:
    """
    Нарушение ограничения
    
    📌 НЕ исключение, а диагноз
    """
    type: str                    # "fit", "manufacturing", "grading"
    rule: str                    # "hem_width >= waist_length"
    actual: Dict[str, Any]       # {"hem_width": 480.0, "waist_length": 520.0}
    severity: str                # "error", "warning", "info"
    message: Optional[str] = None  # Дополнительное сообщение
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "type": self.type,
            "rule": self.rule,
            "actual": self.actual,
            "severity": self.severity,
            "message": self.message
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConstraintViolation':
        """Создать из словаря"""
        return cls(
            type=data["type"],
            rule=data["rule"],
            actual=data["actual"],
            severity=data["severity"],
            message=data.get("message")
        )


class BaseConstraint(ABC):
    """
    Базовый класс для ограничений
    
    📌 Интерфейс для всех типов ограничений
    """
    
    @abstractmethod
    def validate(self, pattern_model) -> List[ConstraintViolation]:
        """
        Валидировать PatternModel
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            список нарушений ограничений
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Название ограничения"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание ограничения"""
        pass


class ConstraintResult:
    """
    Результат валидации ограничений
    
    📌 NEVER бросает исключения, всегда возвращает диагноз
    """
    
    def __init__(self, violations: List[ConstraintViolation]):
        self.violations = violations
    
    @property
    def ok(self) -> bool:
        """Проверить, есть ли ошибки"""
        return not any(v.severity == "error" for v in self.violations)
    
    @property
    def errors(self) -> List[ConstraintViolation]:
        """Получить только ошибки"""
        return [v for v in self.violations if v.severity == "error"]
    
    @property
    def warnings(self) -> List[ConstraintViolation]:
        """Получить только предупреждения"""
        return [v for v in self.violations if v.severity == "warning"]
    
    @property
    def infos(self) -> List[ConstraintViolation]:
        """Получить только информационные сообщения"""
        return [v for v in self.violations if v.severity == "info"]
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "ok": self.ok,
            "violations": [v.to_dict() for v in self.violations],
            "summary": {
                "total": len(self.violations),
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "infos": len(self.infos)
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConstraintResult':
        """Создать из словаря"""
        violations = [ConstraintViolation.from_dict(v) for v in data.get("violations", [])]
        return cls(violations)
