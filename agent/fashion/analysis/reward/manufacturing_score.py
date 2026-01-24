"""
🏭 MANUFACTURING SCORE — ОЦЕНКА ПРОИЗВОДСТВА
============================================

🎯 Использует manufacturing.explain() для оценки качества

❌ НЕ читает геометрию
✅ Только производственные правила
"""

from .base import WeightedRewardComponent


class ManufacturingScore(WeightedRewardComponent):
    """
    Оценка качества производственных правил
    
    📌 Основана на разумности значений и полноте правил
    """
    
    def __init__(self, weight: float = 1.0):
        """Инициализировать оценку производства"""
        super().__init__(weight)
    
    def evaluate(self, pattern_model, constraint_result=None) -> float:
        """
        Оценить PatternModel на основе производственных правил
        
        Args:
            pattern_model: модель паттерна
            constraint_result: результат валидации ограничений
            
        Returns:
            оценка в диапазоне [0.0, 1.0]
        """
        manufacturing = pattern_model.manufacturing
        if manufacturing is None:
            # Если нет производственных правил, оценка = 0.5 (нейтрально)
            return 0.5
        
        # Используем explain() для получения данных
        try:
            manufacturing_explain = manufacturing.explain()
        except Exception:
            # Если explain() не работает, оценка = 0.5
            return 0.5
        
        scores = []
        
        # Оценка припусков
        seam_allowances = manufacturing_explain.get("seam_allowances", {})
        if seam_allowances:
            allowance_scores = []
            
            for role, allowance in seam_allowances.items():
                # Разумные припуски: 5 - 30 мм
                if 5.0 <= allowance <= 30.0:
                    allowance_scores.append(1.0)
                elif 3.0 <= allowance < 5.0:
                    # Маленький припуск
                    allowance_scores.append(0.7)
                elif 30.0 < allowance <= 50.0:
                    # Большой припуск
                    allowance_scores.append(0.7)
                else:
                    # Экстремальный припуск
                    allowance_scores.append(0.3)
            
            if allowance_scores:
                scores.append(sum(allowance_scores) / len(allowance_scores))
        else:
            # Нет припусков - штраф
            scores.append(0.3)
        
        # Оценка надсечек
        notches = manufacturing_explain.get("notches", {})
        if notches:
            notch_scores = []
            
            for role, count in notches.items():
                # Разумное количество надсечек: 1 - 5
                if 1 <= count <= 5:
                    notch_scores.append(1.0)
                elif count == 0:
                    # Нет надсечек - небольшой штраф
                    notch_scores.append(0.8)
                elif 6 <= count <= 10:
                    # Много надсечек
                    notch_scores.append(0.6)
                else:
                    # Слишком много надсечек
                    notch_scores.append(0.3)
            
            if notch_scores:
                scores.append(sum(notch_scores) / len(notch_scores))
        else:
            # Нет надсечек - штраф
            scores.append(0.5)
        
        # Оценка долевой линии
        grainline = manufacturing_explain.get("grainline", "")
        if grainline:
            # Бонус за стандартные значения
            standard_grainlines = ["CENTER_LINE", "FRONT", "BACK", "SIDE"]
            if grainline in standard_grainlines:
                scores.append(1.0)
            else:
                # Нестандартная, но валидная grainline
                scores.append(0.8)
        else:
            # Нет grainline - штраф
            scores.append(0.3)
        
        # Оценка полноты правил
        completeness_score = 0.0
        
        # Есть припуски?
        if seam_allowances:
            completeness_score += 0.4
        
        # Есть надсечки?
        if notches:
            completeness_score += 0.3
        
        # Есть grainline?
        if grainline:
            completeness_score += 0.3
        
        scores.append(completeness_score)
        
        # Возвращаем среднюю оценку
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.5  # Нет данных для оценки
    
    @property
    def name(self) -> str:
        """Название компонента"""
        return "manufacturing"
    
    @property
    def description(self) -> str:
        """Описание компонента"""
        return "Оценка производства: разумность припусков, надсечек, полнота правил"
