"""
👗 FIT SCORE — ОЦЕНКА ПОСАДКИ
==============================

🎯 Использует PatternDimensions для оценки качества посадки

❌ НЕ читает геометрию
✅ Только размеры и пропорции
"""

from .base import WeightedRewardComponent


class FitScore(WeightedRewardComponent):
    """
    Оценка качества посадки
    
    📌 Основана на пропорциях и разумных диапазонах размеров
    """
    
    def __init__(self, weight: float = 1.0):
        """Инициализировать оценку посадки"""
        super().__init__(weight)
    
    def evaluate(self, pattern_model, constraint_result=None) -> float:
        """
        Оценить PatternModel на основе посадки
        
        Args:
            pattern_model: модель паттерна
            constraint_result: результат валидации ограничений
            
        Returns:
            оценка в диапазоне [0.0, 1.0]
        """
        dimensions = pattern_model.dimensions
        if dimensions is None:
            # Если нет размеров, оценка = 1.0 (нейтрально)
            return 1.0
        
        scores = []
        
        # Оценка соотношения ширины низа к талии
        if hasattr(dimensions, 'hem_width') and hasattr(dimensions, 'waist_length'):
            hem_width = getattr(dimensions, 'hem_width', 0)
            waist_length = getattr(dimensions, 'waist_length', 0)
            
            if waist_length > 0:
                ratio = hem_width / waist_length
                # Идеальное соотношение: 1.2 - 2.0
                if 1.2 <= ratio <= 2.0:
                    scores.append(1.0)
                elif 1.0 <= ratio < 1.2:
                    # Немного узко, но приемлемо
                    scores.append(0.8)
                elif 2.0 < ratio <= 3.0:
                    # Немного широко, но приемлемо
                    scores.append(0.8)
                elif ratio < 1.0:
                    # Слишком узко
                    scores.append(0.3)
                else:
                    # Слишком широко
                    scores.append(0.3)
        
        # Оценка длины изделия
        if hasattr(dimensions, 'garment_length'):
            garment_length = getattr(dimensions, 'garment_length', 0)
            
            if garment_length > 0:
                # Разумная длина для юбки: 30 - 120 см
                if 30.0 <= garment_length <= 120.0:
                    scores.append(1.0)
                elif 20.0 <= garment_length < 30.0:
                    # Слишком коротко
                    scores.append(0.5)
                elif 120.0 < garment_length <= 150.0:
                    # Слишком длинно
                    scores.append(0.5)
                else:
                    # Экстремальная длина
                    scores.append(0.2)
        
        # Оценка абсолютных значений
        if hasattr(dimensions, 'waist_length'):
            waist_length = getattr(dimensions, 'waist_length', 0)
            
            if waist_length > 0:
                # Разумный обхват талии: 50 - 150 см
                if 50.0 <= waist_length <= 150.0:
                    scores.append(1.0)
                elif 40.0 <= waist_length < 50.0:
                    # Очень маленький размер
                    scores.append(0.7)
                elif 150.0 < waist_length <= 180.0:
                    # Очень большой размер
                    scores.append(0.7)
                else:
                    # Экстремальный размер
                    scores.append(0.3)
        
        if hasattr(dimensions, 'hem_width'):
            hem_width = getattr(dimensions, 'hem_width', 0)
            
            if hem_width > 0:
                # Разумная ширина низа: 60 - 200 см
                if 60.0 <= hem_width <= 200.0:
                    scores.append(1.0)
                elif 40.0 <= hem_width < 60.0:
                    # Очень узко
                    scores.append(0.7)
                elif 200.0 < hem_width <= 250.0:
                    # Очень широко
                    scores.append(0.7)
                else:
                    # Экстремальная ширина
                    scores.append(0.3)
        
        # Возвращаем среднюю оценку
        if scores:
            return sum(scores) / len(scores)
        else:
            return 1.0  # Нет данных для оценки
    
    @property
    def name(self) -> str:
        """Название компонента"""
        return "fit"
    
    @property
    def description(self) -> str:
        """Описание компонента"""
        return "Оценка посадки: пропорции, диапазоны размеров, соотношения"
