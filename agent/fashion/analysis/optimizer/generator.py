"""
🎲 CANDIDATE GENERATOR — ГЕНЕРАТОР КАНДИДАТОВ
============================================

🎯 Генерирует несколько предложений изменений

❌ НЕ читает геометрию
✅ Только детерминированные предложения
"""

from typing import List, Dict, Any, Optional


class CandidateGenerator:
    """
    Генератор кандидатов на оптимизацию
    
    📌 Создает детерминированные предложения изменений
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Инициализировать генератор
        
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
    
    def generate_candidates(self, pattern_model, count: int = 5) -> List[Dict[str, Any]]:
        """
        Сгенерировать кандидатов на оптимизацию
        
        Args:
            pattern_model: исходная модель паттерна
            count: количество кандидатов
            
        Returns:
            список предложений изменений
        """
        proposals = []
        
        # Генерируем разные типы предложений
        proposals.extend(self._generate_seam_allowance_proposals(pattern_model))
        proposals.extend(self._generate_notch_proposals(pattern_model))
        proposals.extend(self._generate_grading_proposals(pattern_model))
        
        # Ограничиваем количество
        return proposals[:count]
    
    def _generate_seam_allowance_proposals(self, pattern_model) -> List[Dict[str, Any]]:
        """
        Сгенерировать предложения по припускам
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            список предложений
        """
        proposals = []
        
        if pattern_model.manufacturing is None:
            return proposals
        
        try:
            manufacturing_explain = pattern_model.manufacturing.explain()
        except Exception:
            return proposals
        
        seam_allowances = manufacturing_explain.get("seam_allowances", {})
        
        for role, current_value in seam_allowances.items():
            # Предлагаем уменьшить припуск
            if current_value > 5.0:
                reduction = min(5.0, current_value * 0.2)  # 20% или 5мм
                proposals.append({
                    "type": "target",
                    "goal": "reduce_seam_allowance",
                    "role": role,
                    "by": reduction
                })
            
            # Предлагаем увеличить припуск
            if current_value < 25.0:
                increase = min(5.0, current_value * 0.2)  # 20% или 5мм
                proposals.append({
                    "type": "target",
                    "goal": "increase_seam_allowance",
                    "role": role,
                    "by": increase
                })
        
        return proposals
    
    def _generate_notch_proposals(self, pattern_model) -> List[Dict[str, Any]]:
        """
        Сгенерировать предложения по надсечкам
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            список предложений
        """
        proposals = []
        
        if pattern_model.manufacturing is None:
            return proposals
        
        try:
            manufacturing_explain = pattern_model.manufacturing.explain()
        except Exception:
            return proposals
        
        notches = manufacturing_explain.get("notches", {})
        
        for role, current_count in notches.items():
            # Предлагаем добавить надсечку
            if current_count == 0:
                proposals.append({
                    "type": "target",
                    "goal": "change_notch_count",
                    "role": role,
                    "to": 1
                })
            elif current_count < 3:
                proposals.append({
                    "type": "target",
                    "goal": "change_notch_count",
                    "role": role,
                    "to": current_count + 1
                })
            
            # Предлагаем убрать надсечку
            if current_count > 5:
                proposals.append({
                    "type": "target",
                    "goal": "change_notch_count",
                    "role": role,
                    "to": current_count - 1
                })
        
        return proposals
    
    def _generate_grading_proposals(self, pattern_model) -> List[Dict[str, Any]]:
        """
        Сгенерировать предложения по градации
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            список предложений
        """
        proposals = []
        
        if pattern_model.grading is None:
            return proposals
        
        try:
            grading_explain = pattern_model.grading.explain()
        except Exception:
            return proposals
        
        rules = grading_explain.get("rules", {})
        
        for role, rule_data in rules.items():
            if isinstance(rule_data, dict):
                dx = rule_data.get("dx", 0)
                dy = rule_data.get("dy", 0)
                
                # Предлагаем уменьшить смещение
                if abs(dx) > 10.0:
                    new_dx = dx * 0.8  # Уменьшаем на 20%
                    proposals.append({
                        "type": "target",
                        "goal": "change_grading_dx",
                        "role": role,
                        "to": new_dx
                    })
                
                if abs(dy) > 10.0:
                    new_dy = dy * 0.8  # Уменьшаем на 20%
                    proposals.append({
                        "type": "target",
                        "goal": "change_grading_dy",
                        "role": role,
                        "to": new_dy
                    })
        
        return proposals
    
    def generate_empty_proposal(self) -> Dict[str, Any]:
        """
        Сгенерировать пустое предложение (no-op)
        
        Returns:
            пустое предложение
        """
        return {
            "type": "noop",
            "goal": "no_change"
        }


import logging
logger = logging.getLogger(__name__)

logger.debug("CandidateGenerator loaded")
