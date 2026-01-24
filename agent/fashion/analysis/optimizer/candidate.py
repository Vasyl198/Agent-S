"""
🎯 OPTIMIZATION CANDIDATE — КАНДИДАТ ОПТИМИЗАЦИИ
===============================================

🎯 Представляет один вариант оптимизации с результатами оценки
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass(frozen=True)
class OptimizationCandidate:
    """
    Кандидат на оптимизацию
    
    📌 Содержит модель, предложение и результаты оценки
    """
    model: Any  # PatternModel
    proposal: Optional[Dict[str, Any]]
    score: float
    constraint_result: Optional[Any] = None
    reward_result: Optional[Any] = None
    is_valid: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Валидация после создания"""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be in [0.0, 1.0], got {self.score}")
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "score": self.score,
            "is_valid": self.is_valid,
            "proposal": self.proposal,
            "error_message": self.error_message,
            "has_constraint_result": self.constraint_result is not None,
            "has_reward_result": self.reward_result is not None
        }
    
    @classmethod
    def from_dict(cls, data: dict, model: Any) -> 'OptimizationCandidate':
        """Создать из словаря"""
        return cls(
            model=model,
            proposal=data.get("proposal"),
            score=data["score"],
            is_valid=data.get("is_valid", True),
            error_message=data.get("error_message")
        )
    
    def is_better_than(self, other: 'OptimizationCandidate') -> bool:
        """
        Проверить, лучше ли этот кандидат другого
        
        Args:
            other: другой кандидат
            
        Returns:
            True если этот кандидат лучше
        """
        # Сначала валидность
        if self.is_valid and not other.is_valid:
            return True
        if not self.is_valid and other.is_valid:
            return False
        
        # Затем оценка
        return self.score > other.score
    
    @property
    def improvement_needed(self) -> float:
        """
        Насколько нужно улучшить до идеала
        
        Returns:
            1.0 - score
        """
        return 1.0 - self.score


class CandidatePool:
    """
    Пул кандидатов на оптимизацию
    
    📌 Управляет коллекцией кандидатов
    """
    
    def __init__(self):
        """Инициализировать пул"""
        self.candidates: List[OptimizationCandidate] = []
    
    def add_candidate(self, candidate: OptimizationCandidate) -> None:
        """
        Добавить кандидата в пул
        
        Args:
            candidate: кандидат
        """
        self.candidates.append(candidate)
    
    def get_best_candidate(self) -> Optional[OptimizationCandidate]:
        """
        Получить лучшего кандидата
        
        Returns:
            лучший кандидат или None
        """
        if not self.candidates:
            return None
        
        # Фильтруем валидных кандидатов
        valid_candidates = [c for c in self.candidates if c.is_valid]
        
        if not valid_candidates:
            # Если нет валидных, возвращаем лучший из всех
            return max(self.candidates, key=lambda c: c.score)
        
        return max(valid_candidates, key=lambda c: c.score)
    
    def get_valid_candidates(self) -> List[OptimizationCandidate]:
        """
        Получить всех валидных кандидатов
        
        Returns:
            список валидных кандидатов
        """
        return [c for c in self.candidates if c.is_valid]
    
    def get_sorted_candidates(self) -> List[OptimizationCandidate]:
        """
        Получить кандидатов, отсортированных по оценке
        
        Returns:
            отсортированный список кандидатов
        """
        return sorted(self.candidates, key=lambda c: c.score, reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику по пулу
        
        Returns:
            статистика
        """
        if not self.candidates:
            return {
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "best_score": None,
                "worst_score": None,
                "average_score": None
            }
        
        valid_candidates = self.get_valid_candidates()
        scores = [c.score for c in self.candidates]
        
        return {
            "total": len(self.candidates),
            "valid": len(valid_candidates),
            "invalid": len(self.candidates) - len(valid_candidates),
            "best_score": max(scores),
            "worst_score": min(scores),
            "average_score": sum(scores) / len(scores)
        }
    
    def clear(self) -> None:
        """Очистить пул"""
        self.candidates.clear()
    
    def __len__(self) -> int:
        """Размер пула"""
        return len(self.candidates)
    
    def __iter__(self):
        """Итератор по кандидатам"""
        return iter(self.candidates)
