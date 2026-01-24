"""
🧠 ФАЗА 6.0.2 — RULE PROPOSAL ENGINE
==========================================

🎯 Двигатель предложений правил: "Если цель изменилась — какие правила надо поменять?"

❗ НЕ трогает геометрию
❗ НЕ знает про DXF
❗ НЕ вызывает процессоры
✅ Работает только с explain-графом
✅ Предлагает изменения правил
✅ Объясняет почему именно эти правила
"""

from typing import Dict, List, Any, Union

# Импортируем TargetLibrary для стандартизации целей
try:
    from .targets.library import TargetLibrary
    from .targets.spec import TargetSpec
except ImportError:
    # Если targets еще не импортированы, используем заглушки
    TargetLibrary = None
    TargetSpec = None


def propose_rule_changes(
    explain_graph: dict,
    target: Union[TargetSpec, dict]
) -> dict:
    """
    Предложить изменения правил на основе цели
    
    Args:
        explain_graph: текущий explain-граф
        target: цель изменений (TargetSpec или dict)
        
    Returns:
        словарь с предложенными изменениями правил
    """
    result = {
        "proposed_rule_changes": [],
        "affected_derived": []
    }
    
    # Нормализуем цель в TargetSpec
    try:
        if TargetLibrary is not None and TargetSpec is not None:
            if isinstance(target, dict):
                # Преобразуем dict в TargetSpec
                target_spec = TargetLibrary.from_dict(target)
            else:
                # Уже TargetSpec
                target_spec = target
            
            # Полная валидация
            TargetLibrary.full_validate(target_spec)
            
            # Получаем разрешенные пути
            allowed_paths = TargetLibrary.allowed_paths(target_spec)
            
            # Генерируем предложения по разрешенным путям
            _generate_proposals_from_paths(explain_graph, target_spec, allowed_paths, result)
        else:
            # Fallback на старую логику если TargetLibrary недоступен
            _handle_legacy_target(explain_graph, target, result)
    except Exception as e:
        # Если валидация не прошла, возвращаем пустой результат
        # или можно вернуть ошибку в зависимости от требований
        result["error"] = str(e)
        return result
    
    # Определяем затронутую производную геометрию
    _determine_affected_derived(explain_graph, result)
    
    return result


def _generate_proposals_from_paths(
    explain_graph: dict,
    target_spec: 'TargetSpec',
    allowed_paths: List[str],
    result: dict
) -> None:
    """
    Генерировать предложения на основе разрешенных путей
    
    Args:
        explain_graph: explain-граф
        target_spec: стандартизированная цель
        allowed_paths: разрешенные пути
        result: результат для заполнения
    """
    # Получаем текущие правила
    current_rules = _extract_rules(explain_graph)
    
    for path in allowed_paths:
        current_value = current_rules.get(path)
        
        if current_value is None:
            continue
        
        # Применяем изменение в зависимости от цели
        new_value = _apply_target_to_value(current_value, target_spec)
        
        if new_value is None or new_value == current_value:
            continue
        
        # Валидируем новое значение
        if not _validate_new_value(new_value, target_spec):
            continue
        
        result["proposed_rule_changes"].append({
            "path": path,
            "from": current_value,
            "to": new_value,
            "reason": f"target.{target_spec.goal}.{target_spec.role}"
        })


def _apply_target_to_value(current_value: Any, target_spec: 'TargetSpec') -> Any:
    """
    Применить цель к текущему значению
    
    Args:
        current_value: текущее значение
        target_spec: стандартизированная цель
        
    Returns:
        новое значение или None если невозможно применить
    """
    goal = target_spec.goal
    by = target_spec.by
    
    try:
        if goal == "reduce_seam_allowance":
            return max(0.0, float(current_value) - by)
        elif goal == "increase_seam_allowance":
            return float(current_value) + by
        elif goal == "reduce_notches":
            return max(0, int(current_value) - by)
        elif goal == "increase_notches":
            return int(current_value) + by
        elif goal == "change_notch_count":
            return max(0, int(by))  # 'by' используется как новое значение
        elif goal == "change_grading_dx":
            # Для градации работаем с объектом
            if isinstance(current_value, dict):
                new_rule = dict(current_value)
                new_rule["dx"] = by
                return new_rule
        elif goal == "change_grading_dy":
            # Для градации работаем с объектом
            if isinstance(current_value, dict):
                new_rule = dict(current_value)
                new_rule["dy"] = by
                return new_rule
        elif goal == "grading_expand":
            # Расширение градации - увеличиваем оба значения
            if isinstance(current_value, dict):
                new_rule = dict(current_value)
                new_rule["dx"] = float(new_rule.get("dx", 0)) + by
                new_rule["dy"] = float(new_rule.get("dy", 0)) + by
                return new_rule
        elif goal == "grading_shrink":
            # Сужение градации - уменьшаем оба значения
            if isinstance(current_value, dict):
                new_rule = dict(current_value)
                new_rule["dx"] = float(new_rule.get("dx", 0)) - by
                new_rule["dy"] = float(new_rule.get("dy", 0)) - by
                return new_rule
    except (ValueError, TypeError):
        pass
    
    return None


def _validate_new_value(new_value: Any, target_spec: 'TargetSpec') -> bool:
    """
    Валидировать новое значение
    
    Args:
        new_value: новое значение
        target_spec: стандартизированная цель
        
    Returns:
        True если значение валидно
    """
    # Проверяем на отрицательные значения
    if isinstance(new_value, (int, float)) and new_value < 0:
        return False
    
    # Проверяем тип значения
    goal = target_spec.goal
    if goal in ["increase_notches", "reduce_notches", "change_notch_count"]:
        if not isinstance(new_value, int):
            return False
    elif goal in ["increase_seam_allowance", "reduce_seam_allowance"]:
        if not isinstance(new_value, (int, float)):
            return False
    
    return True


