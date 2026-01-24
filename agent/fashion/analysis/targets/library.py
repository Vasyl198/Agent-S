"""
📚 TARGET LIBRARY — ФАБРИКА И НОРМАЛИЗАЦИЯ ЦЕЛЕЙ
=================================================

🎯 TargetLibrary — фабрика + нормализация целей

❌ НЕ импортирует cad_core/derived
✅ Только данные и валидация
"""

from typing import Dict, Any, List, Union
try:
    from .spec import TargetSpec
except ImportError:
    TargetSpec = None
try:
    from .mappings import (
        get_allowed_roles_for_goal,
        get_path_template_for_goal,
        get_value_type_for_goal,
        get_value_range_for_goal,
        is_goal_valid,
        is_role_valid_for_goal,
        generate_path_for_goal
    )
except ImportError:
    # Fallback функции если mappings недоступен
    def get_allowed_roles_for_goal(goal): return set()
    def get_path_template_for_goal(goal): return ""
    def get_value_type_for_goal(goal): return "float"
    def get_value_range_for_goal(goal): return (0.0, 100.0)
    def is_goal_valid(goal): return False
    def is_role_valid_for_goal(goal, role): return False
    def generate_path_for_goal(goal, role): return ""


class TargetLibrary:
    """
    Библиотека целей оптимизации
    
    📌 Фабрика + нормализация + валидация
    """
    
    @staticmethod
    def from_dict(target_dict: Dict[str, Any]) -> TargetSpec:
        """
        Создать TargetSpec из словаря
        
        Args:
            target_dict: словарное представление цели
            
        Returns:
            нормализованная спецификация цели
            
        Raises:
            ValueError: если цель невалидна
        """
        # Извлекаем базовые поля
        goal = target_dict.get("goal")
        role = target_dict.get("role")
        by = target_dict.get("by")
        mode = target_dict.get("mode", "delta")
        constraints = target_dict.get("constraints", {})
        
        # Валидация базовых полей
        if not goal:
            raise ValueError("Goal is required")
        
        if not role:
            raise ValueError("Role is required")
        
        if by is None:
            raise ValueError("By value is required")
        
        # Нормализация
        normalized_goal = TargetLibrary._normalize_goal(goal)
        normalized_role = TargetLibrary._normalize_role(role)
        normalized_by = TargetLibrary._normalize_by(by, normalized_goal)
        normalized_mode = TargetLibrary._normalize_mode(mode)
        normalized_constraints = TargetLibrary._normalize_constraints(constraints, normalized_goal)
        
        return TargetSpec(
            goal=normalized_goal,
            role=normalized_role,
            by=normalized_by,
            mode=normalized_mode,
            constraints=normalized_constraints
        )
    
    @staticmethod
    def allowed_paths(target_spec: TargetSpec) -> List[str]:
        """
        Получить разрешенные пути для цели
        
        Args:
            target_spec: спецификация цели
            
        Returns:
            список разрешенных путей
            
        Raises:
            ValueError: если цель невалидна
        """
        # Генерируем путь для роли
        path = generate_path_for_goal(target_spec.goal, target_spec.role)
        return [path]
    
    @staticmethod
    def normalize(target_spec: TargetSpec) -> TargetSpec:
        """
        Нормализовать спецификацию цели
        
        Args:
            target_spec: исходная спецификация
            
        Returns:
            нормализованная спецификация
        """
        normalized_by = TargetLibrary._normalize_by(target_spec.by, target_spec.goal)
        normalized_role = TargetLibrary._normalize_role(target_spec.role)
        normalized_constraints = TargetLibrary._normalize_constraints(
            target_spec.constraints, target_spec.goal
        )
        
        return TargetSpec(
            goal=target_spec.goal,
            role=normalized_role,
            by=normalized_by,
            mode=target_spec.mode,
            constraints=normalized_constraints
        )
    
    @staticmethod
    def validate_roles(target_spec: TargetSpec) -> None:
        """
        Валидировать роль для цели
        
        Args:
            target_spec: спецификация цели
            
        Raises:
            ValueError: если роль невалидна
        """
        if not is_role_valid_for_goal(target_spec.goal, target_spec.role):
            allowed_roles = get_allowed_roles_for_goal(target_spec.goal)
            raise ValueError(
                f"Role '{target_spec.role}' not allowed for goal '{target_spec.goal}'. "
                f"Allowed roles: {sorted(allowed_roles)}"
            )
    
    @staticmethod
    def validate_goal(goal: str) -> None:
        """
        Валидировать цель
        
        Args:
            goal: цель оптимизации
            
        Raises:
            ValueError: если цель невалидна
        """
        if not is_goal_valid(goal):
            available_goals = list(get_allowed_roles_for_goal.__self__.keys())
            raise ValueError(
                f"Unknown goal '{goal}'. Available goals: {available_goals}"
            )
    
    @staticmethod
    def validate_value_range(target_spec: TargetSpec) -> None:
        """
        Валидировать диапазон значения
        
        Args:
            target_spec: спецификация цели
            
        Raises:
            ValueError: если значение вне диапазона
        """
        min_val, max_val = get_value_range_for_goal(target_spec.goal)
        
        if target_spec.by < min_val or target_spec.by > max_val:
            raise ValueError(
                f"Value {target_spec.by} out of range [{min_val}, {max_val}] "
                f"for goal '{target_spec.goal}'"
            )
    
    @staticmethod
    def validate_value_type(target_spec: TargetSpec) -> None:
        """
        Валидировать тип значения
        
        Args:
            target_spec: спецификация цели
            
        Raises:
            ValueError: если тип значения неверный
        """
        expected_type = get_value_type_for_goal(target_spec.goal)
        
        if expected_type == "int" and not isinstance(target_spec.by, int):
            raise ValueError(
                f"Goal '{target_spec.goal}' requires integer value, got {type(target_spec.by)}"
            )
        
        if expected_type == "float" and not isinstance(target_spec.by, (int, float)):
            raise ValueError(
                f"Goal '{target_spec.goal}' requires float value, got {type(target_spec.by)}"
            )
    
    @staticmethod
    def full_validate(target_spec: TargetSpec) -> None:
        """
        Полная валидация спецификации
        
        Args:
            target_spec: спецификация цели
            
        Raises:
            ValueError: если спецификация невалидна
        """
        # Валидация цели
        TargetLibrary.validate_goal(target_spec.goal)
        
        # Валидация роли
        TargetLibrary.validate_roles(target_spec)
        
        # Валидация типа значения
        TargetLibrary.validate_value_type(target_spec)
        
        # Валидация диапазона значения
        TargetLibrary.validate_value_range(target_spec)
    
    @staticmethod
    def _normalize_goal(goal: str) -> str:
        """
        Нормализовать цель
        
        Args:
            goal: исходная цель
            
        Returns:
            нормализованная цель
        """
        if not isinstance(goal, str):
            raise ValueError(f"Goal must be string, got {type(goal)}")
        
        return goal.strip().upper()
    
    @staticmethod
    def _normalize_role(role: str) -> str:
        """
        Нормализовать роль
        
        Args:
            role: исходная роль
            
        Returns:
            нормализованная роль
        """
        if not isinstance(role, str):
            raise ValueError(f"Role must be string, got {type(role)}")
        
        return role.strip().upper()
    
    @staticmethod
    def _normalize_by(by: Union[int, float], goal: str) -> Union[int, float]:
        """
        Нормализовать величину
        
        Args:
            by: исходная величина
            goal: цель (для определения типа)
            
        Returns:
            нормализованная величина
        """
        expected_type = get_value_type_for_goal(goal)
        
        if expected_type == "int":
            return int(float(by))
        else:
            return float(by)
    
    @staticmethod
    def _normalize_mode(mode: str) -> str:
        """
        Нормализовать режим
        
        Args:
            mode: исходный режим
            
        Returns:
            нормализованный режим
        """
        if not isinstance(mode, str):
            raise ValueError(f"Mode must be string, got {type(mode)}")
        
        normalized = mode.strip().lower()
        if normalized != "delta":
            raise ValueError(f"Only 'delta' mode is supported, got '{mode}'")
        
        return "delta"
    
    @staticmethod
    def _normalize_constraints(constraints: Dict[str, Any], goal: str) -> Dict[str, Any]:
        """
        Нормализовать ограничения
        
        Args:
            constraints: исходные ограничения
            goal: цель
            
        Returns:
            нормализованные ограничения
        """
        if not isinstance(constraints, dict):
            raise ValueError(f"Constraints must be dict, got {type(constraints)}")
        
        normalized = {}
        
        # Нормализуем min/max
        for key in ["min", "max"]:
            if key in constraints:
                value = constraints[key]
                if isinstance(value, (int, float)):
                    normalized[key] = float(value)
                else:
                    raise ValueError(f"Constraint '{key}' must be number, got {type(value)}")
        
        # Нормализуем флаги
        for key in ["allow_negative", "allow_zero"]:
            if key in constraints:
                value = constraints[key]
                if isinstance(value, bool):
                    normalized[key] = value
                else:
                    raise ValueError(f"Constraint '{key}' must be boolean, got {type(value)}")
        
        return normalized
    
    @staticmethod
    def create_seam_allowance_target(role: str, by: float, increase: bool = False) -> TargetSpec:
        """
        Создать цель для припуска на шве
        
        Args:
            role: роль шва
            by: величина изменения
            increase: True для увеличения, False для уменьшения
            
        Returns:
            спецификация цели
        """
        goal = "increase_seam_allowance" if increase else "reduce_seam_allowance"
        
        return TargetSpec(
            goal=goal,
            role=role,
            by=abs(by),
            mode="delta"
        )
    
    @staticmethod
    def create_notch_target(role: str, by: int, increase: bool = False) -> TargetSpec:
        """
        Создать цель для надсечек
        
        Args:
            role: роль надсечки
            by: величина изменения
            increase: True для увеличения, False для уменьшения
            
        Returns:
            спецификация цели
        """
        goal = "increase_notches" if increase else "reduce_notches"
        
        return TargetSpec(
            goal=goal,
            role=role,
            by=int(abs(by)),
            mode="delta"
        )
    
    @staticmethod
    def create_grading_target(role: str, dx: float = 0.0, dy: float = 0.0) -> TargetSpec:
        """
        Создать цель для градации
        
        Args:
            role: роль точки
            dx: изменение по X
            dy: изменение по Y
            
        Returns:
            спецификация цели
        """
        # Если оба изменения нулевые, создаем цель для dx
        if dx != 0.0:
            return TargetSpec(
                goal="change_grading_dx",
                role=role,
                by=dx,
                mode="delta"
            )
        elif dy != 0.0:
            return TargetSpec(
                goal="change_grading_dy",
                role=role,
                by=dy,
                mode="delta"
            )
        else:
            raise ValueError("At least one of dx or dy must be non-zero")


import logging
logger = logging.getLogger(__name__)

logger.debug("TargetLibrary loaded")
