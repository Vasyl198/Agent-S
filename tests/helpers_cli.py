# tests/helpers_cli.py
import json
import subprocess
import sys
from typing import Any, Dict, Tuple


def run_dataset_report(args: list[str], expect_error: bool = False) -> Tuple[Dict[str, Any], int] | int:
    """
    Запускает dataset_report и возвращает JSON + exit code.
    
    Args:
        args: Список аргументов CLI (без имени программы)
        expect_error: Если True, ожидает ошибку и возвращает только exit code
        
    Returns:
        Если expect_error=False: (stdout_json: dict, exit_code: int)
        Если expect_error=True: exit_code: int
    """
    cmd = [sys.executable, "-m", "agent.fashion.ml.dataset_report"] + args
    
    # Добавляем --stdout если его нет и не ожидаем ошибку, чтобы получить JSON
    if not expect_error and "--stdout" not in args:
        args = args + ["--stdout"]
        cmd = [sys.executable, "-m", "agent.fashion.ml.dataset_report"] + args
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if expect_error:
        return result.returncode
    
    try:
        stdout_json = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse stdout as JSON: {e}\nstdout: {result.stdout}\nstderr: {result.stderr}")
    
    return stdout_json, result.returncode


def assert_has_path(obj: Dict[str, Any], path: str) -> Any:
    """
    Проверяет что путь существует в объекте и возвращает значение.
    
    Args:
        obj: Объект для проверки
        path: Путь в формате "a.b.c"
        
    Returns:
        Значение по пути
        
    Raises:
        AssertionError: если путь не существует
    """
    keys = path.split(".")
    current = obj
    
    for key in keys:
        assert isinstance(current, dict), f"Expected dict at '{'.'.join(keys[:keys.index(key)])}', got {type(current)}"
        assert key in current, f"Missing key '{key}' in path '{path}'"
        current = current[key]
    
    return current


def assert_type(value: Any, expected_type: type, path: str) -> None:
    """
    Проверяет тип значения с учетом None для опциональных полей.
    
    Args:
        value: Значение для проверки
        expected_type: Ожидаемый тип
        path: Путь для сообщения об ошибке
    """
    if value is None:
        return  # None допускается для опциональных полей
    
    assert isinstance(value, expected_type), f"Expected {expected_type.__name__} at '{path}', got {type(value).__name__}"


def assert_schema_structure(obj: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> None:
    """
    Рекурсивно проверяет структуру объекта по схеме.
    
    Args:
        obj: Объект для проверки
        schema: Схема (dict с типами или вложенными схемами)
        path: Текущий путь (рекурсия)
    """
    for key, expected_type in schema.items():
        current_path = f"{path}.{key}" if path else key
        
        # Ключ должен присутствовать, даже если значение может быть None
        assert key in obj, f"Missing key '{current_path}'"
        value = obj[key]
        
        if isinstance(expected_type, dict):
            assert isinstance(value, dict), f"Expected dict at '{current_path}', got {type(value).__name__}"
            assert_schema_structure(value, expected_type, current_path)
        else:
            assert_type(value, expected_type, current_path)
