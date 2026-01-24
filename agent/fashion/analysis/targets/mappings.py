"""
🗺️ TARGET PATH MAPPINGS — КАРТА ЦЕЛЕЙ В ПУТИ ПРАВИЛ
===================================================

🎯 Строгая карта "цель → какие rule paths трогаем"

❌ НЕ импортирует cad_core/derived
✅ Только данные и валидация
"""

from typing import Dict, List, Set, Any


# Белые списки ролей по типам
SEAM_ROLES = {
    "HEM", "WAIST", "SIDE", "CENTER", "FRONT_CENTER", "BACK_CENTER",
    "FRONT_SIDE", "BACK_SIDE", "SHOULDER", "ARMHOLE", "NECK"
}

NOTCH_ROLES = {
    "WAIST_CENTER", "WAIST_SIDE", "HIP_SIDE", "HEM_SIDE", "HEM_CENTER",
    "FRONT_CENTER", "BACK_CENTER", "SHOULDER_TIP", "ARMHOLE", "NECK_CENTER"
}

POINT_ROLES = {
    "WAIST_SIDE", "HIP_SIDE", "HEM_CENTER", "HEM_SIDE", "WAIST_CENTER",
    "FRONT_CENTER", "BACK_CENTER", "SHOULDER_TIP", "ARMHOLE", "NECK_CENTER",
    "BUST_POINT", "SHOULDER_END", "HIP_CENTER"
}

# Карта целей в пути правил
TARGET_PATH_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "reduce_seam_allowance": {
        "path_template": "manufacturing.seam_allowances.{role}",
        "allowed_roles": SEAM_ROLES,
        "value_type": "float",
        "min_value": 0.0,
        "max_value": 50.0,
        "description": "Уменьшить припуск на шве"
    },
    
    "increase_seam_allowance": {
        "path_template": "manufacturing.seam_allowances.{role}",
        "allowed_roles": SEAM_ROLES,
        "value_type": "float",
        "min_value": 0.0,
        "max_value": 50.0,
        "description": "Увеличить припуск на шве"
    },
    
    "reduce_notches": {
        "path_template": "manufacturing.notches.{role}",
        "allowed_roles": NOTCH_ROLES,
        "value_type": "int",
        "min_value": 0,
        "max_value": 10,
        "description": "Уменьшить количество надсечек"
    },
    
    "increase_notches": {
        "path_template": "manufacturing.notches.{role}",
        "allowed_roles": NOTCH_ROLES,
        "value_type": "int",
        "min_value": 0,
        "max_value": 10,
        "description": "Увеличить количество надсечек"
    },
    
    "change_notch_count": {
        "path_template": "manufacturing.notches.{role}",
        "allowed_roles": NOTCH_ROLES,
        "value_type": "int",
        "min_value": 0,
        "max_value": 10,
        "description": "Изменить количество надсечек"
    },
    
    "grading_expand": {
        "path_template": "grading.rules.{role}",
        "allowed_roles": POINT_ROLES,
        "value_type": "float",
        "min_value": -50.0,
        "max_value": 50.0,
        "description": "Расширить градацию"
    },
    
    "grading_shrink": {
        "path_template": "grading.rules.{role}",
        "allowed_roles": POINT_ROLES,
        "value_type": "float",
        "min_value": -50.0,
        "max_value": 50.0,
        "description": "Сузить градацию"
    },
    
    "change_grading_dx": {
        "path_template": "grading.rules.{role}.dx",
        "allowed_roles": POINT_ROLES,
        "value_type": "float",
        "min_value": -50.0,
        "max_value": 50.0,
        "description": "Изменить градацию по X"
    },
    
    "change_grading_dy": {
        "path_template": "grading.rules.{role}.dy",
        "allowed_roles": POINT_ROLES,
        "value_type": "float",
        "min_value": -50.0,
        "max_value": 50.0,
        "description": "Изменить градацию по Y"
    }
}


