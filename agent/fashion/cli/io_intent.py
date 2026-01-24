# agent/fashion/cli/io_intent.py
# IO модуль для pattern_intent.json (stdlib only)

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_intent(path: Path) -> Dict[str, Any]:
    """
    Загрузить pattern intent из JSON файла.
    
    Args:
        path: путь к файлу pattern_intent.json
        
    Returns:
        нормализованный dict с полями meta, dimensions, grading, manufacturing, derived
        
    Raises:
        FileNotFoundError: если файл не существует
        json.JSONDecodeError: если файл не валидный JSON
    """
    if not path.exists():
        raise FileNotFoundError(f"Intent file not found: {path}")
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {path}: {e.msg}", e.doc, e.pos)
    
    return normalize_intent(data)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    """
    Сохранить данные в JSON файл.
    
    Args:
        path: путь для сохранения
        data: данные для сохранения
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_intent(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализовать intent данные:
    - Гарантирует наличие всех полей
    - Приводит типы чисел к float/int
    - Очищает от лишних полей
    
    Args:
        data: сырые данные из JSON
        
    Returns:
        нормализованный dict
    """
    normalized = {}
    
    # meta - обязательное поле
    meta = data.get("meta", {})
    if not isinstance(meta, dict):
        raise ValueError("meta field must be a dictionary")
    normalized["meta"] = meta
    
    # dimensions - опциональное поле
    dimensions = data.get("dimensions", {})
    if dimensions is None:
        dimensions = {}
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions field must be a dictionary or null")
    normalized["dimensions"] = _normalize_numbers(dimensions)
    
    # grading - опциональное поле
    grading = data.get("grading", {})
    if grading is None:
        grading = {}
    if not isinstance(grading, dict):
        raise ValueError("grading field must be a dictionary or null")
    normalized["grading"] = _normalize_numbers(grading)
    
    # manufacturing - опциональное поле
    manufacturing = data.get("manufacturing", {})
    if manufacturing is None:
        manufacturing = {}
    if not isinstance(manufacturing, dict):
        raise ValueError("manufacturing field must be a dictionary or null")
    normalized["manufacturing"] = _normalize_numbers(manufacturing)
    
    # derived - опциональное поле
    derived = data.get("derived", {})
    if derived is None:
        derived = {}
    if not isinstance(derived, dict):
        raise ValueError("derived field must be a dictionary or null")
    normalized["derived"] = _normalize_numbers(derived)
    
    return normalized


def _normalize_numbers(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Рекурсивно приводит числа к правильным типам.
    
    Args:
        data: данные для нормализации
        
    Returns:
        данные с приведенными типами
    """
    if isinstance(data, dict):
        return {k: _normalize_numbers(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_normalize_numbers(item) for item in data]
    elif isinstance(data, (int, float)):
        # Оставляем как есть - JSON уже правильно парсит числа
        return data
    elif isinstance(data, str):
        # Пытаемся конвертировать строки с числами
        try:
            if "." in data:
                return float(data)
            else:
                return int(data)
        except ValueError:
            return data
    else:
        return data


def create_sample_intent() -> Dict[str, Any]:
    """
    Создать пример pattern intent для демонстрации.
    
    Returns:
        пример структуры pattern_intent.json
    """
    return {
        "meta": {
            "name": "Skirt Front",
            "size": "M",
            "version": "v1.0",
            "author": "user"
        },
        "dimensions": {
            "waist_width": 70.0,
            "hip_width": 95.0,
            "length": 60.0
        },
        "grading": {
            "rules": {
                "WAIST": {"x": 0.5, "y": 0.0},
                "HIP": {"x": 0.7, "y": 0.0},
                "HEM": {"x": 0.7, "y": 0.0}
            }
        },
        "manufacturing": {
            "seam_allowance": {
                "WAIST": 1.5,
                "SIDE": 1.5,
                "HEM": 2.0
            },
            "notches": {
                "WAIST": 2,
                "SIDE": 1
            }
        },
        "derived": {}
    }
