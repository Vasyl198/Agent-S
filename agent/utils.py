"""
Вспомогательные функции и утилиты для агента
"""

import os
import sys
import logging
import time
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Проверка зависимостей
def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    dependencies = {
        'requests': 'requests',
        'beautifulsoup4': 'BS4_AVAILABLE',
        'readability': 'READABILITY_AVAILABLE',
        'restrictedpython': 'RESTRICTED_PYTHON_AVAILABLE',
        'sentence_transformers': 'SENTENCE_TRANSFORMERS_AVAILABLE',
        'faiss': 'FAISS_AVAILABLE',
        'tenacity': 'tenacity',
        'crewai': 'CREWAI_AVAILABLE'
    }
    
    status = {}
    
    # Проверяем requests
    try:
        import requests
        status['requests'] = True
    except ImportError:
        status['requests'] = False
    
    # Проверяем BeautifulSoup4
    try:
        import bs4
        status['beautifulsoup4'] = True
    except ImportError:
        status['beautifulsoup4'] = False
    
    # Проверяем readability
    try:
        from readability import Document
        status['readability'] = True
    except ImportError:
        status['readability'] = False
    
    # Проверяем RestrictedPython
    try:
        import RestrictedPython
        status['restrictedpython'] = True
    except ImportError:
        status['restrictedpython'] = False
    
    # Проверяем sentence-transformers
    try:
        import sentence_transformers
        status['sentence_transformers'] = True
    except ImportError:
        status['sentence_transformers'] = False
    
    # Проверяем FAISS
    try:
        import faiss  # type: ignore
        status['faiss'] = True
    except ImportError:
        status['faiss'] = False
    
    # Проверяем tenacity
    try:
        import tenacity
        status['tenacity'] = True
    except ImportError:
        status['tenacity'] = False
    
    # Проверяем CrewAI
    try:
        import crewai
        status['crewai'] = True
    except ImportError:
        status['crewai'] = False
    
    # Устанавливаем глобальные переменные
    globals()['BS4_AVAILABLE'] = status.get('beautifulsoup4', False)
    globals()['READABILITY_AVAILABLE'] = status.get('readability', False)
    globals()['RESTRICTED_PYTHON_AVAILABLE'] = status.get('restrictedpython', False)
    globals()['SENTENCE_TRANSFORMERS_AVAILABLE'] = status.get('sentence_transformers', False)
    globals()['FAISS_AVAILABLE'] = status.get('faiss', False)
    globals()['CREWAI_AVAILABLE'] = status.get('crewai', False)
    
    return status

# Выполняем проверку зависимостей при импорте
DEPENDENCIES_STATUS = check_dependencies()

# Логируем предупреждения для отсутствующих зависимостей
logger = logging.getLogger(__name__)
for dep, available in DEPENDENCIES_STATUS.items():
    if not available:
        logger.debug(f"Missing optional dependency: {dep}. Some features may not work.")

