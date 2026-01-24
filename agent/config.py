"""
Конфигурация проекта Universal Agent
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Добавляем корень проекта в Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Пути к директориям
AGENT_DIR = PROJECT_ROOT / "agent"
INTERFACES_DIR = PROJECT_ROOT / "interfaces"
MEMORY_DIR = PROJECT_ROOT / "memory"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"
FASHION_DATASET_DIR = PROJECT_ROOT / "fashion_dataset"  # Garment-Pattern-Generator Dataset

# Создаем директории если их нет
for directory in [MEMORY_DIR, LOGS_DIR, CONFIG_DIR]:
    directory.mkdir(exist_ok=True)

# Настройки по умолчанию
DEFAULT_CONFIG = {
    'model': 'llama3.2:3b',  # Быстрая и стабильная модель для генерации сайтов
    'temperature': 0.7,
    'max_tokens': 2048,
    'timeout': 60,  # Быстрый таймаут для стабильной модели
    'retries': 2,
    'memory_file': 'universal_agent_memory.json',
    'log_level': 'INFO',
    "ollama": {
        'model': 'llama3.2:3b',
        'timeout': 60,
        'retries': 2
    },
    "memory": {
        "persist_path": str(MEMORY_DIR / "agent_memory"),
        "max_entries": 1000,
        "embedding_dim": 384
    },
    "tools": {
        "tavily_timeout": 30,
        "code_execution_timeout": 120,
        "web_search_timeout": 15
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": str(LOGS_DIR / "agent.log")
    },
    "fashion": {
        "dataset_path": str(FASHION_DATASET_DIR),
        "dataset_index_path": str(PROJECT_ROOT / "fashion_dataset_index.faiss"),
        "dataset_metadata_path": str(PROJECT_ROOT / "fashion_dataset_metadata.pkl"),
        "embedding_model": "all-MiniLM-L6-v2",
        "max_dataset_patterns": 2000
    }
}

def setup_logging(level: str = "INFO", log_file: str = None):
    """Настраивает логирование для всего проекта"""
    import logging
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )

def load_config() -> Dict[str, Any]:
    """Загружает конфигурацию из файла или возвращает настройки по умолчанию"""
    config_file = CONFIG_DIR / "config.json"
    
    if config_file.exists():
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # Объединяем с настройками по умолчанию
            config = DEFAULT_CONFIG.copy()
            _deep_update(config, user_config)
            return config
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return DEFAULT_CONFIG
    
    return DEFAULT_CONFIG

def _deep_update(base_dict: dict, update_dict: dict):
    """Рекурсивно обновляет словарь"""
    for key, value in update_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            _deep_update(base_dict[key], value)
        else:
            base_dict[key] = value

def get_env_vars() -> Dict[str, str]:
    """Получает переменные окружения"""
    return {
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        "EMAIL_USERNAME": os.getenv("EMAIL_USERNAME", ""),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", ""),
    }

# Глобальная конфигурация
CONFIG = load_config()
ENV_VARS = get_env_vars()
