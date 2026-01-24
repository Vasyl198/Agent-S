"""
Universal Agent - Модульная структура автономного агента

Основные классы:
- UniversalAgent: основной класс агента с памятью и инструментами
- ExtendedLocalEnv: среда выполнения с инструментами
- AgentMemory: система памяти на FAISS
- TaskPlanner: планировщик задач
- GrokIntegration: интеграция с Grok
- CopilotIntegration: интеграция с GitHub Copilot
- WebsiteBuilder: создатель веб-сайтов
- SiteCopier: копировщик сайтов
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Optional, Any

_log = logging.getLogger(__name__)

# Ленивые импорты для предотвращения FAISS ошибок при импорте пакета
def _lazy_import_core():
    try:
        from .core import UniversalAgent
        return UniversalAgent
    except ImportError as e:
        _log.warning("Could not import core module: %s", e)
        return None

def _lazy_import_memory():
    try:
        from .memory import AgentMemory
        return AgentMemory
    except ImportError as e:
        _log.warning("Could not import memory module: %s", e)
        return None

def _lazy_import_tools():
    try:
        from .tools import TOOLS
        return TOOLS
    except ImportError as e:
        _log.warning("Could not import tools module: %s", e)
        return None

def _lazy_import_planner():
    try:
        from .planner import TaskPlanner
        return TaskPlanner
    except ImportError as e:
        _log.warning("Could not import planner module: %s", e)
        return None

def _lazy_import_ollama():
    try:
        from .ollama_client import OllamaClient
        return OllamaClient
    except ImportError as e:
        _log.warning("Could not import ollama module: %s", e)
        return None

def _lazy_import_grok():
    try:
        from .grok_integration import GrokIntegration
        return GrokIntegration
    except ImportError as e:
        _log.warning("Could not import grok module: %s", e)
        return None

def _lazy_import_copilot():
    try:
        from .copilot_integration import CopilotIntegration
        return CopilotIntegration
    except ImportError as e:
        _log.warning("Could not import copilot module: %s", e)
        return None

def _lazy_import_website():
    try:
        from .website_builder import WebsiteBuilder
        return WebsiteBuilder
    except ImportError as e:
        _log.warning("Could not import website module: %s", e)
        return None

def _lazy_import_site():
    try:
        from .site_copier import SiteCopier
        return SiteCopier
    except ImportError as e:
        _log.warning("Could not import site module: %s", e)
        return None

def _lazy_import_gpu():
    try:
        from .gpu_tools import GPUTools
        return GPUTools
    except ImportError as e:
        _log.warning("Could not import gpu_tools module: %s", e)
        return None

def _lazy_import_core_tools():
    try:
        from .core_tools import CoreTools
        return CoreTools
    except ImportError as e:
        _log.warning("Could not import core_tools module: %s", e)
        return None

from .utils import setup_logger, format_execution_time, SUMMARIZER_PROMPT_TEMPLATE, clean_instruction

_LAZY_EXPORTS: Dict[str, Callable[[], Optional[Any]]] = {
    "UniversalAgent": _lazy_import_core,
    "AgentMemory": _lazy_import_memory,
    "TOOLS": _lazy_import_tools,
    "TaskPlanner": _lazy_import_planner,
    "OllamaClient": _lazy_import_ollama,
    "GrokIntegration": _lazy_import_grok,
    "CopilotIntegration": _lazy_import_copilot,
    "WebsiteBuilder": _lazy_import_website,
    "SiteCopier": _lazy_import_site,
    "GPUTools": _lazy_import_gpu,
    "CoreTools": _lazy_import_core_tools,
}

def __getattr__(name: str):
    """
    Lazy-export public symbols so `import agent; agent.UniversalAgent` works,
    without importing heavy/optional deps at package import time.
    """
    factory = _LAZY_EXPORTS.get(name)
    if factory is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    obj = factory()
    # Cache (even if None) to avoid repeated import attempts.
    globals()[name] = obj
    return obj

def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_EXPORTS.keys()))

__all__ = [
    'UniversalAgent',
    'AgentMemory', 
    'TOOLS',
    'TaskPlanner',
    'OllamaClient',
    'GrokIntegration',
    'CopilotIntegration',
    'WebsiteBuilder',
    'SiteCopier',
    'GPUTools',
    'CoreTools',
    'setup_logger',
    'format_execution_time',
    'SUMMARIZER_PROMPT_TEMPLATE',
    'clean_instruction'
]
