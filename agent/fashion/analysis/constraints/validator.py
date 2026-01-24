"""
🛡️ CONSTRAINT VALIDATOR — ОРКЕСТРАТОР ОГРАНИЧЕНИЙ
=================================================

🎯 Агрегатор всех ограничений

❌ НЕ читает геометрию
✅ Только оркестрация валидации
"""

from typing import List
from .base import BaseConstraint, ConstraintResult
from .fit_constraints import FitConstraints
from .manufacturing_constraints import ManufacturingConstraints
from .grading_constraints import GradingConstraints


class ConstraintValidator:
    """
    Валидатор ограничений PatternModel
    
    📌 Агрегирует все типы ограничений
    📌 Возвращает единый диагноз
    """
    
    def __init__(self):
        """Инициализировать валидатор с ограничениями по умолчанию"""
        self.constraints: List[BaseConstraint] = [
            FitConstraints(),
            ManufacturingConstraints(),
            GradingConstraints()
        ]
    
    def add_constraint(self, constraint: BaseConstraint) -> 'ConstraintValidator':
        """
        Добавить пользовательское ограничение
        
        Args:
            constraint: ограничение
            
        Returns:
            себя для цепочки вызовов
        """
        self.constraints.append(constraint)
        return self
    
    def remove_constraint(self, constraint_name: str) -> 'ConstraintValidator':
        """
        Удалить ограничение по имени
        
        Args:
            constraint_name: имя ограничения
            
        Returns:
            себя для цепочки вызовов
        """
        self.constraints = [
            c for c in self.constraints 
            if c.name != constraint_name
        ]
        return self
    
    def validate(self, pattern_model) -> ConstraintResult:
        """
        Валидировать PatternModel по всем ограничениям
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            результат валидации
        """
        all_violations = []
        
        for constraint in self.constraints:
            try:
                violations = constraint.validate(pattern_model)
                all_violations.extend(violations)
            except Exception as e:
                # Если ограничение упало с ошибкой, создаем violation
                from .base import ConstraintViolation
                
                all_violations.append(ConstraintViolation(
                    type="system",
                    rule=f"constraint_{constraint.name}_failed",
                    actual={"error": str(e)},
                    severity="error",
                    message=f"Ограничение {constraint.name} завершилось с ошибкой"
                ))
        
        return ConstraintResult(all_violations)
    
    def validate_fit_only(self, pattern_model) -> ConstraintResult:
        """
        Валидировать только ограничения посадки
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            результат валидации
        """
        fit_constraint = next(
            (c for c in self.constraints if isinstance(c, FitConstraints)),
            None
        )
        
        if fit_constraint is None:
            from .base import ConstraintViolation
            return ConstraintResult([
                ConstraintViolation(
                    type="system",
                    rule="fit_constraint_not_found",
                    actual={},
                    severity="error",
                    message="Ограничение посадки не найдено"
                )
            ])
        
        violations = fit_constraint.validate(pattern_model)
        return ConstraintResult(violations)
    
    def validate_manufacturing_only(self, pattern_model) -> ConstraintResult:
        """
        Валидировать только производственные ограничения
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            результат валидации
        """
        manufacturing_constraint = next(
            (c for c in self.constraints if isinstance(c, ManufacturingConstraints)),
            None
        )
        
        if manufacturing_constraint is None:
            from .base import ConstraintViolation
            return ConstraintResult([
                ConstraintViolation(
                    type="system",
                    rule="manufacturing_constraint_not_found",
                    actual={},
                    severity="error",
                    message="Производственное ограничение не найдено"
                )
            ])
        
        violations = manufacturing_constraint.validate(pattern_model)
        return ConstraintResult(violations)
    
    def validate_grading_only(self, pattern_model) -> ConstraintResult:
        """
        Валидировать только ограничения градации
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            результат валидации
        """
        grading_constraint = next(
            (c for c in self.constraints if isinstance(c, GradingConstraints)),
            None
        )
        
        if grading_constraint is None:
            from .base import ConstraintViolation
            return ConstraintResult([
                ConstraintViolation(
                    type="system",
                    rule="grading_constraint_not_found",
                    actual={},
                    severity="error",
                    message="Ограничение градации не найдено"
                )
            ])
        
        violations = grading_constraint.validate(pattern_model)
        return ConstraintResult(violations)
    
    def get_constraint_names(self) -> List[str]:
        """
        Получить имена всех ограничений
        
        Returns:
            список имен ограничений
        """
        return [constraint.name for constraint in self.constraints]
    
    def get_constraint_descriptions(self) -> dict:
        """
        Получить описания всех ограничений
        
        Returns:
            словарь {имя: описание}
        """
        return {
            constraint.name: constraint.description 
            for constraint in self.constraints
        }


# Создаем валидатор по умолчанию
default_validator = ConstraintValidator()


def validate_pattern_model(pattern_model) -> ConstraintResult:
    """
    Валидировать PatternModel с ограничениями по умолчанию
    
    Args:
        pattern_model: модель паттерна
        
    Returns:
        результат валидации
    """
    return default_validator.validate(pattern_model)
