"""
📊 CANDIDATE EVALUATOR — ОЦЕНЩИК КАНДИДАТОВ
============================================

🎯 Применяет предложения и оценивает кандидатов

❌ НЕ читает геометрию
✅ Только API-вызовы
"""

from typing import Any, Dict, Optional, List
from .candidate import OptimizationCandidate, CandidatePool


class DemoRewardEvaluator:
    """
    Демо оценщик качества, который дает разные scores на основе proposal/target
    """
    
    def __init__(self, target: Optional[Dict[str, Any]] = None):
        self.target = target or {}
    
    def evaluate(self, pattern_model, constraint_result=None, proposal=None) -> Any:
        """
        Оценить модель по proposal относительно target
        
        Args:
            pattern_model: модель паттерна (не используется в демо)
            constraint_result: результат валидации ограничений
            proposal: предложение изменений
            
        Returns:
            объект с total_score
        """
        from types import SimpleNamespace
        
        # Если нет proposal или target - нейтральная оценка
        if not proposal or not self.target:
            return SimpleNamespace(total_score=0.5)
        
        # Если constraint не ok - минимальная оценка
        if constraint_result and not constraint_result.ok:
            return SimpleNamespace(total_score=0.0)
        
        # Демо scoring на основе совпадения proposal с target
        t_goal = self.target.get("goal")
        t_role = self.target.get("role")
        t_by = float(self.target.get("by") or 0.0)
        
        p_goal = proposal.get("goal")
        p_role = proposal.get("role")
        p_by = float(proposal.get("by") or 0.0)
        
        score = 0.5  # базовая оценка
        
        # Совпадение role -> +0.2
        if p_role is not None and p_role == t_role:
            score += 0.2
        
        # Совпадение goal -> +0.1
        if p_goal is not None and p_goal == t_goal:
            score += 0.1
        
        # Штраф за расхождение в by
        by_diff = abs(p_by - t_by)
        score -= by_diff * 0.02
        
        # Ограничиваем диапазон [0, 1]
        score = max(0.0, min(1.0, score))
        
        return SimpleNamespace(total_score=score)


class CandidateEvaluator:
    """
    Оценщик кандидатов на оптимизацию
    
    📌 Применяет предложения и оценивает через Constraint Engine и Reward Engine
    """
    
    def __init__(self, constraint_validator=None, reward_evaluator=None, target: Optional[Dict[str, Any]] = None):
        """
        Инициализировать оценщик
        
        Args:
            constraint_validator: валидатор ограничений
            reward_evaluator: оценщик качества
            target: цель оптимизации для демо reward evaluator
        """
        self.constraint_validator = constraint_validator
        self.reward_evaluator = reward_evaluator
        self.target = target
        
        # Если нет reward_evaluator, создаем демо
        if self.reward_evaluator is None and self.target is not None:
            self.reward_evaluator = DemoRewardEvaluator(target=self.target)
    
    def evaluate_candidate(
        self, 
        pattern_model, 
        proposal: Optional[Dict[str, Any]] = None
    ) -> OptimizationCandidate:
        """
        Оценить одного кандидата
        
        Args:
            pattern_model: исходная модель паттерна
            proposal: предложение изменений
            
        Returns:
            кандидат с результатами оценки
        """
        # Если нет предложения, возвращаем исходную модель
        if proposal is None or proposal.get("type") == "noop":
            return OptimizationCandidate(
                model=pattern_model,
                proposal=None,
                score=self._evaluate_model(pattern_model),
                is_valid=True
            )
        
        try:
            # Применяем предложение
            new_model = self._apply_proposal(pattern_model, proposal)
            
            # Валидируем ограничения
            constraint_result = None
            is_valid = True
            error_message = None
            
            if self.constraint_validator:
                try:
                    constraint_result = self.constraint_validator.validate(new_model)
                    is_valid = constraint_result.ok
                except Exception as e:
                    is_valid = False
                    error_message = f"Constraint validation failed: {str(e)}"
            
            # Оцениваем качество
            score = 0.0
            if is_valid:
                score = self._evaluate_model(new_model, constraint_result, proposal=proposal)
            else:
                score = 0.0  # Невалидные модели получают минимальную оценку
            
            return OptimizationCandidate(
                model=new_model,
                proposal=proposal,
                score=score,
                constraint_result=constraint_result,
                is_valid=is_valid,
                error_message=error_message
            )
            
        except Exception as e:
            # Если применение предложения не удалось
            return OptimizationCandidate(
                model=pattern_model,
                proposal=proposal,
                score=0.0,
                is_valid=False,
                error_message=f"Failed to apply proposal: {str(e)}"
            )
    
    def evaluate_candidates(
        self, 
        pattern_model, 
        proposals: List[Dict[str, Any]]
    ) -> CandidatePool:
        """
        Оценить несколько кандидатов
        
        Args:
            pattern_model: исходная модель паттерна
            proposals: список предложений
            
        Returns:
            пул кандидатов с результатами оценки
        """
        pool = CandidatePool()
        
        for proposal in proposals:
            candidate = self.evaluate_candidate(pattern_model, proposal)
            pool.add_candidate(candidate)
        
        return pool
    
    def _apply_proposal(self, pattern_model, proposal: Dict[str, Any]) -> Any:
        """
        Применить предложение к модели
        
        Args:
            pattern_model: исходная модель
            proposal: предложение
            
        Returns:
            новая модель
        """
        # Импортируем здесь, чтобы избежать циклических зависимостей
        try:
            from ..apply_proposal import apply_rule_proposal
            return apply_rule_proposal(pattern_model, proposal)
        except Exception as e:
            # ВАЖНО: не делаем тихий fallback - поднимаем ошибку
            raise RuntimeError(f"apply_rule_proposal failed: {e}") from e
    
    def _evaluate_model(self, pattern_model, constraint_result=None, proposal=None) -> float:
        """
        Оценить модель через Reward Engine
        
        Args:
            pattern_model: модель паттерна
            constraint_result: результат валидации ограничений
            proposal: предложение изменений (для демо evaluator)
            
        Returns:
            оценка качества
        """
        if self.reward_evaluator is None:
            # Если нет оценщика, возвращаем нейтральную оценку
            return 0.5
        
        try:
            # Передаем proposal в демо evaluator
            if hasattr(self.reward_evaluator, 'evaluate'):
                reward_result = self.reward_evaluator.evaluate(
                    pattern_model, 
                    constraint_result, 
                    proposal=proposal
                )
                return reward_result.total_score
            else:
                # Обратная совместимость
                reward_result = self.reward_evaluator.evaluate(pattern_model, constraint_result)
                return reward_result.total_score
        except Exception:
            # Если оценка не удалась, возвращаем минимальную
            return 0.0
    
    def set_constraint_validator(self, constraint_validator) -> None:
        """
        Установить валидатор ограничений
        
        Args:
            constraint_validator: валидатор ограничений
        """
        self.constraint_validator = constraint_validator
    
    def set_reward_evaluator(self, reward_evaluator) -> None:
        """
        Установить оценщик качества
        
        Args:
            reward_evaluator: оценщик качества
        """
        self.reward_evaluator = reward_evaluator


import logging
logger = logging.getLogger(__name__)

logger.debug("CandidateEvaluator loaded")