# Добавляем корень проекта в Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Настройка логирования
def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Настраивает логирование для всего проекта"""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def setup_logger(name: str) -> logging.Logger:
    """Создает и настраивает логгер для модуля"""
    return logging.getLogger(name)

# Глобальный логгер
logger = setup_logger(__name__)

# Функции для работы с хорошими примерами
def save_good_example(task: str, result: Dict[str, Any], generated_code: str = None):
    """Сохраняет успешный пример для обучения"""
    try:
        examples_file = PROJECT_ROOT / "agent" / "good_examples.json"
        
        # Загружаем существующие примеры
        if examples_file.exists():
            with open(examples_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"examples": [], "last_updated": None, "total_examples": 0}
        
        # Создаем новый пример
        example = {
            "id": len(data["examples"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "result": result,
            "generated_code": generated_code,
            "task_type": result.get("task_type", "unknown"),
            "success": True
        }
        
        # Добавляем пример
        data["examples"].append(example)
        data["last_updated"] = datetime.now().isoformat()
        data["total_examples"] = len(data["examples"])
        
        # Ограничиваем количество примеров (оставляем последние 50)
        if len(data["examples"]) > 50:
            data["examples"] = data["examples"][-50:]
            data["total_examples"] = len(data["examples"])
        
        # Сохраняем
        with open(examples_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Good example saved: {task[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to save good example: {e}")
        return False

def load_good_examples(task_type: str = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Загружает хорошие примеры для обучения"""
    try:
        examples_file = PROJECT_ROOT / "agent" / "good_examples.json"
        
        if not examples_file.exists():
            return []
        
        with open(examples_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = data.get("examples", [])
        
        # Фильтруем по типу задачи если указан
        if task_type:
            examples = [ex for ex in examples if ex.get("task_type") == task_type]
        
        # Возвращаем последние примеры
        return examples[-limit:] if examples else []
    except Exception as e:
        logger.error(f"Failed to load good examples: {e}")
        return []

def format_examples_for_prompt(examples: List[Dict[str, Any]]) -> str:
    """Форматирует примеры для добавления в промпт"""
    if not examples:
        return ""
    
    formatted = "\n\nВот примеры хорошего кода и ответов из прошлых успешных задач (включая идеальные ответы от Grok):\n"
    for i, example in enumerate(examples, 1):
        formatted += f"\nПример {i}:\n"
        formatted += f"Задача: {example.get('task', 'Unknown')}\n"
        
        # Если это пример от Grok, выделяем его
        if example.get('source') == 'grok_ideal_answer':
            formatted += "🌟 Идеальный ответ от Grok:\n"
            formatted += f"{example.get('generated_code', example.get('response', ''))}\n"
        elif example.get('generated_code'):
            # Ограничиваем размер кода в промпте
            code = example['generated_code']
            if len(code) > 1000:
                code = code[:1000] + "...\n[код обрезан для экономии места]"
            formatted += f"Код: {code}\n"
        formatted += "---\n"
    
    formatted += "\nСтарайся делать похоже на эти примеры, особенно на идеальные ответы от Grok.\n"
    return formatted

def safe_execute(func, *args, **kwargs) -> Dict[str, Any]:
    """Безопасное выполнение функции с обработкой ошибок"""
    try:
        result = func(*args, **kwargs)
        return {'success': True, 'result': result}
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return {'success': False, 'error': str(e)}

def format_execution_time(seconds: float) -> str:
    """Форматирует время выполнения в читаемый вид"""
    if seconds < 1:
        return f"{seconds*1000:.0f} мс"
    elif seconds < 60:
        return f"{seconds:.2f} сек"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes} мин {secs:.1f} сек"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезает текст до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def validate_tool_params(params: Dict[str, Any], required_params: list) -> Dict[str, Any]:
    """Валидация параметров инструмента"""
    missing = [p for p in required_params if p not in params]
    if missing:
        return {
            'success': False,
            'error': f'Missing required parameters: {missing}'
        }
    return {'success': True}

def clean_instruction(instruction: str) -> str:
    """Очищает инструкцию от лишнего текста"""
    
    # Проверяем тип
    if not isinstance(instruction, str):
        instruction = str(instruction)
    
    # Удаляем "Similar past tasks"
    if "Similar past tasks" in instruction:
        parts = instruction.split("Similar past tasks")
        instruction = parts[0].strip()
    
    # Удаляем префиксы
    prefixes_to_remove = [
        "Task:", "Задача:", "Instruction:", "Инструкция:",
        "Please", "Пожалуйста", "Could you", "Можете ли вы"
    ]
    
    for prefix in prefixes_to_remove:
        if instruction.lower().startswith(prefix.lower()):
            instruction = instruction[len(prefix):].strip()
    
    return instruction

def is_programming_task(instruction: str) -> bool:
    """Проверяет, является ли задача программированием"""
    # Проверяем тип
    if not isinstance(instruction, str):
        return False
        
    programming_keywords = [
        'код', 'code', 'программа', 'program', 'скрипт', 'script',
        'напиши код', 'создай код', 'покажи код', 'выведи код', 'выполни код', 'запусти код',
        'python', 'javascript', 'java', 'cpp', 'c++',
        'функция', 'function', 'класс', 'class', 'игра', 'game',
        'алгоритм', 'algorithm', 'переменная', 'variable'
    ]
    
    # Исключаем простые приветствия
    greetings = ['привет', 'здравствуй', 'hello', 'hi', 'приветствую', 'добрый день']
    instruction_lower = instruction.lower()
    
    # Если это приветствие, не считаем программированием
    if any(greeting in instruction_lower for greeting in greetings):
        return False
    
    instruction_str = str(instruction) if not isinstance(instruction, str) else instruction
    instruction_lower = instruction_str.lower()
    return any(keyword in instruction_lower for keyword in programming_keywords)

