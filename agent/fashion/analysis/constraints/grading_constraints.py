"""
📐 GRADING CONSTRAINTS — ОГРАНИЧЕНИЯ ГРАДАЦИИ
============================================

🎯 Работают с grading.explain()

❌ НЕ читают геометрию
✅ Только правила градации
"""

from typing import List
from .base import BaseConstraint, ConstraintViolation


class GradingConstraints(BaseConstraint):
    """
    Ограничения градации
    
    📌 Проверяют корректность правил градации
    """
    
    def validate(self, pattern_model) -> List[ConstraintViolation]:
        """
        Валидировать ограничения градации
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            список нарушений ограничений
        """
        violations = []
        
        # Получаем правила градации
        grading = pattern_model.grading
        if grading is None:
            return violations
        
        # Используем explain() для получения данных
        try:
            grading_explain = grading.explain()
        except Exception:
            # Если explain() не работает, пропускаем
            return violations
        
        # Правило: нет UNKNOWN ролей
        rules = grading_explain.get("rules", {})
        for role in rules.keys():
            if "UNKNOWN" in role.upper():
                violations.append(ConstraintViolation(
                    type="grading",
                    rule="no UNKNOWN roles",
                    actual={"role": role},
                    severity="error",
                    message=f"Неизвестная роль в градации: {role}"
                ))
        
        # Правило: dx/dy не NaN
        for role, rule_data in rules.items():
            if isinstance(rule_data, dict):
                dx = rule_data.get("dx")
                dy = rule_data.get("dy")
                
                # Проверка dx
                if dx is None or (isinstance(dx, float) and (dx != dx)):  # NaN check
                    violations.append(ConstraintViolation(
                        type="grading",
                        rule=f"dx_{role} not NaN",
                        actual={"role": role, "dx": dx},
                        severity="error",
                        message=f"dx для {role} не должен быть NaN"
                    ))
                elif not isinstance(dx, (int, float)):
                    violations.append(ConstraintViolation(
                        type="grading",
                        rule=f"dx_{role} is number",
                        actual={"role": role, "dx": dx},
                        severity="error",
                        message=f"dx для {role} должен быть числом"
                    ))
                
                # Проверка dy
                if dy is None or (isinstance(dy, float) and (dy != dy)):  # NaN check
                    violations.append(ConstraintViolation(
                        type="grading",
                        rule=f"dy_{role} not NaN",
                        actual={"role": role, "dy": dy},
                        severity="error",
                        message=f"dy для {role} не должен быть NaN"
                    ))
                elif not isinstance(dy, (int, float)):
                    violations.append(ConstraintViolation(
                        type="grading",
                        rule=f"dy_{role} is number",
                        actual={"role": role, "dy": dy},
                        severity="error",
                        message=f"dy для {role} должен быть числом"
                    ))
        
        # Правило: правила не пустые при size_from ≠ size_to
        size_from = grading_explain.get("size_from")
        size_to = grading_explain.get("size_to")
        
        if size_from and size_to and size_from != size_to:
            if not rules:
                violations.append(ConstraintViolation(
                    type="grading",
                    rule="rules not empty when sizes differ",
                    actual={
                        "size_from": size_from,
                        "size_to": size_to,
                        "rules_count": len(rules)
                    },
                    severity="error",
                    message="При разных размерах должны быть правила градации"
                ))
        
        # Правило: разумные значения смещений
        for role, rule_data in rules.items():
            if isinstance(rule_data, dict):
                dx = rule_data.get("dx", 0)
                dy = rule_data.get("dy", 0)
                
                # Проверка на слишком большие значения
                if isinstance(dx, (int, float)) and abs(dx) > 100:
                    violations.append(ConstraintViolation(
                        type="grading",
                        rule=f"abs(dx_{role}) <= 100",
                        actual={"role": role, "dx": dx},
                        severity="warning",
                        message=f"Слишком большое смещение dx для {role}"
                    ))
                
                if isinstance(dy, (int, float)) and abs(dy) > 100:
                    violations.append(ConstraintViolation(
                        type="grading",
                        rule=f"abs(dy_{role}) <= 100",
                        actual={"role": role, "dy": dy},
                        severity="warning",
                        message=f"Слишком большое смещение dy для {role}"
                    ))
        
        # Правило: size_from и size_to должны быть строками
        if size_from and not isinstance(size_from, str):
            violations.append(ConstraintViolation(
                type="grading",
                rule="size_from is string",
                actual={"size_from": size_from},
                severity="error",
                message="size_from должен быть строкой"
            ))
        
        if size_to and not isinstance(size_to, str):
            violations.append(ConstraintViolation(
                type="grading",
                rule="size_to is string",
                actual={"size_to": size_to},
                severity="error",
                message="size_to должен быть строкой"
            ))
        
        # Правило: размеры не должны быть пустыми
        if not size_from or not size_from.strip():
            violations.append(ConstraintViolation(
                type="grading",
                rule="size_from not empty",
                actual={"size_from": size_from},
                severity="error",
                message="size_from не должен быть пустым"
            ))
        
        if not size_to or not size_to.strip():
            violations.append(ConstraintViolation(
                type="grading",
                rule="size_to not empty",
                actual={"size_to": size_to},
                severity="error",
                message="size_to не должен быть пустым"
            ))
        
        return violations
    
    @property
    def name(self) -> str:
        """Название ограничения"""
        return "grading_constraints"
    
    @property
    def description(self) -> str:
        """Описание ограничения"""
        return "Ограничения градации: проверка корректности правил градации"
