"""
Планировщик задач для агента с исправленными командами копирования
"""

import json
import re
from typing import Dict, Any, Optional

from .utils import (
    PLANNER_PROMPT_TEMPLATE, 
    validate_tool_params,
    is_programming_task,
    is_search_task,
    is_website_task,
    setup_logger,
    logger,
    clean_instruction as clean_instruction_func,  # Явно импортируем как функцию
    GPU_STATUS_KEYWORDS,
    GPU_ENABLE_KEYWORDS,
    GPU_RESTART_KEYWORDS,
    COPY_KEYWORDS,
    ANALYZE_KEYWORDS,
    FULL_SITE_KEYWORDS,
    ORIGINAL_KEYWORDS,
    COPY_VERB_KEYWORDS
)

logger = setup_logger(__name__)

class TaskPlanner:
    """Планировщик задач с поддержкой различных движков"""
    
    def __init__(self, engine=None, local_llm=None, agent=None):
        self.engine = engine
        self.local_llm = local_llm
        self.agent = agent
        self.ollama_client = getattr(agent, 'ollama_client', None) if agent else None
    
    def create_plan(self, instruction: str) -> Dict[str, Any]:
        """Создает план выполнения задачи"""
        # Очищаем инструкцию от лишнего текста
        cleaned_instruction = clean_instruction_func(instruction)
        instruction_lower = cleaned_instruction.lower()
        
        # Проверяем на fashion-задачи (приоритет 0.5)
        if self._is_fashion_task(instruction_lower):
            return self._create_fashion_plan(cleaned_instruction)
        
        # Проверяем на GPU команды (приоритет 1)
        
        # GPU статус
        if any(keyword in instruction_lower for keyword in GPU_STATUS_KEYWORDS):
            return {
                'task_type': 'gpu_status',
                'steps': [{
                    'tool': 'gpu_status',
                    'description': 'Проверка статуса GPU',
                    'parameters': {}
                }],
                'requires_local_env': True
            }
        
        # Включение GPU
        if any(keyword in instruction_lower for keyword in GPU_ENABLE_KEYWORDS):
            return {
                'task_type': 'gpu_enable',
                'steps': [{
                    'tool': 'enable_gpu',
                    'description': 'Включение GPU для агента',
                    'parameters': {}
                }],
                'requires_local_env': True
            }
        
        # Перезапуск сервисов
        if any(keyword in instruction_lower for keyword in GPU_RESTART_KEYWORDS):
            return {
                'task_type': 'gpu_restart',
                'steps': [{
                    'tool': 'restart_services',
                    'description': 'Перезапуск сервисов для GPU',
                    'parameters': {}
                }],
                'requires_local_env': True
            }
        
        # Проверяем на команду анализа и копирования сайта (приоритет 1)
        
        is_copy_request = any(keyword in instruction_lower for keyword in COPY_KEYWORDS)
        
        if is_copy_request:
            # Извлекаем URL из инструкции
            url_pattern = r'https?://[^\s\)]+'
            url_match = re.search(url_pattern, instruction)
            
            if url_match:
                url = url_match.group(0)
                return {
                    'task_type': 'site_copy',
                    'steps': [{
                        'tool': 'analyze_and_copy',
                        'description': f'Анализ и копирование сайта с URL: {url}',
                        'parameters': {'url': url}
                    }],
                    'requires_local_env': True
                }
            else:
                return {
                    'task_type': 'site_copy',
                    'steps': [{
                        'tool': 'analyze_and_copy',
                        'description': 'Анализ и копирование сайта (URL не указан)',
                        'parameters': {'url': 'https://example.com'}
                    }],
                    'requires_local_env': True
                }
        
        # Проверяем на команду анализа сайта (приоритет 2)
        
        is_analyze_request = any(keyword in instruction_lower for keyword in ANALYZE_KEYWORDS)
        
        if is_analyze_request:
            # Извлекаем URL из инструкции
            url_pattern = r'https?://[^\s\)]+'
            url_match = re.search(url_pattern, instruction)
            
            if url_match:
                url = url_match.group(0)
                return {
                    'task_type': 'website_analysis',
                    'steps': [{
                        'tool': 'analyze_website',
                        'description': f'Анализ сайта: {url}',
                        'parameters': {'url': url, 'depth': 2}
                    }],
                    'requires_local_env': True
                }
            else:
                return {
                    'task_type': 'website_analysis',
                    'steps': [{
                        'tool': 'analyze_website',
                        'description': 'Анализ сайта (URL не указан)',
                        'parameters': {'url': 'https://example.com', 'depth': 2}
                    }],
                    'requires_local_env': True
                }
        
        # Проверяем на команду создания полноценного сайта (приоритет 3)
        
        is_full_site_request = any(keyword in instruction_lower for keyword in FULL_SITE_KEYWORDS)
        
        if is_full_site_request:
            # Извлекаем тему из инструкции
            theme = "business"  # тема по умолчанию
            
            # Пытаемся извлечь тему из инструкции
            theme_patterns = [
                r'тема[:\s]+["\']?([^"\',\s]+)["\']?',
                r'тематика[:\s]+["\']?([^"\',\s]+)["\']?',
                r'о\s+["\']?([^"\',\s]+)["\']?',
                r'про\s+["\']?([^"\',\s]+)["\']?',
                r'для\s+["\']?([^"\',\s]+)["\']?',
                r'сайт\s+["\']?([^"\',\s]+)["\']?',
                r'веб-сайт\s+["\']?([^"\',\s]+)["\']?',
                r'website\s+["\']?([^"\',\s]+)["\']?',
            ]
            
            for pattern in theme_patterns:
                match = re.search(pattern, instruction_lower)
                if match:
                    theme = match.group(1)
                    break
            
            # Определяем тип сайта
            if 'магазин' in instruction_lower or 'shop' in instruction_lower:
                site_type = 'ecommerce'
                pages_count = 8
            elif 'портфолио' in instruction_lower or 'portfolio' in instruction_lower:
                site_type = 'portfolio'
                pages_count = 5
            elif 'блог' in instruction_lower or 'blog' in instruction_lower:
                site_type = 'blog'
                pages_count = 4
            elif 'полноценный' in instruction_lower or 'многостраничный' in instruction_lower:
                site_type = 'full'
                pages_count = 7
            else:
                site_type = 'full'
                pages_count = 7
            
            return {
                'task_type': 'website_creation',
                'steps': [
                    {
                        'tool': 'create_full_website',
                        'description': f'Создание {site_type} сайта на тему: {theme}',
                        'parameters': {
                            'theme': theme,
                            'site_type': site_type,
                            'pages_count': pages_count,
                            'framework': 'bootstrap'
                        }
                    }
                ],
                'requires_local_env': True
            }
        
        # Проверяем на команду обучения у Grok (приоритет 4)
        instruction_str = str(cleaned_instruction) if not isinstance(cleaned_instruction, str) else cleaned_instruction
        if instruction_str.lower().startswith("учи у grok") or instruction_str.lower().startswith("learn from grok"):
            # Извлекаем вопрос из команды
            question = ""
            if ":" in cleaned_instruction:
                question = cleaned_instruction.split(":", 1)[1].strip()
            
            return {
                'task_type': 'grok_learning',
                'steps': [
                    {
                        'tool': 'ask_grok',
                        'description': f'Обучение на Grok для: {question}',
                        'parameters': {'question': f'Как лучше всего ответить на: {question}'}
                    }
                ]
            }
        
        # Проверяем на команду программирования (приоритет 5)
        if is_programming_task(cleaned_instruction):
            return self._create_code_plan(cleaned_instruction)
        
        # Проверяем на команду поиска (приоритет 6)
        if is_search_task(cleaned_instruction):
            return self._create_search_plan(cleaned_instruction)
        
        # Проверяем на запросы погоды (приоритет 7)
        weather_keywords = ['погода', 'weather', 'температура', 'прогноз']
        if any(word in instruction_lower for word in weather_keywords):
            # Извлекаем город из запроса
            city_match = re.search(r"погода\s+(?:в\s+)?([\w\-]+)", instruction_lower)
            city = city_match.group(1).title() if city_match else "Киев"  # Fallback на Киев
            return {
                'task_type': 'weather',
                'steps': [{
                    'tool': 'get_weather',
                    'description': f'Получить погоду в {city}',
                    'parameters': {'city': city}
                }],
                'requires_local_env': True
            }
        
        # Создаем общий план через LLM
        return self._create_general_plan(cleaned_instruction)
    
    def _create_website_plan(self, instruction: str) -> Dict[str, Any]:
        """Создает план для анализа или копирования сайта"""
        # Сначала очищаем инструкцию
        cleaned_instruction = clean_instruction_func(instruction)
        
        # Извлекаем URL из инструкции
        url = self._extract_url_from_instruction(cleaned_instruction)
        
        # Извлекаем тему контента
        theme = self._extract_theme_from_instruction(cleaned_instruction)
        
        # Проверяем, нужно ли создавать оригинальный сайт
        
        is_original_task = any(keyword in cleaned_instruction.lower() for keyword in ORIGINAL_KEYWORDS)
        is_copy_task = any(keyword in cleaned_instruction.lower() for keyword in COPY_VERB_KEYWORDS)
        
        if is_original_task:
            # Компромиссный план: анализ + копия главной + генерация оригинальных подстраниц
            return {
                'task_type': 'website_original',
                'steps': [
                    {
                        'tool': 'analyze_website',
                        'description': f'Анализ сайта: {url}',
                        'parameters': {'url': url, 'depth': 2}
                    },
                    {
                        'tool': 'create_site_copy',
                        'description': f'Копия главной страницы: {url}',
                        'parameters': {
                            'structure_json': '{{previous_result.analysis}}',
                            'folder': f'original_site_{url.replace("https://", "").replace("http://", "").replace("/", "_")}',
                            'only_main': True
                        }
                    },
                    {
                        'tool': 'generate_original_site',
                        'description': f'Генерация оригинальных подстраниц на основе {url}',
                        'parameters': {
                            'analysis_json': '{{previous_result.analysis}}',
                            'content_theme': theme,
                            'folder': f'original_site_{url.replace("https://", "").replace("http://", "").replace("/", "_")}',
                            'num_pages': 5,
                            'with_sidebar': True,
                            'adaptive': True
                        }
                    }
                ]
            }
        elif is_copy_task:
            # План для создания копии сайта
            return {
                'task_type': 'website_copy',
                'steps': [
                    {
                        'tool': 'analyze_website',
                        'description': f'Анализ сайта: {url}',
                        'parameters': {'url': url, 'depth': 1}
                    },
                    {
                        'tool': 'create_site_copy',
                        'description': f'Создание копии сайта: {url}',
                        'parameters': {
                            'structure_json': '{{previous_result.analysis}}',
                            'folder': f'site_copy_{url.replace("https://", "").replace("http://", "").replace("/", "_")}'
                        }
                    }
                ]
            }
        else:
            # План только для анализа сайта
            return {
                'task_type': 'website_analysis',
                'steps': [{
                    'tool': 'analyze_website',
                    'description': f'Анализ сайта: {url}',
                    'parameters': {'url': url, 'depth': 2}
                }]
            }
    
    def _extract_theme_from_instruction(self, instruction: str) -> str:
        """Извлекает тему контента из инструкции"""
        import re
        
        # Ищем тему после ключевых слов
        theme_patterns = [
            r'тема[:\s]+["\']?([^"\',\s]+)["\']?',
            r'тематика[:\s]+["\']?([^"\',\s]+)["\']?',
            r'о\s+["\']?([^"\',\s]+)["\']?',
            r'про\s+["\']?([^"\',\s]+)["\']?',
            r'для\s+["\']?([^"\',\s]+)["\']?',
            r'сайт\s+["\']?([^"\',\s]+)["\']?',
            r'веб-сайт\s+["\']?([^"\',\s]+)["\']?',
            r'website\s+["\']?([^"\',\s]+)["\']?',
            r'в\s+папку\s+["\']?([^"\',\s]+)["\']?'
        ]
        
        for pattern in theme_patterns:
            match = re.search(pattern, cleaned_instruction.lower())
            if match:
                return match.group(1)
        
        # Если тема не найдена, используем "my_theme"
        return "my_theme"
    
    def _extract_url_from_instruction(self, instruction: str) -> str:
        """Извлекает URL из инструкции"""
        import re
        
        # Ищем URL в тексте
        url_patterns = [
            r'https?://[^\s\)]+',
            r'http://[^\s\)]+'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, instruction)
            if match:
                return match.group(0)
        
        # Если URL не найден, возвращаем пример
        return "https://example.com"
    
    def _create_code_plan(self, instruction: str) -> Dict[str, Any]:
        """Создает план для выполнения кода"""
        # Извлекаем код из инструкции
        code = self._extract_code_from_instruction(instruction)
        
        return {
            'task_type': 'code',
            'steps': [{
                'tool': 'code_execution',
                'description': f'Выполнить код: {instruction}',
                'parameters': {'code': code}
            }]
        }
    
    def _create_search_plan(self, instruction: str) -> Dict[str, Any]:
        """Создает план для поиска информации"""
        # Извлекаем поисковый запрос
        search_query = self._extract_search_query(instruction)
        
        return {
            'task_type': 'search',
            'steps': [{
                'tool': 'tavily_search',
                'description': f'Поиск: {search_query}',
                'parameters': {'query': search_query}
            }]
        }
    
    def _extract_code_from_instruction(self, instruction: str) -> str:
        """Извлекает код из инструкции"""
        # Простая реализация - возвращаем всю инструкцию как код
        return instruction
    
    def _extract_search_query(self, instruction: str) -> str:
        """Извлекает поисковый запрос"""
        # Простая реализация - возвращаем всю инструкцию как запрос
        return instruction
    
    def _create_general_plan(self, instruction: str) -> Dict[str, Any]:
        """Создает общий план через LLM"""
        # Создаем пример JSON отдельно
        example_json = '{"steps": [{"tool": "code_execution", "description": "выполнить код", "parameters": {"code": "print(\\"hello\\")"}}]}'
        
        plan_prompt = PLANNER_PROMPT_TEMPLATE.format(
            instruction=instruction,
            example_json=example_json
        )
        
        try:
            # Пробуем основной engine
            if self.engine:
                response = self.engine.generate(plan_prompt)
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from engine. Raw response: {response[:500]}...")
                    pass
            
            # Пробуем локальный LLM
            elif self.local_llm and self.local_llm.model:
                response = self.local_llm.generate(plan_prompt)
                try:
                    json_match = re.search(r'\\{.*\\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from local LLM. Raw response: {response[:500]}...")
                    pass
            
            # Пробуем Ollama
            elif self.ollama_client:
                response = self.ollama_client.generate(plan_prompt)
                try:
                    json_match = re.search(r'\\{.*\\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from Ollama. Raw response: {response[:500]}...")
                    pass
            
            # Fallback план
            return self._create_fallback_plan(instruction)
            
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            return self._create_fallback_plan(instruction)
    
    def _create_fallback_plan(self, instruction: str) -> Dict[str, Any]:
        """Создает простой fallback план через Ollama"""
        logger.info(f"DEBUG _create_fallback_plan: received instruction type = {type(instruction)}")
        logger.info(f"DEBUG _create_fallback_plan: received instruction value = {repr(instruction)}")
        
        # Проверяем, не является ли instruction функцией
        if callable(instruction):
            logger.warning("instruction is callable, using fallback string")
            instruction = "Общий запрос"
        else:
            logger.info(f"DEBUG _create_fallback_plan: instruction is not callable, value = {instruction}")
        
        # Сначала очищаем инструкцию
        cleaned_instruction = clean_instruction_func(instruction)
        logger.info(f"DEBUG _create_fallback_plan: cleaned_instruction = {cleaned_instruction}")
        
        # Проверяем программирование и поиск (приоритетные)
        if is_programming_task(cleaned_instruction):
            return self._create_code_plan(cleaned_instruction)
        elif is_search_task(cleaned_instruction):
            return self._create_search_plan(cleaned_instruction)
        else:
            # Всё остальное - отправляем в Ollama для осмысленного ответа
            logger.info(f"DEBUG _create_fallback_plan: sending to Ollama: {cleaned_instruction}")
            return {
                'task_type': 'general_query',
                'steps': [{
                    'tool': 'ollama',
                    'description': f'Ответ на общий вопрос через Ollama',
                    'parameters': {'prompt': cleaned_instruction}
                }],
                'requires_local_env': False
            }
    
    def validate_plan(self, plan: Dict[str, Any]) -> bool:
        """Валидирует план выполнения"""
        if not isinstance(plan, dict):
            return False
        
        steps = plan.get('steps', [])
        if not isinstance(steps, list):
            return False
        
        valid_tools = [
            'tavily_search', 'browse_page', 'file_operations', 'code_execution', 
            'analyze_website', 'create_site_copy', 'generate_original_site', 
            'html_validator', 'css_beautifier', 'js_beautifier',
            'ask_grok', 'learn_from_grok', 'save_grok_answer',
            'get_weather', 'ollama', 'ollama_models', 'ollama_status',
            'copy_site', 'analyze_and_copy', 'create_full_website',
            'gpu_status', 'enable_gpu', 'restart_services',
            'design_clothing'
        ]
        # Copilot инструменты отключены по запросу пользователя
        
        for step in steps:
            if not isinstance(step, dict):
                return False
            
            tool = step.get('tool')
            if tool not in valid_tools:
                logger.warning(f"Unknown tool in plan: {tool}")
                return False
        
        return True
    
    def _extract_garment_type(self, description: str) -> str:
        """Извлечь тип одежды из описания"""
        garment_mapping = {
            'платье': 'dress',
            'платья': 'dress', 
            'куртку': 'jacket',
            'куртка': 'jacket',
            'брюки': 'pants',
            'брюки': 'pants',
            'футболку': 'tshirt',
            'футболка': 'tshirt',
            'джинсы': 'pants',
            'джинсы': 'pants',
            'рубашка': 'shirt',
            'рубашку': 'shirt',
            'юбка': 'skirt',
            'юбку': 'skirt',
            'блузка': 'blouse',
            'блузку': 'blouse',
            'пальто': 'coat',
            'пальто': 'coat',
            'пиджак': 'vest',
            'пиджака': 'vest',
            'свитер': 'sweater',
            'свитера': 'sweater'
        }
        
        description_lower = description.lower()
        for key, value in garment_mapping.items():
            if key in description_lower:
                return value
        
        return 'dress'  # По умолчанию
    
    def _extract_style(self, description: str) -> str:
        """Извлечь стиль одежды из описания"""
        style_mapping = {
            'вечерний': 'evening',
            'вечернее': 'evening',
            'деловой': 'business',
            'деловая': 'business',
            'спортивный': 'sport',
            'спортивная': 'sport',
            'повседневный': 'casual',
            'повседневная': 'casual',
            'классический': 'formal',
            'классическая': 'formal',
            'современный': 'modern',
            'современная': 'modern',
            'ретро': 'vintage',
            'ретро': 'vintage'
        }
        
        description_lower = description.lower()
        for key, value in style_mapping.items():
            if key in description_lower:
                return value
        
        return 'casual'  # По умолчанию
    
    def _get_default_measurements(self) -> Dict[str, float]:
        """Получить стандартные мерки по умолчанию"""
        return {
            'height': 168.0,  # Рост в см
            'bust': 88.0,     # Обхват груди в см
            'waist': 68.0,    # Обхват талии в см
            'hips': 94.0      # Обхват бедер в см
        }
    
    def _is_fashion_task(self, instruction: str) -> bool:
        """Проверяет, является ли задача fashion-типом"""
        clothing_keywords = [
            'одежда', 'лекала', 'выкройка',
            'блузка', 'свитер', 'пиджак',
            'юбка', 'платье', 'пальто',
            'куртка', 'брюки', 'создай', 'сделай'
        ]
        instruction_lower = instruction.lower()
        return any(word in instruction_lower for word in clothing_keywords)
    
    def _create_fashion_plan(self, instruction: str) -> Dict[str, Any]:
        """Создает план для fashion-задачи"""
        # Извлекаем тип одежды из текста
        garment_type = self._extract_garment_type(instruction)
        
        return {
            'task_type': 'clothing_design',
            'steps': [
                {
                    'tool': 'design_clothing',
                    'description': 'Генерация дизайна и конструкции одежды',
                    'parameters': {
                        'garment_type': garment_type,
                        'style': 'default'
                    }
                },
                {
                    'tool': 'design_clothing',
                    'description': 'Построение лекал',
                    'parameters': {
                        'stage': 'pattern'
                    }
                },
                {
                    'tool': 'design_clothing',
                    'description': 'Экспорт лекал',
                    'parameters': {
                        'stage': 'export'
                    }
                }
            ],
            'requires_local_env': True
        }
    
    def get_plan_summary(self, plan: Dict[str, Any]) -> str:
        """Возвращает текстовое описание плана"""
        if not plan or 'steps' not in plan:
            return "План не создан"
        
        steps = plan['steps']
        if not steps:
            return "Пустой план"
        
        summary = f"План содержит {len(steps)} шагов:\n"
        for i, step in enumerate(steps, 1):
            tool = step.get('tool', 'неизвестно')
            description = step.get('description', 'нет описания')
            summary += f"{i}. {tool}: {description}\n"
        
        return summary
