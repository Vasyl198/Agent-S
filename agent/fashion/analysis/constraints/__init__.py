"""
🛡️ CONSTRAINT ENGINE — AI ДОЛЖЕН ЗНАТЬ, КОГДА ОН ОШИБСЯСЯ
========================================================

🎯 Независимый слой ограничений для PatternModel

❌ НЕ читает геометрию
❌ НЕ импортирует CAD Core
❌ НЕ знает про DXF
❌ НЕ вызывает processors
✅ Работает только с explain() и данными
"""

from .base import BaseConstraint, ConstraintViolation
from .fit_constraints import FitConstraints
from .manufacturing_constraints import ManufacturingConstraints
from .grading_constraints import GradingConstraints
from .validator import ConstraintValidator

__all__ = [
    'BaseConstraint',
    'ConstraintViolation',
    'FitConstraints',
    'ManufacturingConstraints',
    'GradingConstraints',
    'ConstraintValidator'
]
