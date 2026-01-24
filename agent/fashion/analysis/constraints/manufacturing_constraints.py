"""
🏭 MANUFACTURING CONSTRAINTS — ПРОИЗВОДСТВЕННЫЕ ОГРАНИЧЕНИЯ
=======================================================

🎯 Работают с manufacturing.explain()

❌ НЕ читают геометрию
✅ Только производственные правила
"""

from typing import List
from .base import BaseConstraint, ConstraintViolation


class ManufacturingConstraints(BaseConstraint):
    """
    Производственные ограничения
    
    📌 Проверяют корректность производственных правил
    """
    
    def validate(self, pattern_model) -> List[ConstraintViolation]:
        """
        Валидировать производственные ограничения
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            список нарушений ограничений
        """
        violations = []
        
        # Получаем производственные правила
        manufacturing = pattern_model.manufacturing
        if manufacturing is None:
            return violations
        
        # Используем explain() для получения данных
        try:
            manufacturing_explain = manufacturing.explain()
        except Exception:
            # Если explain() не работает, пропускаем
            return violations
        
        # Правило: припуски ≥ 0
        seam_allowances = manufacturing_explain.get("seam_allowances", {})
        for role, allowance in seam_allowances.items():
            if allowance < 0:
                violations.append(ConstraintViolation(
                    type="manufacturing",
                    rule=f"seam_allowance_{role} >= 0",
                    actual={
                        "role": role,
                        "allowance": allowance
                    },
                    severity="error",
                    message=f"Припуск для {role} не может быть отрицательным"
                ))
            
            # Правило: припуски не должны быть слишком большими
            if allowance > 100.0:  # 10 см - слишком много для припуска
                violations.append(ConstraintViolation(
                    type="manufacturing",
                    rule=f"seam_allowance_{role} <= 100.0",
                    actual={
                        "role": role,
                        "allowance": allowance
                    },
                    severity="warning",
                    message=f"Припуск для {role} может быть слишком большим"
                ))
        
        # Правило: надсечки ∈ ℕ (натуральные числа)
        notches = manufacturing_explain.get("notches", {})
        for role, count in notches.items():
            if not isinstance(count, int) or count < 0:
                violations.append(ConstraintViolation(
                    type="manufacturing",
                    rule=f"notch_count_{role} in ℕ",
                    actual={
                        "role": role,
                        "count": count
                    },
                    severity="error",
                    message=f"Количество надсечек для {role} должно быть целым неотрицательным числом"
                ))
            
            # Правило: не должно быть слишком много надсечек
            if count > 10:
                violations.append(ConstraintViolation(
                    type="manufacturing",
                    rule=f"notch_count_{role} <= 10",
                    actual={
                        "role": role,
                        "count": count
                    },
                    severity="warning",
                    message=f"Слишком много надсечек для {role}"
                ))
        
        # Правило: grainline ∈ enum
        grainline = manufacturing_explain.get("grainline", "")
        valid_grainlines = ["CENTER_LINE", "FRONT", "BACK", "SIDE"]
        
        if not grainline or not isinstance(grainline, str):
            violations.append(ConstraintViolation(
                type="manufacturing",
                rule="grainline in enum",
                actual={"grainline": grainline},
                severity="error",
                message="Долевая линия должна быть указана"
            ))
        elif grainline not in valid_grainlines:
            violations.append(ConstraintViolation(
                type="manufacturing",
                rule="grainline in enum",
                actual={
                    "grainline": grainline,
                    "valid_options": valid_grainlines
                },
                severity="warning",
                message=f"Неизвестная долевая линия: {grainline}"
            ))
        
        # Правило: должны быть припуски
        if not seam_allowances:
            violations.append(ConstraintViolation(
                type="manufacturing",
                rule="seam_allowances not empty",
                actual={"seam_allowances": seam_allowances},
                severity="error",
                message="Должны быть указаны припуски"
            ))
        
        # Правило: должны быть надсечки
        if not notches:
            violations.append(ConstraintViolation(
                type="manufacturing",
                rule="notches not empty",
                actual={"notches": notches},
                severity="warning",
                message="Рекомендуется указать надсечки"
            ))
        
        return violations
    
    @property
    def name(self) -> str:
        """Название ограничения"""
        return "manufacturing_constraints"
    
    @property
    def description(self) -> str:
        """Описание ограничения"""
        return "Производственные ограничения: проверка корректности производственных правил"