def _handle_legacy_target(
    explain_graph: dict,
    target: dict,
    result: dict
) -> None:
    """
    Обработать цель в старом формате (fallback)
    
    Args:
        explain_graph: explain-граф
        target: цель в старом формате
        result: результат для заполнения
    """
    # Получаем текущие правила
    current_rules = _extract_rules(explain_graph)
    
    # Анализируем цель
    target_type = target.get("type", "")
    goal = target.get("goal", "")
    
    if target_type != "target":
        return
    
    # Обрабатываем разные типы целей
    if goal == "reduce_seam_allowance":
        _handle_reduce_seam_allowance(current_rules, target, result)
    elif goal == "increase_seam_allowance":
        _handle_increase_seam_allowance(current_rules, target, result)
    elif goal == "change_notch_count":
        _handle_change_notch_count(current_rules, target, result)
    else:
        # Неизвестная цель
        return


def _handle_reduce_seam_allowance(
    current_rules: Dict[str, Any],
    target: dict,
    result: dict
) -> None:
    """
    Обработать цель уменьшения припуска
    
    Args:
        current_rules: текущие правила
        target: цель
        result: результат для заполнения
    """
    role = target.get("role", "")
    reduction = target.get("by", 0.0)
    
    if not role or reduction <= 0:
        return
    
    rule_path = f"manufacturing.seam_allowances.{role}"
    current_value = current_rules.get(rule_path)
    
    if current_value is None:
        return
    
    new_value = max(0.0, current_value - reduction)
    
    result["proposed_rule_changes"].append({
        "path": rule_path,
        "from": current_value,
        "to": new_value,
        "reason": f"target.reduce_seam_allowance.{role}"
    })


def _handle_increase_seam_allowance(
    current_rules: Dict[str, Any],
    target: dict,
    result: dict
) -> None:
    """
    Обработать цель увеличения припуска
    
    Args:
        current_rules: текущие правила
        target: цель
        result: результат для заполнения
    """
    role = target.get("role", "")
    increase = target.get("by", 0.0)
    
    if not role or increase <= 0:
        return
    
    rule_path = f"manufacturing.seam_allowances.{role}"
    current_value = current_rules.get(rule_path)
    
    if current_value is None:
        return
    
    new_value = current_value + increase
    
    result["proposed_rule_changes"].append({
        "path": rule_path,
        "from": current_value,
        "to": new_value,
        "reason": f"target.increase_seam_allowance.{role}"
    })


def _handle_change_notch_count(
    current_rules: Dict[str, Any],
    target: dict,
    result: dict
) -> None:
    """
    Обработать цель изменения количества надсечек
    
    Args:
        current_rules: текущие правила
        target: цель
        result: результат для заполнения
    """
    role = target.get("role", "")
    new_count = target.get("to", 0)
    
    if not role or new_count < 0:
        return
    
    rule_path = f"manufacturing.notches.{role}"
    current_value = current_rules.get(rule_path)
    
    if current_value is None:
        return
    
    result["proposed_rule_changes"].append({
        "path": rule_path,
        "from": current_value,
        "to": new_count,
        "reason": f"target.change_notch_count.{role}"
    })


def _determine_affected_derived(explain_graph: dict, result: dict) -> None:
    """
    Определить затронутую производную геометрию через links
    
    Args:
        explain_graph: explain-граф
        result: результат для заполнения
    """
    affected_derived = set()
    
    # Из explain-графа берем links
    links = explain_graph.get("links", [])
    
    for change in result["proposed_rule_changes"]:
        rule_path = change["path"]
        
        # Ищем связи для этого правила
        for link in links:
            from_path = link.get("from", "")
            to_path = link.get("to", "")
            
            if from_path == rule_path:
                affected_derived.add(to_path)
    
    result["affected_derived"] = sorted(list(affected_derived))


def _extract_rules(explain_graph: dict) -> Dict[str, Any]:
    """
    Извлечь все правила из explain-графа в плоский словарь
    
    Args:
        explain_graph: explain-граф
        
    Returns:
        плоский словарь правил path → value
    """
    rules = {}
    
    # Извлекаем правила из manufacturing
    manufacturing = explain_graph.get("intent", {}).get("manufacturing", {})
    
    # Припуски
    seam_allowances = manufacturing.get("seam_allowances", {})
    for role, value in seam_allowances.items():
        rules[f"manufacturing.seam_allowances.{role}"] = value
    
    # Надсечки
    notches = manufacturing.get("notches", {})
    for role, value in notches.items():
        rules[f"manufacturing.notches.{role}"] = value
    
    # Долевая линия
    grainline = manufacturing.get("grainline")
    if grainline is not None:
        rules["manufacturing.grainline"] = grainline
    
    # Извлекаем правила из grading
    grading = explain_graph.get("intent", {}).get("grading", {})
    
    # Правила градации
    grading_rules = grading.get("rules", {})
    for role, rule_data in grading_rules.items():
        # Для градации сохраняем как объект
        rules[f"grading.rules.{role}"] = rule_data
    
    return rules


import logging
logger = logging.getLogger(__name__)

logger.debug("RuleProposal Engine loaded")
logger.debug("Proposes changes to rules, not geometry")
logger.debug("Works only with explain-graphs")
logger.debug("Explains the reason for proposals")
