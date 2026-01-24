"""
🔄 BASE OPTIMIZER — ОСНОВА ОПТИМИЗАТОРА
========================================

🎯 Базовые классы для Optimization Loop
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


@dataclass(frozen=True)
class OptimizationResult:
    """
    Результат оптимизации
    
    📌 Содержит лучшую модель и сравнение с baseline
    """
    best_score: float
    baseline_score: float
    improvement: float
    chosen_proposal: Optional[Dict[str, Any]]
    candidates: List[Dict[str, Any]]
    best_model: Any  # PatternModel
    baseline_model: Any  # PatternModel
    
    def __post_init__(self):
        """Валидация после создания"""
        if not 0.0 <= self.best_score <= 1.0:
            raise ValueError(f"Best score must be in [0.0, 1.0], got {self.best_score}")
        
        if not 0.0 <= self.baseline_score <= 1.0:
            raise ValueError(f"Baseline score must be in [0.0, 1.0], got {self.baseline_score}")
        
        if not -1.0 <= self.improvement <= 1.0:
            raise ValueError(f"Improvement must be in [-1.0, 1.0], got {self.improvement}")
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "best_score": self.best_score,
            "baseline_score": self.baseline_score,
            "improvement": self.improvement,
            "chosen_proposal": self.chosen_proposal,
            "candidates": self.candidates,
            "improved": self.improvement > 0.01  # Значимое улучшение
        }
    
    @classmethod
    def from_dict(cls, data: dict, best_model: Any, baseline_model: Any) -> 'OptimizationResult':
        """Создать из словаря"""
        return cls(
            best_score=data["best_score"],
            baseline_score=data["baseline_score"],
            improvement=data["improvement"],
            chosen_proposal=data.get("chosen_proposal"),
            candidates=data.get("candidates", []),
            best_model=best_model,
            baseline_model=baseline_model
        )


class BaseOptimizer(ABC):
    """
    Базовый класс для оптимизаторов
    
    📌 Интерфейс для всех типов оптимизации
    """
    
    @abstractmethod
    def optimize(self, pattern_model, **kwargs) -> OptimizationResult:
        """
        Оптимизировать PatternModel
        
        Args:
            pattern_model: исходная модель паттерна
            **kwargs: дополнительные параметры
            
        Returns:
            результат оптимизации
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Название оптимизатора"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание оптимизатора"""
        pass


class DeterministicOptimizer(BaseOptimizer):
    """
    Детерминированный оптимизатор
    
    📌 Базовый класс с гарантией детерминизма
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Инициализировать оптимизатор
        
        Args:
            seed: seed для детерминизма
        """
        self.seed = seed
        if seed is not None:
            self._setup_determinism(seed)
    
    def _setup_determinism(self, seed: int):
        """
        Настроить детерминизм
        
        Args:
            seed: seed для детерминизма
        """
        import random
        random.seed(seed)
        
        # Если есть numpy, тоже настраиваем
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass
