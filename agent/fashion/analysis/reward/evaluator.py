"""
📊 REWARD EVALUATOR — ОРКЕСТРАТОР ОЦЕНКИ
==========================================

🎯 Агрегатор всех компонентов оценки

❌ НЕ читает геометрию
✅ Только оркестрация оценки
"""

from typing import List, Dict
from .base import RewardComponent, RewardResult
from .constraint_score import ConstraintScore
from .fit_score import FitScore
from .manufacturing_score import ManufacturingScore
from .grading_score import GradingScore


class RewardEvaluator:
    """
    Оценщик качества PatternModel
    
    📌 Агрегирует все компоненты оценки
    📌 ВСЕГДА возвращает число + breakdown
    """
    
    def __init__(self):
        """Инициализировать оценщик с компонентами по умолчанию"""
        self.components: List[RewardComponent] = [
            ConstraintScore(weight=0.4),      # Самый важный
            FitScore(weight=0.3),
            ManufacturingScore(weight=0.2),
            GradingScore(weight=0.1)
        ]
    
    def add_component(self, component: RewardComponent) -> 'RewardEvaluator':
        """
        Добавить пользовательский компонент оценки
        
        Args:
            component: компонент оценки
            
        Returns:
            себя для цепочки вызовов
        """
        self.components.append(component)
        return self
    
    def remove_component(self, component_name: str) -> 'RewardEvaluator':
        """
        Удалить компонент по имени
        
        Args:
            component_name: имя компонента
            
        Returns:
            себя для цепочки вызовов
        """
        self.components = [
            c for c in self.components 
            if c.name != component_name
        ]
        return self
    
    def set_component_weight(self, component_name: str, weight: float) -> 'RewardEvaluator':
        """
        Установить вес компонента
        
        Args:
            component_name: имя компонента
            weight: новый вес
            
        Returns:
            себя для цепочки вызовов
        """
        for component in self.components:
            if component.name == component_name:
                if hasattr(component, 'set_weight'):
                    component.set_weight(weight)
                break
        
        return self
    
    def evaluate(self, pattern_model, constraint_result=None) -> RewardResult:
        """
        Оценить PatternModel по всем компонентам
        
        Args:
            pattern_model: модель паттерна
            constraint_result: результат валидации ограничений
            
        Returns:
            результат оценки
        """
        component_scores = {}
        component_details = {}
        
        # Оцениваем каждый компонент
        for component in self.components:
            try:
                score = component.evaluate(pattern_model, constraint_result)
                component_scores[component.name] = score
                
                # Собираем детали (если есть)
                if hasattr(component, '__dict__'):
                    component_details[component.name] = {
                        'weight': component.weight,
                        'description': component.description
                    }
                
            except Exception as e:
                # Если компонент упал с ошибкой, ставим минимальную оценку
                component_scores[component.name] = 0.0
                component_details[component.name] = {
                    'weight': getattr(component, 'weight', 0.0),
                    'description': getattr(component, 'description', ''),
                    'error': str(e)
                }
        
        # Вычисляем общую оценку с весами
        total_score = self._compute_weighted_score(component_scores)
        
        return RewardResult(
            total_score=total_score,
            components=component_scores,
            details=component_details
        )
    
    def _compute_weighted_score(self, component_scores: Dict[str, float]) -> float:
        """
        Вычислить взвешенную оценку
        
        Args:
            component_scores: оценки компонентов
            
        Returns:
            взвешенная оценка
        """
        total_weight = 0.0
        weighted_sum = 0.0
        
        for component in self.components:
            score = component_scores.get(component.name, 0.0)
            weight = component.weight
            
            weighted_sum += score * weight
            total_weight += weight
        
        # Нормализуем по общему весу
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.0
    
    def evaluate_constraints_only(self, pattern_model) -> RewardResult:
        """
        Оценить только ограничения
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            результат оценки
        """
        constraint_component = next(
            (c for c in self.components if isinstance(c, ConstraintScore)),
            None
        )
        
        if constraint_component is None:
            return RewardResult(
                total_score=0.0,
                components={},
                details={"error": "ConstraintScore component not found"}
            )
        
        score = constraint_component.evaluate(pattern_model)
        
        return RewardResult(
            total_score=score,
            components={"constraints": score},
            details={"constraints": {
                "weight": constraint_component.weight,
                "description": constraint_component.description
            }}
        )
    
    def get_component_names(self) -> List[str]:
        """
        Получить имена всех компонентов
        
        Returns:
            список имен компонентов
        """
        return [component.name for component in self.components]
    
    def get_component_descriptions(self) -> Dict[str, str]:
        """
        Получить описания всех компонентов
        
        Returns:
            словарь {имя: описание}
        """
        return {
            component.name: component.description 
            for component in self.components
        }
    
    def get_component_weights(self) -> Dict[str, float]:
        """
        Получить веса всех компонентов
        
        Returns:
            словарь {имя: вес}
        """
        return {
            component.name: component.weight 
            for component in self.components
        }


# Создаем оценщик по умолчанию
default_evaluator = RewardEvaluator()


def evaluate_pattern_model(pattern_model, constraint_result=None) -> RewardResult:
    """
    Оценить PatternModel с компонентами по умолчанию
    
    Args:
        pattern_model: модель паттерна
        constraint_result: результат валидации ограничений
        
    Returns:
        результат оценки
    """
    return default_evaluator.evaluate(pattern_model, constraint_result)
