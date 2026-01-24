"""
🧠 ФАЗА 6.0.1 — RULE DIFF (АНАЛИЗ ИЗМЕНЕНИЙ ПРАВИЛ)
========================================================

🎯 Модуль для анализа изменений в explain-графах.

❗ НЕ анализирует геометрию
❗ НЕ импортирует CAD Core
❗ Только правила → intent → explain
"""

from typing import Dict, Any


def diff_explain(a: dict, b: dict) -> dict:
    """
    Сравнить два explain-графа и найти изменения в правилах
    
    Args:
        a: первый explain-граф (старая версия)
        b: второй explain-граф (новая версия)
        
    Returns:
        словарь с изменениями правил и затронутой производной геометрией
    """
    result = {
        "changed_rules": [],
        "affected_derived": []
    }
    
    # Получаем правила из обеих версий
    a_rules = _extract_rules(a)
    b_rules = _extract_rules(b)
    
    # Находим измененные правила
    for path, value in b_rules.items():
        if path in a_rules:
            old_value = a_rules[path]
            if old_value != value:
                result["changed_rules"].append({
                    "path": path,
                    "from": old_value,
                    "to": value
                })
        else:
            # Новое правило
            result["changed_rules"].append({
                "path": path,
                "from": None,
                "to": value
            })
    
    # Находим удаленные правила
    for path, value in a_rules.items():
        if path not in b_rules:
            result["changed_rules"].append({
                "path": path,
                "from": value,
                "to": None
            })
    
    # Определяем затронутую производную геометрию через links
    affected_derived = set()
    
    # Из новой версии берем links
    links = b.get("links", [])
    for link in links:
        from_path = link.get("from", "")
        to_path = link.get("to", "")
        
        # Если источник правила изменился
        for change in result["changed_rules"]:
            if change["path"] == from_path:
                affected_derived.add(to_path)
    
    result["affected_derived"] = sorted(list(affected_derived))
    
    return result


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


def _get_value_by_path(data: dict, path: str) -> Any:
    """
    Получить значение по пути в словаре
    
    Args:
        data: словарь
        path: путь вида "manufacturing.seam_allowances.HEM"
        
    Returns:
        значение или None
    """
    parts = path.split(".")
    current = data
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    
    return current


import logging
logger = logging.getLogger(__name__)

logger.debug("RuleDiff loaded")