def get_allowed_roles_for_goal(goal: str) -> Set[str]:
    """
    Получить разрешенные роли для цели
    
    Args:
        goal: цель оптимизации
        
    Returns:
        множество разрешенных ролей
        
    Raises:
        ValueError: если цель неизвестна
    """
    if goal not in TARGET_PATH_MAPPINGS:
        raise ValueError(f"Unknown goal: {goal}")
    
    return TARGET_PATH_MAPPINGS[goal]["allowed_roles"]


def get_path_template_for_goal(goal: str) -> str:
    """
    Получить шаблон пути для цели
    
    Args:
        goal: цель оптимизации
        
    Returns:
        шаблон пути
        
    Raises:
        ValueError: если цель неизвестна
    """
    if goal not in TARGET_PATH_MAPPINGS:
        raise ValueError(f"Unknown goal: {goal}")
    
    return TARGET_PATH_MAPPINGS[goal]["path_template"]


def get_value_type_for_goal(goal: str) -> str:
    """
    Получить тип значения для цели
    
    Args:
        goal: цель оптимизации
        
    Returns:
        тип значения
        
    Raises:
        ValueError: если цель неизвестна
    """
    if goal not in TARGET_PATH_MAPPINGS:
        raise ValueError(f"Unknown goal: {goal}")
    
    return TARGET_PATH_MAPPINGS[goal]["value_type"]


def get_value_range_for_goal(goal: str) -> tuple:
    """
    Получить диапазон значений для цели
    
    Args:
        goal: цель оптимизации
        
    Returns:
        кортеж (min_value, max_value)
        
    Raises:
        ValueError: если цель неизвестна
    """
    if goal not in TARGET_PATH_MAPPINGS:
        raise ValueError(f"Unknown goal: {goal}")
    
    mapping = TARGET_PATH_MAPPINGS[goal]
    return mapping["min_value"], mapping["max_value"]


def get_description_for_goal(goal: str) -> str:
    """
    Получить описание цели
    
    Args:
        goal: цель оптимизации
        
    Returns:
        описание цели
        
    Raises:
        ValueError: если цель неизвестна
    """
    if goal not in TARGET_PATH_MAPPINGS:
        raise ValueError(f"Unknown goal: {goal}")
    
    return TARGET_PATH_MAPPINGS[goal]["description"]


def generate_path_for_goal(goal: str, role: str) -> str:
    """
    Сгенерировать путь правила для цели и роли
    
    Args:
        goal: цель оптимизации
        role: роль
        
    Returns:
        путь правила
        
    Raises:
        ValueError: если цель или роль неизвестны
    """
    # Проверяем цель
    if goal not in TARGET_PATH_MAPPINGS:
        raise ValueError(f"Unknown goal: {goal}")
    
    # Проверяем роль
    allowed_roles = get_allowed_roles_for_goal(goal)
    if role not in allowed_roles:
        raise ValueError(f"Role '{role}' not allowed for goal '{goal}'. Allowed roles: {allowed_roles}")
    
    # Генерируем путь
    template = get_path_template_for_goal(goal)
    return template.format(role=role)


def is_goal_valid(goal: str) -> bool:
    """
    Проверить, что цель известна
    
    Args:
        goal: цель оптимизации
        
    Returns:
        True если цель известна
    """
    return goal in TARGET_PATH_MAPPINGS


def is_role_valid_for_goal(goal: str, role: str) -> bool:
    """
    Проверить, что роль разрешена для цели
    
    Args:
        goal: цель оптимизации
        role: роль
        
    Returns:
        True если роль разрешена
    """
    if not is_goal_valid(goal):
        return False
    
    allowed_roles = get_allowed_roles_for_goal(goal)
    return role in allowed_roles


def get_all_goals() -> List[str]:
    """
    Получить список всех известных целей
    
    Returns:
        список целей
    """
    return list(TARGET_PATH_MAPPINGS.keys())


def get_all_seam_roles() -> Set[str]:
    """Получить все шовные роли"""
    return SEAM_ROLES.copy()


def get_all_notch_roles() -> Set[str]:
    """Получить все роли надсечек"""
    return NOTCH_ROLES.copy()


def get_all_point_roles() -> Set[str]:
    """Получить все точечные роли"""
    return POINT_ROLES.copy()


import logging
logger = logging.getLogger(__name__)

logger.debug("TargetPathMappings loaded")
