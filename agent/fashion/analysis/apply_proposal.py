"""
🔐 ФАЗА 6.0.3 — APPLY PROPOSAL (SAFE RULE APPLICATION)
========================================================

🎯 Механизм применения предложенных правил с валидацией безопасности

❗ НЕ трогает геометрию напрямую
❗ НЕ знает про CAD / DXF
❗ НЕ вызывает processors
✅ Применяет только декларативные изменения
✅ Возвращает новый PatternModel
✅ Полностью детерминирован
✅ Валидирует безопасность изменений
"""

from typing import Any, Union

# Импортируем TargetLibrary для гейтинга по путям
try:
    from .targets.library import TargetLibrary
    from .targets.spec import TargetSpec
except ImportError:
    # Если targets еще не импортированы, используем заглушки
    TargetLibrary = None
    TargetSpec = None


def apply_rule_proposal(pattern_model, proposal: dict) -> Any:
    """
    Применить предложенные изменения правил к PatternModel
    
    Args:
        pattern_model: исходная модель паттерна
        proposal: предложение изменений правил
        
    Returns:
        новый PatternModel с примененными изменениями
    """
    # Валидация предложения
    if not _validate_proposal(proposal):
        # При невалидном предложении возвращаем исходную модель
        return pattern_model
    
    # 7.0.2: поддержка target-предложений
    if proposal.get("type") == "target":
        # Для target-предложений просто возвращаем исходную модель
        # В реальной системе здесь была бы трансформация в rule changes
        # Но для демо просто возвращаем модель без изменений
        return pattern_model
    
    # Получаем текущие правила
    current_manufacturing = pattern_model.manufacturing
    current_grading = pattern_model.grading
    
    # Создаем копии правил для изменений
    new_manufacturing = _apply_manufacturing_changes(current_manufacturing, proposal)
    new_grading = _apply_grading_changes(current_grading, proposal)
    
    # Создаем новую модель с измененными правилами
    if new_manufacturing != current_manufacturing:
        pattern_model = pattern_model.with_manufacturing(new_manufacturing)
    
    if new_grading != current_grading:
        pattern_model = pattern_model.with_grading(new_grading)
    
    return pattern_model


def apply_proposal_with_target(pattern_model, proposal: dict, target: Union[dict, 'TargetSpec']) -> Any:
    """
    Применить предложение с гейтингом по разрешенным путям цели
    
    Args:
        pattern_model: исходная модель паттерна
        proposal: предложение изменений
        target: цель оптимизации (для гейтинга)
        
    Returns:
        новый PatternModel с примененными изменениями
    """
    try:
        # Гейтинг по разрешенным путям цели
        if TargetLibrary is not None and TargetSpec is not None:
            # Нормализуем цель
            if isinstance(target, dict):
                target = TargetLibrary.from_dict(target)
            
            # Получаем разрешенные пути
            allowed_paths = TargetLibrary.allowed_paths(target)
            
            # 7.0.2: поддержка target-предложений
            if proposal.get("type") == "target":
                # Для target-предложений просто применяем через apply_rule_proposal
                # который теперь поддерживает target-предложения
                return apply_rule_proposal(pattern_model, proposal)
            
            # Проверяем каждый путь в предложении
            for change in proposal.get("proposed_rule_changes", []):
                path = change.get("path")
                if path not in allowed_paths:
                    raise ValueError(f"proposal_path_not_allowed: {path}")
            
            # Все пути разрешены - применяем предложение
            return apply_rule_proposal(pattern_model, proposal)
        else:
            # Fallback если TargetLibrary недоступен
            return apply_rule_proposal(pattern_model, proposal)
    except Exception as e:
        # Если валидация не прошла, прокидываем ошибку
        raise ValueError(f"apply_proposal_with_target failed: {e}")


