"""
📐 GRADING SCORE — ОЦЕНКА ГРАДАЦИИ
===================================

🎯 Использует grading.explain() для оценки качества

❌ НЕ читает геометрию
✅ Только правила градации
"""

from typing import Optional
from .base import WeightedRewardComponent


class GradingScore(WeightedRewardComponent):
    """
    Оценка качества правил градации
    
    📌 Основана на разумности смещений и симметрии
    """
    
    def __init__(self, weight: float = 1.0):
        """Инициализировать оценку градации"""
        super().__init__(weight)
    
    def evaluate(self, pattern_model, constraint_result=None) -> float:
        """
        Оценить PatternModel на основе правил градации
        
        Args:
            pattern_model: модель паттерна
            constraint_result: результат валидации ограничений
            
        Returns:
            оценка в диапазоне [0.0, 1.0]
        """
        grading = pattern_model.grading
        if grading is None:
            # Если нет градации, оценка = 1.0 (нейтрально)
            return 1.0
        
        # Используем explain() для получения данных
        try:
            grading_explain = grading.explain()
        except Exception:
            # Если explain() не работает, оценка = 0.5
            return 0.5
        
        scores = []
        
        # Оценка правил смещения
        rules = grading_explain.get("rules", {})
        if rules:
            displacement_scores = []
            
            for role, rule_data in rules.items():
                if isinstance(rule_data, dict):
                    dx = rule_data.get("dx", 0)
                    dy = rule_data.get("dy", 0)
                    
                    # Разумные смещения: -20 до +20 мм
                    dx_score = self._evaluate_displacement(dx)
                    dy_score = self._evaluate_displacement(dy)
                    
                    # Средняя оценка для этого правила
                    rule_score = (dx_score + dy_score) / 2
                    displacement_scores.append(rule_score)
            
            if displacement_scores:
                scores.append(sum(displacement_scores) / len(displacement_scores))
            
            # Оценка симметрии (если есть парные правила)
            symmetry_score = self._evaluate_symmetry(rules)
            if symmetry_score is not None:
                scores.append(symmetry_score)
            
            # Оценка минимальности изменений
            minimality_score = self._evaluate_minimality(rules)
            if minimality_score is not None:
                scores.append(minimality_score)
        
        else:
            # Нет правил при разных размерах - штраф
            size_from = grading_explain.get("size_from")
            size_to = grading_explain.get("size_to")
            
            if size_from and size_to and size_from != size_to:
                scores.append(0.3)
            else:
                # Одинаковые размеры - нет градации, это нормально
                scores.append(1.0)
        
        # Возвращаем среднюю оценку
        if scores:
            return sum(scores) / len(scores)
        else:
            return 1.0  # Нет данных для оценки
    
    def _evaluate_displacement(self, displacement: float) -> float:
        """
        Оценить смещение
        
        Args:
            displacement: смещение в мм
            
        Returns:
            оценка в диапазоне [0.0, 1.0]
        """
        if abs(displacement) <= 10.0:
            # Маленькое смещение - хорошо
            return 1.0
        elif abs(displacement) <= 20.0:
            # Разумное смещение
            return 0.8
        elif abs(displacement) <= 50.0:
            # Большое смещение
            return 0.5
        else:
            # Экстремальное смещение
            return 0.2
    
    def _evaluate_symmetry(self, rules: dict) -> Optional[float]:
        """
        Оценить симметрию правил
        
        Args:
            rules: правила градации
            
        Returns:
            оценка симметрии или None
        """
        # Пары симметричных ролей
        symmetry_pairs = [
            ("WAIST_LEFT", "WAIST_RIGHT"),
            ("HIP_LEFT", "HIP_RIGHT"),
            ("HEM_LEFT", "HEM_RIGHT"),
            ("SIDE_LEFT", "SIDE_RIGHT")
        ]
        
        symmetry_scores = []
        
        for left_role, right_role in symmetry_pairs:
            if left_role in rules and right_role in rules:
                left_rule = rules[left_role]
                right_rule = rules[right_role]
                
                if isinstance(left_rule, dict) and isinstance(right_rule, dict):
                    left_dx = left_rule.get("dx", 0)
                    right_dx = right_rule.get("dx", 0)
                    
                    # Симметрия по dx (зеркальная)
                    if abs(left_dx + right_dx) < 1.0:  # Сумма должна быть близка к 0
                        symmetry_scores.append(1.0)
                    else:
                        symmetry_scores.append(0.5)
        
        if symmetry_scores:
            return sum(symmetry_scores) / len(symmetry_scores)
        
        return None
    
    def _evaluate_minimality(self, rules: dict) -> Optional[float]:
        """
        Оценить минимальность изменений
        
        Args:
            rules: правила градации
            
        Returns:
            оценка минимальности или None
        """
        if not rules:
            return None
        
        # Считаем общее количество изменений
        total_changes = len(rules)
        
        # Чем меньше изменений, тем лучше (но не меньше 1)
        if total_changes == 1:
            return 1.0
        elif total_changes <= 3:
            return 0.9
        elif total_changes <= 5:
            return 0.7
        elif total_changes <= 10:
            return 0.5
        else:
            return 0.3
    
    @property
    def name(self) -> str:
        """Название компонента"""
        return "grading"
    
    @property
    def description(self) -> str:
        """Описание компонента"""
        return "Оценка градации: разумность смещений, симметрия, минимальность"