def is_search_task(instruction: str) -> bool:
    """Проверяет, является ли задача поиском"""
    search_keywords = [
        'найди', 'поиск', 'ищи', 'search', 'find', 'google',
        'информация', 'information', 'данные', 'data', 'новости', 'news'
    ]
    
    instruction_str = str(instruction) if not isinstance(instruction, str) else instruction
    instruction_lower = instruction_str.lower()
    return any(keyword in instruction_lower for keyword in search_keywords)

def is_website_task(instruction: str) -> bool:
    """Проверяет, является ли задача анализом или копированием сайта"""
    website_keywords = [
        'сайт', 'website', 'анализ', 'analyze', 'копия', 'copy',
        'парсинг', 'parsing', 'скачай', 'download', 'структуру',
        'html', 'css', 'javascript', 'страницу', 'проанализируй',
        'подобное', 'похожее', 'создай похожее', 'сделай подобное',
        'original', 'оригинальный', 'на основе', 'новое', 'подобное',
        'create new similar', 'create similar', 'based on', 'new similar',
        'create site', 'build site', 'generate site', 'website based',
        'создай сайт', 'создай веб-сайт', 'создай сайт на основе', 'создай веб-сайт на основе',
        'создай сайт с функцией', 'создай веб-сайт с функцией',
        'создай сайт с возможностью', 'создай веб-сайт с возможностью',
        'создай сайт на основе', 'создай веб-сайт на основе',
        'создай сайт с функцией', 'создай веб-сайт с функцией',
        'создай сайт с возможностью', 'создай веб-сайт с возможностью'
    ]
    
    instruction_str = str(instruction) if not isinstance(instruction, str) else instruction
    instruction_lower = instruction_str.lower()
    return any(keyword in instruction_lower for keyword in website_keywords)

# Промпты для Ollama
PLANNER_PROMPT_TEMPLATE = """
Разбей запрос на шаги. Используй только: tavily_search, browse_page, file_operations, code_execution, analyze_website, create_site_copy, generate_original_site.

Доступные инструменты:
- tavily_search — для поиска информации в интернете
- browse_page — для чтения веб-страниц
- file_operations — для работы с файлами
- code_execution — для написания и запуска Python-кода. Передавай код как строку.
- analyze_website — для анализа структуры сайта (заголовок, секции, ссылки, изображения)
- create_site_copy — для создания копии сайта на основе анализа
- generate_original_site — для создания оригинального сайта на основе анализа

ВАЖНО: 
- Если пользователь просит написать, выполнить или запустить код — используй code_execution
- Если задача про анализ сайта — используй analyze_website
- Если задача про копирование сайта — используй analyze_website + create_site_copy
- Если задача про "создай подобное" или "создай похожее" — используй analyze_website + generate_original_site
- Для создания оригинальных сайтов сначала анализируй, затем генерируй
- Глубина анализа: 1-2 страницы, только для обучения, не для коммерции

Примеры:
- 'напиши код и запусти' → code_execution
- 'выполни код' → code_execution
- 'запусти Python код' → code_execution
- 'проанализируй сайт example.com' → analyze_website
- 'создай копию сайта example.com' → analyze_website + create_site_copy
- 'создай подобный сайт example.com' → analyze_website + generate_original_site
- 'сделай похожий сайт на блог' → analyze_website + generate_original_site

Если задача про программирование и требует выполнения — приоритет code_execution над поиском.

Думай step-by-step. Проанализируй запрос, выбери правильный инструмент и создай план.

Запрос: {instruction}

Ответ в формате JSON:
{example_json}
"""

SUMMARIZER_PROMPT_TEMPLATE = """
Кратко и понятно на русском суммируй эту информацию, выделив главное. Будь дружелюбным и точным.

ВАЖНО: НЕ придумывай факты, используй только предоставленные данные ниже.

Заголовок: {heading}
Аннотация: {abstract}
Источник: {abstract_url}
Ссылки:
{links}

Суммаризуй в 2-4 предложения, укажи основную идею и 1-2 важные ссылки.
"""

CODE_GENERATION_TEMPLATES = {
    'abilities': 'print("Я умею: искать информацию, выполнять Python код, создавать игры, анализировать данные, суммаризировать тексты. Могу научиться новым задачам через примеры!")',
    'hello': 'print("Привет, мир!")',
    'calculator': '''
a = 10
b = 20
print(f"{a} + {b} = {a + b}")
print(f"{a} * {b} = {a * b}")
''',
    'numbers': '''
for i in range(1, 11):
    print(f"Число: {i}")
''',
    'default': 'print("Code generated based on request")'
}

