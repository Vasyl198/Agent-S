"""
📊 FEEDBACK & REWARD ENGINE — AI ДОЛЖЕН ПОНИМАТЬ, НАСКОЛЬКО ХОРОШО ОН СДЕЛАЛ
================================================================================

🎯 Превращает ConstraintValidator + explain-данные → числовую оценку качества

❌ НЕ меняет модель
❌ НЕ знает про геометрию
❌ НЕ вызывает processors
✅ Готов для RL, evolutionary optimization, auto-fitting, self-play
"""

from .base import RewardComponent, RewardResult
from .constraint_score import ConstraintScore
from .fit_score import FitScore
from .manufacturing_score import ManufacturingScore
from .grading_score import GradingScore
from .evaluator import RewardEvaluator

__all__ = [
    'RewardComponent',
    'RewardResult',
    'ConstraintScore',
    'FitScore',
    'ManufacturingScore',
    'GradingScore',
    'RewardEvaluator'
]