def _validate_proposal(proposal: dict) -> bool:
    """
    Валидировать предложение изменений
    
    Args:
        proposal: предложение изменений
        
    Returns:
        True если предложение валидно
    """
    if not isinstance(proposal, dict):
        return False
    
    # 7.0.2: поддержка target-предложений
    if proposal.get("type") == "target":
        # Для target-предложений проверяем базовые поля
        required_fields = ["goal", "role", "by"]
        for field in required_fields:
            if field not in proposal:
                return False
        return True
    
    changes = proposal.get("proposed_rule_changes", [])
    if not isinstance(changes, list):
        return False
    
    for change in changes:
        # Проверяем обязательные поля
        if not isinstance(change, dict):
            return False
        
        if "path" not in change or "from" not in change or "to" not in change:
            return False
        
        path = change["path"]
        if not isinstance(path, str) or not path.strip():
            return False
        
        # Проверяем на запрещенные изменения
        if _is_forbidden_change(path, change):
            return False
    
    return True


def _is_forbidden_change(path: str, change: dict) -> bool:
    """
    Проверить, является ли изменение запрещенным
    
    Args:
        path: путь правила
        change: изменение
        
    Returns:
        True если изменение запрещено
    """
    # Запрет отрицательных значений для припусков
    if path.startswith("manufacturing.seam_allowances."):
        new_value = change.get("to")
        if new_value is not None and (not isinstance(new_value, (int, float)) or new_value < 0):
            return True
    
    # Запрет отрицательных значений для надсечек
    if path.startswith("manufacturing.notches."):
        new_value = change.get("to")
        if new_value is not None and (not isinstance(new_value, int) or new_value < 0):
            return True
    
    # Запрет UNKNOWN-ролей
    if "UNKNOWN" in path.upper():
        return True
    
    # Запрет изменения size_from / size_to
    if path in ["grading.size_from", "grading.size_to"]:
        return True
    
    # Запрет изменения grainline region на None
    if path == "manufacturing.grainline":
        new_value = change.get("to")
        if new_value is None or (isinstance(new_value, str) and not new_value.strip()):
            return True
    
    return False


def _apply_manufacturing_changes(manufacturing, proposal: dict) -> Any:
    """
    Применить изменения к PatternManufacturing
    
    Args:
        manufacturing: текущие производственные правила
        proposal: предложение изменений
        
    Returns:
        новые производственные правила
    """
    if manufacturing is None:
        return manufacturing
    
    # Создаем копию правил
    new_seam_allowances = dict(manufacturing.seam_allowances or {})
    new_notches = dict(manufacturing.notches or {})
    new_grainline = manufacturing.grainline
    
    # Применяем изменения
    for change in proposal.get("proposed_rule_changes", []):
        path = change["path"]
        new_value = change["to"]
        
        if path.startswith("manufacturing.seam_allowances."):
            role = path.replace("manufacturing.seam_allowances.", "")
            new_seam_allowances[role] = new_value
        
        elif path.startswith("manufacturing.notches."):
            role = path.replace("manufacturing.notches.", "")
            new_notches[role] = new_value
        
        elif path == "manufacturing.grainline":
            new_grainline = new_value
    
    # Создаем новые производственные правила
    # Используем тот же конструктор, что и в оригинале
    return type(manufacturing)(
        seam_allowances=new_seam_allowances,
        notches=new_notches,
        grainline=new_grainline,
        stitch_lines=manufacturing.stitch_lines,
        drill_holes=manufacturing.drill_holes
    )


def _apply_grading_changes(grading, proposal: dict) -> Any:
    """
    Применить изменения к PatternGrading
    
    Args:
        grading: текущие правила градации
        proposal: предложение изменений
        
    Returns:
        новые правила градации
    """
    if grading is None:
        return grading
    
    # Создаем копию правил
    new_point_rules = dict(grading.point_rules or {})
    
    # Применяем изменения
    for change in proposal.get("proposed_rule_changes", []):
        path = change["path"]
        new_value = change["to"]
        
        if path.startswith("grading.rules."):
            role = path.replace("grading.rules.", "")
            if isinstance(new_value, dict) and "dx" in new_value and "dy" in new_value:
                new_point_rules[role] = (new_value["dx"], new_value["dy"])
    
    # Создаем новые правила градации
    return type(grading)(
        size_from=grading.size_from,
        size_to=grading.size_to,
        point_rules=new_point_rules
    )


import logging
logger = logging.getLogger(__name__)

logger.debug("ApplyProposal loaded")
logger.debug("Deteministic application")
