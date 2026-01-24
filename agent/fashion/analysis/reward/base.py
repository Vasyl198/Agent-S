"""
📊 BASE REWARD — ОСНОВА ОЦЕНКИ КАЧЕСТВА
==========================================

🎯 Базовые классы для Reward Engine
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


@dataclass(frozen=True)
class RewardResult:
    """
    Результат оценки качества
    
    📌 ВСЕГДА возвращает число + breakdown
    """
    total_score: float
    components: Dict[str, float]
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Валидация после создания"""
        if not 0.0 <= self.total_score <= 1.0:
            raise ValueError(f"Total score must be in [0.0, 1.0], got {self.total_score}")
        
        for component, score in self.components.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Component {component} score must be in [0.0, 1.0], got {score}")
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "total_score": self.total_score,
            "components": self.components,
            "details": self.details or {}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RewardResult':
        """Создать из словаря"""
        return cls(
            total_score=data["total_score"],
            components=data["components"],
            details=data.get("details")
        )


class RewardComponent(ABC):
    """
    Базовый класс для компонентов оценки
    
    📌 Интерфейс для всех типов оценки
    """
    
    @abstractmethod
    def evaluate(self, pattern_model, constraint_result=None) -> float:
        """
        Оценить PatternModel
        
        Args:
            pattern_model: модель паттерна
            constraint_result: результат валидации ограничений (опционально)
            
        Returns:
            оценка в диапазоне [0.0, 1.0]
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Название компонента"""
        pass
    
    @property
    @abstractmethod
    def weight(self) -> float:
        """Вес компонента в общей оценке"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание компонента"""
        pass


class WeightedRewardComponent(RewardComponent):
    """
    Взвешенный компонент оценки
    
    📌 Базовый класс с весом
    """
    
    def __init__(self, weight: float = 1.0):
        """
        Инициализировать компонент с весом
        
        Args:
            weight: вес компонента (по умолчанию 1.0)
        """
        self._weight = weight
    
    @property
    def weight(self) -> float:
        """Вес компонента"""
        return self._weight
    
    def set_weight(self, weight: float) -> 'WeightedRewardComponent':
        """
        Установить вес компонента
        
        Args:
            weight: новый вес
            
        Returns:
            себя для цепочки вызовов
        """
        if not 0.0 <= weight <= 1.0:
            raise ValueError(f"Weight must be in [0.0, 1.0], got {weight}")
        
        self._weight = weight
        return self
