"""
🔄 OPTIMIZATION LOOP — САМОСТОЯТЕЛЬНОЕ УЛУЧШЕНИЕ ЛЕКАЛА
======================================================

🎯 Создает Optimization Loop, который генерирует предложения, применяет их безопасно,
оценивает через Reward Engine и выбирает лучший PatternModel

❗ НИЧЕГО не ломает
❗ Полностью детерминирован (без ML на этом этапе)
"""

try:
    from .base import BaseOptimizer, OptimizationResult
    from .candidate import OptimizationCandidate
    from .generator import CandidateGenerator
    from .evaluator import CandidateEvaluator
    from .loop import OptimizationLoop
    from .report import OptimizationReportBuilder
    
    __all__ = [
        'BaseOptimizer',
        'OptimizationResult',
        'OptimizationCandidate',
        'CandidateGenerator',
        'CandidateEvaluator',
        'OptimizationLoop',
        'OptimizationReportBuilder'
    ]
except ImportError as e:
    # Fallback если модули недоступны
    print(f"Warning: Could not import optimizer modules: {e}")
    __all__ = []
