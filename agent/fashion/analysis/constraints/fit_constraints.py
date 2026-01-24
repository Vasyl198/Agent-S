"""
👗 FIT CONSTRAINTS — ОГРАНИЧЕНИЯ ПОСАДКИ
========================================

🎯 Работают с PatternDimensions

❌ НЕ читают геометрию
✅ Только размеры и правила посадки
"""

from typing import List
from .base import BaseConstraint, ConstraintViolation


class FitConstraints(BaseConstraint):
    """
    Ограничения посадки
    
    📌 Проверяют физическую возможность конструкции
    """
    
    def validate(self, pattern_model) -> List[ConstraintViolation]:
        """
        Валидировать ограничения посадки
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            список нарушений ограничений
        """
        violations = []
        
        # Получаем размеры
        dimensions = pattern_model.dimensions
        if dimensions is None:
            return violations
        
        # Правило: ширина низа >= обхват талии
        if hasattr(dimensions, 'hem_width') and hasattr(dimensions, 'waist_length'):
            hem_width = getattr(dimensions, 'hem_width', 0)
            waist_length = getattr(dimensions, 'waist_length', 0)
            
            if hem_width < waist_length:
                violations.append(ConstraintViolation(
                    type="fit",
                    rule="hem_width >= waist_length",
                    actual={
                        "hem_width": hem_width,
                        "waist_length": waist_length
                    },
                    severity="error",
                    message="Ширина низа должна быть не меньше обхвата талии"
                ))
        
        # Правило: длина изделия > 0
        if hasattr(dimensions, 'garment_length'):
            garment_length = getattr(dimensions, 'garment_length', 0)
            
            if garment_length <= 0:
                violations.append(ConstraintViolation(
                    type="fit",
                    rule="garment_length > 0",
                    actual={"garment_length": garment_length},
                    severity="error",
                    message="Длина изделия должна быть положительной"
                ))
        
        # Правило: обхват талии > 0
        if hasattr(dimensions, 'waist_length'):
            waist_length = getattr(dimensions, 'waist_length', 0)
            
            if waist_length <= 0:
                violations.append(ConstraintViolation(
                    type="fit",
                    rule="waist_length > 0",
                    actual={"waist_length": waist_length},
                    severity="error",
                    message="Обхват талии должен быть положительным"
                ))
        
        # Правило: ширина низа > 0
        if hasattr(dimensions, 'hem_width'):
            hem_width = getattr(dimensions, 'hem_width', 0)
            
            if hem_width <= 0:
                violations.append(ConstraintViolation(
                    type="fit",
                    rule="hem_width > 0",
                    actual={"hem_width": hem_width},
                    severity="error",
                    message="Ширина низа должна быть положительной"
                ))
        
        # Правило: разумное соотношение ширины к длине
        if hasattr(dimensions, 'hem_width') and hasattr(dimensions, 'garment_length'):
            hem_width = getattr(dimensions, 'hem_width', 0)
            garment_length = getattr(dimensions, 'garment_length', 0)
            
            if garment_length > 0:
                ratio = hem_width / garment_length
                if ratio > 3.0:  # Слишком широкое
                    violations.append(ConstraintViolation(
                        type="fit",
                        rule="hem_width / garment_length <= 3.0",
                        actual={
                            "hem_width": hem_width,
                            "garment_length": garment_length,
                            "ratio": ratio
                        },
                        severity="warning",
                        message="Изделие может быть слишком широким"
                    ))
                elif ratio < 0.1:  # Слишком узкое
                    violations.append(ConstraintViolation(
                        type="fit",
                        rule="hem_width / garment_length >= 0.1",
                        actual={
                            "hem_width": hem_width,
                            "garment_length": garment_length,
                            "ratio": ratio
                        },
                        severity="warning",
                        message="Изделие может быть слишком узким"
                    ))
        
        return violations
    
    @property
    def name(self) -> str:
        """Название ограничения"""
        return "fit_constraints"
    
    @property
    def description(self) -> str:
        """Описание ограничения"""
        return "Ограничения посадки: проверка физической возможности конструкции"
