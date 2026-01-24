"""
🛡️ CONSTRAINT SCORE — ОЦЕНКА ОГРАНИЧЕНИЙ
========================================

🎯 Использует ConstraintValidator для оценки качества

❌ НЕ читает геометрию
✅ Только результат валидации ограничений
"""

from .base import WeightedRewardComponent


class ConstraintScore(WeightedRewardComponent):
    """
    Оценка на основе ограничений
    
    📌 error → score = 0
    📌 warning → штраф
    📌 ok → 1.0
    """
    
    def __init__(self, weight: float = 1.0, warning_penalty: float = 0.1):
        """
        Инициализировать оценку ограничений
        
        Args:
            weight: вес компонента
            warning_penalty: штраф за предупреждение
        """
        super().__init__(weight)
        self.warning_penalty = warning_penalty
    
    def evaluate(self, pattern_model, constraint_result=None) -> float:
        """
        Оценить PatternModel на основе ограничений
        
        Args:
            pattern_model: модель паттерна
            constraint_result: результат валидации ограничений
            
        Returns:
            оценка в диапазоне [0.0, 1.0]
        """
        if constraint_result is None:
            # Если нет результата валидации, считаем идеальным
            return 1.0
        
        # Если есть ошибки, оценка = 0
        if hasattr(constraint_result, 'errors') and constraint_result.errors:
            return 0.0
        
        # Штраф за предупреждения
        if hasattr(constraint_result, 'warnings') and constraint_result.warnings:
            warning_count = len(constraint_result.warnings)
            # Каждое предупреждение снижает оценку
            penalty = min(warning_count * self.warning_penalty, 0.5)  # Максимум 50% штрафа
            return max(0.0, 1.0 - penalty)
        
        # Если нет ошибок и предупреждений, оценка = 1.0
        return 1.0
    
    @property
    def name(self) -> str:
        """Название компонента"""
        return "constraints"
    
    @property
    def description(self) -> str:
        """Описание компонента"""
        return "Оценка на основе ограничений: error → 0, warning → штраф, ok → 1.0"
    
    def set_warning_penalty(self, penalty: float) -> 'ConstraintScore':
        """
        Установить штраф за предупреждение
        
        Args:
            penalty: новый штраф
            
        Returns:
            себя для цепочки вызовов
        """
        if not 0.0 <= penalty <= 1.0:
            raise ValueError(f"Warning penalty must be in [0.0, 1.0], got {penalty}")
        
        self.warning_penalty = penalty
        return self