def get_code_template(query: str) -> Optional[str]:
    """Возвращает шаблон кода на основе запроса"""
    query_lower = query.lower()
    
    if 'что ты умеешь' in query_lower or 'умеешь делать' in query_lower:
        return CODE_GENERATION_TEMPLATES['abilities']
    elif 'привет' in query_lower:
        return CODE_GENERATION_TEMPLATES['hello']
    elif 'калькулятор' in query_lower:
        return CODE_GENERATION_TEMPLATES['calculator']
    elif 'числа' in query_lower and 'от' in query_lower:
        return CODE_GENERATION_TEMPLATES['numbers']
    else:
        return CODE_GENERATION_TEMPLATES['default']

def check_gpu_status():
    """Проверяет статус GPU при запуске"""
    try:
        import torch
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU не используется! Запустите 'включи gpu' для активации")
            logger.info("💡 Используйте 'gpu status' для проверки состояния GPU")
            return False
        else:
            logger.info(f"✅ GPU доступен: {torch.cuda.get_device_name()}")
            return True
    except ImportError:
        logger.warning("⚠️ PyTorch не установлен")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Ошибка проверки GPU: {e}")
        return False

def setup_ollama_gpu():
    """Настраивает Ollama для использования GPU"""
    import os
    try:
        # Устанавливаем переменные окружения для Ollama
        os.environ['OLLAMA_GPU'] = '1'
        os.environ['OLLAMA_NUM_GPU_LAYERS'] = '999'
        
        logger.info("🦙 Ollama настроен для использования GPU")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Ошибка настройки Ollama GPU: {e}")
        return False

def get_gpu_info():
    """Получает базовую информацию о GPU"""
    try:
        import torch
        if torch.cuda.is_available():
            return {
                'available': True,
                'name': torch.cuda.get_device_name(),
                'memory': torch.cuda.get_device_properties(0).total_memory,
                'count': torch.cuda.device_count()
            }
        else:
            return {'available': False}
    except:
        return {'available': False}


# Константы для ключевых слов планировщика
GPU_STATUS_KEYWORDS = [
    'gpu status', 'статус gpu', 'gpu статус', 'проверь gpu', 'проверка gpu',
    'gpu информация', 'gpu info', 'gpu check'
]

GPU_ENABLE_KEYWORDS = [
    'включи gpu', 'enable gpu', 'gpu включи', 'активируй gpu', 'gpu активируй',
    'включить gpu', 'enable gpu', 'gpu enable', 'настрой gpu', 'gpu настрой'
]

GPU_RESTART_KEYWORDS = [
    'перезапусти сервисы', 'restart services', 'перезапуск сервисов',
    'restart gpu', 'gpu перезапусти', 'перезапусти gpu'
]

COPY_KEYWORDS = [
    'скопируй сайт', 'скопировать сайт', 'копируй сайт', 'копировать сайт',
    'скопируй веб-сайт', 'скопировать веб-сайт', 'копия сайта', 'сделай копию сайта',
    'проанализируй и создай', 'проанализируй и скопируй', 'анализируй и создай',
    'анализируй и скопируй', 'изучи и создай', 'изучи и скопируй',
    'создай точную копию', 'создай копию', 'сделай дубликат'
]

ANALYZE_KEYWORDS = [
    'проанализируй сайт', 'анализируй сайт', 'проанализируй', 'анализируй',
    'изучи сайт', 'разбери сайт', 'покажи структуру сайта'
]

FULL_SITE_KEYWORDS = [
    'полноценный сайт', 'многостраничный сайт', 'создай полноценный сайт', 
    'создай многостраничный сайт', 'полноценный многостраничный сайт',
    'сайт-магазин', 'магазин гаджетов', 'полноценный сайт-магазин',
    'создай сайт магазин', 'создай интернет-магазин', 'создай магазин',
    'create full website', 'create full site', 'создай полноценный сайт'
]

ORIGINAL_KEYWORDS = [
    'подобный', 'похожий', 'создай похожее', 'сделай подобное', 'original', 
    'оригинальный', 'на основе', 'новое', 'подобное', 'похожее', 'создай новое', 
    'create new similar', 'create similar', 'based on', 'new similar'
]

COPY_VERB_KEYWORDS = [
    'копия', 'copy', 'скачай', 'download'
]
