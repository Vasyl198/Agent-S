"""
Основной класс агента с логикой выполнения и интеграцией компонентов
"""

import json
import time
from typing import Dict, Any, List, Optional

# Ленивые импорты для предотвращения FAISS ошибок
def _lazy_import_memory():
    try:
        from .memory import AgentMemory
        return AgentMemory
    except ImportError as e:
        print(f"Warning: Could not import memory module: {e}")
        return None

def _lazy_import_tools():
    try:
        from .tools import TOOLS
        return TOOLS
    except ImportError as e:
        print(f"Warning: Could not import tools module: {e}")
        return None

def _lazy_import_planner():
    try:
        from .planner import TaskPlanner
        return TaskPlanner
    except ImportError as e:
        print(f"Warning: Could not import planner module: {e}")
        return None

def _lazy_import_ollama():
    try:
        from .ollama_client import OllamaClient
        return OllamaClient
    except ImportError as e:
        print(f"Warning: Could not import ollama module: {e}")
        return None

def _lazy_import_grok():
    try:
        from .grok_integration import GrokIntegration
        return GrokIntegration
    except ImportError as e:
        print(f"Warning: Could not import grok module: {e}")
        return None

def _lazy_import_copilot():
    try:
        from .copilot_integration import CopilotIntegration
        return CopilotIntegration
    except ImportError as e:
        print(f"Warning: Could not import copilot module: {e}")
        return None

def _lazy_import_website():
    try:
        from .website_builder import WebsiteBuilder
        return WebsiteBuilder
    except ImportError as e:
        print(f"Warning: Could not import website module: {e}")
        return None

def _lazy_import_site():
    try:
        from .site_copier import SiteCopier
        return SiteCopier
    except ImportError as e:
        print(f"Warning: Could not import site module: {e}")
        return None

def _lazy_import_self_improvement():
    try:
        from .self_improvement import SelfImprovementSystem
        return SelfImprovementSystem
    except ImportError as e:
        print(f"Warning: Could not import self_improvement module: {e}")
        return None

from .utils import logger, format_execution_time, SUMMARIZER_PROMPT_TEMPLATE, check_gpu_status, setup_ollama_gpu, CREWAI_AVAILABLE

# Импорты CrewAI если доступны
try:
    from crewai import Crew, Agent, Task
    from crewai.process import Process
    CREWAI_IMPORTS_AVAILABLE = True
except ImportError:
    CREWAI_IMPORTS_AVAILABLE = False

class UniversalAgent:
    """Универсальный автономный агент с памятью и инструментами"""
    
    def __init__(self, enable_local_env: bool = True, enable_reflection: bool = True, persist_path: str = "universal_agent_memory") -> None:
        self.persist_path = persist_path
        
        # Ленивая инициализация компонентов для предотвращения FAISS ошибок
        AgentMemory = _lazy_import_memory()
        self.memory = AgentMemory(persist_path)
        
        TOOLS = _lazy_import_tools()
        self.tools = TOOLS
        
        OllamaClient = _lazy_import_ollama()
        self.ollama_client = OllamaClient()
        
        # Проверяем и настраиваем GPU
        setup_ollama_gpu()
        gpu_available = check_gpu_status()
        self.gpu_enabled = gpu_available
        
        # Инициализация планировщика
        TaskPlanner = _lazy_import_planner()
        self.planner = TaskPlanner(
            engine=getattr(self, 'engine', None),
            local_llm=getattr(self, 'local_llm', None),
            agent=self
        )
        
        # Инициализация новых интеграций
        GrokIntegration = _lazy_import_grok()
        self.grok_integration = GrokIntegration(self)
        
        WebsiteBuilder = _lazy_import_website()
        self.website_builder = WebsiteBuilder(self)
        
        SiteCopier = _lazy_import_site()
        self.site_copier = SiteCopier()
        
        SelfImprovementSystem = _lazy_import_self_improvement()
        self.self_improvement = SelfImprovementSystem(self)
        
        # Инициализация системы самообучения
        self.self_improvement = SelfImprovementSystem(f"{persist_path}_improvement")
        
        # Copilot отключен по запросу пользователя
        # self.copilot_integration = CopilotIntegration(self)
        
        # Дополнительные компоненты
        self.enable_reflection = enable_reflection
        
        # История выполнения
        self.execution_history = []
        
        # Регистрируем инструменты
        self._register_tools()
        
        logger.info("UniversalAgent initialized successfully")
    
    def _register_tools(self) -> None:
        """Регистрирует все инструменты в tools"""
        # Инструменты уже зарегистрированы в реестре
        # Дополнительная регистрация не нужна
        pass
    
    # Делегирование методов Grok интеграции
    def copy_website(self, url: str, output_dir: str = None) -> Dict[str, Any]:
        """Копирует сайт с указанного URL"""
        return self.site_copier.copy_site(url, output_dir)
    
    def analyze_and_copy_site(self, url: str, output_dir: str = None) -> Dict[str, Any]:
        """Анализирует и копирует сайт"""
        try:
            # Используем tools вместо local_env
            if 'analyze_website' in self.tools:
                analysis = self.tools['analyze_website'](url)
                if analysis.get('success'):
                    logger.info(f"Site analysis completed: {url}")
                else:
                    logger.warning(f"Site analysis failed: {analysis.get('error', 'Unknown error')}")
            
            # Затем копируем сайт
            return self.site_copier.copy_site(url, output_dir)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка анализа и копирования сайта: {str(e)}'
            }
    
    def ask_ollama(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """Задает вопрос Ollama"""
        try:
            if model is None:
                model = self.ollama_client.default_model
            
            response = self.ollama_client.generate(prompt, model)
            if response:
                return {
                    'success': True,
                    'response': response,
                    'model': model,
                    'prompt': prompt
                }
            else:
                return {
                    'success': False,
                    'error': 'Ollama не смог сгенерировать ответ'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка Ollama: {str(e)}'
            }
    
    def list_ollama_models(self) -> Dict[str, Any]:
        """Возвращает список моделей Ollama"""
        try:
            models = self.ollama_client.list_models()
            return {
                'success': True,
                'models': models,
                'count': len(models)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка получения моделей: {str(e)}'
            }
    
    def check_ollama_status(self) -> Dict[str, Any]:
        """Проверяет статус Ollama"""
        try:
            is_available = self.ollama_client.is_available()
            models = self.ollama_client.list_models() if is_available else []
            
            return {
                'success': True,
                'available': is_available,
                'models': models,
                'default_model': self.ollama_client.default_model,
                'base_url': self.ollama_client.base_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка проверки статуса: {str(e)}'
            }
    
    def ask_grok(self, question: str, gui_mode: bool = False) -> Dict[str, Any]:
        """Задает вопрос Grok (ручной режим без API ключа)"""
        return self.grok_integration.ask_grok(question, gui_mode)
    
    def save_grok_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """Сохраняет ответ от Grok (для GUI режима)"""
        return self.grok_integration.save_grok_answer(question, answer)
    
    def learn_from_grok(self, topic: str) -> Dict[str, Any]:
        """Обучается у Grok в ручном режиме с показом и запуском кода"""
        return self.grok_integration.learn_from_grok(topic)
    
    # Делегирование методов Copilot интеграции
    def copilot_authenticate(self) -> Dict[str, Any]:
        """Аутентификация в GitHub Copilot"""
        return self.copilot_integration.copilot_authenticate()
    
    def copilot_suggest(self, code: str, language: str = "python", context: str = "") -> Dict[str, Any]:
        """Получает предложение от Copilot для улучшения кода"""
        return self.copilot_integration.copilot_suggest(code, language, context)
    
    def copilot_explain(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Объясняет код с помощью Copilot"""
        return self.copilot_integration.copilot_explain(code, language)
    
    def copilot_generate(self, description: str, language: str = "python", context: str = "") -> Dict[str, Any]:
        """Генерирует код с помощью Copilot"""
        return self.copilot_integration.copilot_generate(description, language, context)
    
    def copilot_review(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Проводит code review с помощью Copilot"""
        return self.copilot_integration.copilot_review(code, language)
    
    def copilot_status(self) -> Dict[str, Any]:
        """Получает статус Copilot"""
        return self.copilot_integration.copilot_status()
    
    def test_tavily(self) -> Dict[str, Any]:
        """Тестирует подключение к Tavily"""
        try:
            result = self.tools['tavily_search']("текущая погода в Одессе")
            return {'success': True, 'result': result[:3]}  # первые 3 результата
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Делегирование методов Website Builder
    def create_full_website(self, theme: str, pages_count: int = 5, framework: str = 'bootstrap', **kwargs) -> Dict[str, Any]:
        """Создает полноценный многостраничный сайт с Bootstrap/Tailwind"""
        return self.website_builder.create_full_website(theme, pages_count, framework, **kwargs)
    
    def code_execution(self, code: str) -> Dict[str, Any]:
        """Выполняет Python код"""
        try:
            import subprocess
            import sys
            import tempfile
            import os
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Выполняем код
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=120  # Увеличили таймаут до 2 минут
                )
                
                output = result.stdout
                error = result.stderr
                
                return {
                    'success': result.returncode == 0,
                    'output': output,
                    'error': error if error else None,
                    'returncode': result.returncode
                }
            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': None
            }
    
    def execute_instruction(self, instruction: str) -> Dict[str, Any]:
        """Выполняет инструкцию и возвращает результат"""
        start_time = time.time()
        
        # Проверяем тип инструкции
        if not isinstance(instruction, str):
            logger.error(f"Instruction is not string: type={type(instruction)}")
            return {'success': False, 'error': 'Invalid instruction type'}
        
        # Отладка: проверяем что пришло
        logger.info(f"DEBUG execute_instruction: instruction type = {type(instruction)}")
        logger.info(f"DEBUG execute_instruction: instruction value = {repr(instruction)}")
        
        try:
            # Получаем похожие задачи из памяти
            similar_tasks = self.memory.recall_similar(instruction, top_k=3)
            
            # Создаем план выполнения
            plan = self.planner.create_plan(instruction)
            
            # Проверяем, нужно ли использовать CrewAI для сложных задач
            if (CREWAI_AVAILABLE and CREWAI_IMPORTS_AVAILABLE and 
                len(plan.get('steps', [])) > 3 and 
                any(keyword in str(instruction).lower() for keyword in ['анализ', 'отчет', 'исследование', 'анализируй'])):
                
                logger.info("Using CrewAI for complex task")
                crew_result = self._execute_with_crew(instruction, plan)
                
                # Сохраняем в память
                self.memory.add_task(instruction, crew_result, plan)
                
                # Формируем результат
                execution_time = time.time() - start_time
                
                result = {
                    'success': crew_result.get('success', False),
                    'plan': plan,
                    'results': [crew_result],
                    'execution_time': execution_time,
                    'similar_tasks': similar_tasks,
                    'instruction': instruction,
                    'used_crew': True
                }
                
                # Добавляем в историю
                self.execution_history.append({
                    'instruction': instruction,
                    'result': result,
                    'timestamp': time.time()
                })
                
                logger.info(f"CrewAI instruction executed in {format_execution_time(execution_time)}")
                return result
            
            # Валидируем план
            if not self.planner.validate_plan(plan):
                logger.warning("Invalid plan created, using fallback")
                plan = self.planner._create_fallback_plan(instruction)
            
            # Выполняем план
            results = self._execute_plan(plan)
            
            # Сохраняем в память
            self.memory.add_task(instruction, results, plan)
            
            # Формируем результат
            execution_time = time.time() - start_time
            
            result = {
                'success': all(r.get('success', False) for r in results),
                'plan': plan,
                'results': results,
                'execution_time': execution_time,
                'similar_tasks': similar_tasks,
                'instruction': instruction,
                'used_crew': False
            }
            
            # Добавляем в историю
            self.execution_history.append({
                'instruction': instruction,
                'result': result,
                'timestamp': time.time()
            })
            
            logger.info(f"Instruction executed in {format_execution_time(execution_time)}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing instruction: {e}")
            return {
                'success': False,
                'error': str(e),
                'instruction': instruction,
                'used_crew': False
            }
    
    def _execute_with_crew(self, instruction: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет задачу с помощью CrewAI"""
        try:
            # Создаем агентов для CrewAI
            researcher = Agent(
                role='Researcher',
                goal='Find and analyze information from various sources',
                backstory="""You are an expert researcher with strong analytical skills.
                You excel at finding relevant information and presenting it clearly.""",
                verbose=True,
                allow_delegation=False
            )
            
            writer = Agent(
                role='Writer',
                goal='Create comprehensive reports and summaries',
                backstory="""You are a skilled writer who can create clear, 
                well-structured reports based on research findings.""",
                verbose=True,
                allow_delegation=False
            )
            
            analyst = Agent(
                role='Analyst',
                goal='Analyze data and provide insights',
                backstory="""You are a data analyst who can identify patterns 
                and provide meaningful insights from information.""",
                verbose=True,
                allow_delegation=False
            )
            
            # Создаем задачи на основе плана
            tasks = []
            steps = plan.get('steps', [])
            
            for i, step in enumerate(steps[:3]):  # Ограничиваем 3 задачами
                task_description = step.get('description', f"Step {i+1}")
                
                if i == 0:
                    # Первая задача - исследование
                    task = Task(
                        description=f"Research: {task_description}",
                        agent=researcher,
                        expected_output="Detailed research findings with sources"
                    )
                elif i == 1:
                    # Вторая задача - анализ
                    task = Task(
                        description=f"Analyze: {task_description}",
                        agent=analyst,
                        expected_output="Analysis with insights and patterns"
                    )
                else:
                    # Третья задача - написание отчета
                    task = Task(
                        description=f"Report: {task_description}",
                        agent=writer,
                        expected_output="Comprehensive report with clear structure"
                    )
                
                tasks.append(task)
            
            # Создаем и запускаем crew
            crew = Crew(
                agents=[researcher, analyst, writer],
                tasks=tasks,
                verbose=2,
                process=Process.sequential
            )
            
            # Выполняем crew
            result = crew.kickoff()
            
            return {
                'success': True,
                'result': str(result),
                'crew_agents': len([researcher, analyst, writer]),
                'crew_tasks': len(tasks),
                'method': 'crewai'
            }
            
        except Exception as e:
            logger.error(f"Error in CrewAI execution: {e}")
            return {
                'success': False,
                'error': str(e),
                'method': 'crewai'
            }
    
    def save_state(self) -> None:
        """Сохраняет состояние агента"""
        try:
            if hasattr(self, 'memory'):
                self.memory.save_to_file()
            logger.info("Agent state saved")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _execute_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Выполняет план шаг за шагом"""
        results = []
        steps = plan.get('steps', [])
        
        for i, step in enumerate(steps):
            try:
                logger.info(f"Executing step {i+1}/{len(steps)}: {step.get('tool', 'unknown')}")
                
                # Обрабатываем параметры с подстановкой результатов предыдущих шагов
                processed_step = self._process_step_parameters(step, results)
                
                step_result = self._execute_step(processed_step)
                results.append(step_result)
                
                # Если шаг не удался и включена рефлексия
                if not step_result.get('success', False) and self.enable_reflection:
                    reflection = self._reflect_on_failure(step, step_result)
                    if reflection.get('should_retry', False):
                        # Повторная попытка с исправленным шагом
                        corrected_step = reflection.get('corrected_step', step)
                        retry_result = self._execute_step(corrected_step)
                        results[-1] = retry_result  # Заменяем результат
                
            except Exception as e:
                logger.error(f"Error executing step {i+1}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'step': step
                })
        
        return results
    
    def _process_step_parameters(self, step: Dict[str, Any], previous_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Обрабатывает параметры шага, подставляя результаты предыдущих шагов"""
        processed_step = step.copy()
        parameters = step.get('parameters', {}).copy()
        
        # Ищем плейсхолдеры вроде {{previous_result.structure}}
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str) and '{{previous_result' in param_value:
                # Если есть предыдущие результаты, подставляем их
                if previous_results:
                    last_result = previous_results[-1]
                    # Заменяем плейсхолдер на реальное значение
                    if '{{previous_result.analysis}}' in param_value:
                        if 'analysis' in last_result:
                            import json
                            param_value = param_value.replace('{{previous_result.analysis}}', json.dumps(last_result['analysis']))
                        else:
                            param_value = param_value.replace('{{previous_result.analysis}}', '{}')
                    elif '{{previous_result.structure}}' in param_value:
                        if 'structure' in last_result:
                            import json
                            param_value = param_value.replace('{{previous_result.structure}}', json.dumps(last_result['structure']))
                        else:
                            param_value = param_value.replace('{{previous_result.structure}}', '{}')
                    elif '{{previous_result}}' in param_value:
                        param_value = param_value.replace('{{previous_result}}', str(last_result))
                else:
                    # Если нет предыдущих результатов, заменяем на пустое значение
                    param_value = param_value.replace('{{previous_result.analysis}}', '{}')
                    param_value = param_value.replace('{{previous_result.structure}}', '{}')
                    param_value = param_value.replace('{{previous_result}}', '{}')
                
                parameters[param_name] = param_value
        
        processed_step['parameters'] = parameters
        return processed_step
    
    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет один шаг плана"""
        tool_name = step.get('tool')
        parameters = step.get('parameters', {})
        description = step.get('description', '')
        
        # Отладка: показываем все доступные инструменты
        if tool_name == 'create_full_website':
            logger.info(f"Available tools: {list(self.tools.keys())}")
            logger.info(f"Looking for tool: {tool_name}")
        
        # Получаем инструмент
        tool_func = self.tools.get(tool_name)
        if not tool_func:
            logger.error(f"Tool {tool_name} not found. Available: {list(self.tools.keys())}")
            return {
                'success': False,
                'error': f'Tool {tool_name} not found'
            }
        
        try:
            # Выполняем инструмент
            if tool_name == 'code_execution':
                # Особая обработка для code_execution
                code = parameters.get('code', description)
                
                # Проверяем тип и преобразуем в строку если нужно
                if not isinstance(code, str):
                    logger.warning(f"code parameter is not string: {type(code)}")
                    code = str(code)
                
                # Дополнительная проверка на функцию
                if callable(code):
                    logger.error(f"code parameter is callable, converting to string representation")
                    code = f"# Function object: {code}"
                
                # Проверяем, является ли это запросом на генерацию кода
                if self._is_text_request(code):
                    logger.info(f"Generating code for request: {code[:50]}...")
                    generated_code = self._generate_code_with_ollama(code)
                    
                    if generated_code and generated_code.strip():
                        code = generated_code
                        logger.info(f"Successfully generated code: {len(code)} chars")
                    else:
                        # Если не удалось сгенерировать, пробуем еще раз
                        logger.warning("Failed to generate code, retrying with simpler prompt...")
                        generated_code = self._generate_code_with_ollama(f"Напиши только код для: {code}")
                        if generated_code and generated_code.strip():
                            code = generated_code
                        else:
                            return {
                                'success': False,
                                'error': 'Failed to generate code for the request',
                                'request': code
                            }
                else:
                    # Если это уже код, извлекаем его
                    code = self._extract_code_from_description(code)
                
                # Выполняем сгенерированный код
                result = tool_func(code)
                # Добавляем сгенерированный код в результат для отображения
                if result.get('success'):
                    result['generated_code'] = code
            elif tool_name == 'tavily_search':
                # Особая обработка для поиска
                query = parameters.get('query', description)
                result = tool_func(query)
                if result.get('success') and result.get('data'):
                    # Суммаризируем результаты поиска
                    summary = self._summarize_search_results(result['data'])
                    result['summary'] = summary
            else:
                # Общее выполнение
                result = tool_func(**parameters)
            
            # Добавляем информацию о шаге
            result['step'] = step
            result['tool'] = tool_name
            
            # Если в шаге есть прямой ответ, добавляем его в результат
            if 'direct_response' in step:
                result['direct_response'] = step['direct_response']
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'step': step,
                'tool': tool_name
            }
    
    def _is_text_request(self, text) -> bool:
        """Проверяет, является ли запрос текстовым (не кодом)"""
        # Проверяем тип и преобразуем в строку если нужно
        if not isinstance(text, str):
            text = str(text)
        
        text_lower = text.lower()
        text_indicators = [
            'напиши', 'создай', 'покажи', 'выведи', 'сделай', 
            'сгенерируй', 'создай', 'разработай', 'напиши скрипт',
            'сделай программу', 'создай приложение'
        ]
        return any(indicator in text_lower for indicator in text_indicators)
    
    def _generate_code_with_ollama(self, request) -> Optional[str]:
        """Генерирует код через Ollama"""
        # Проверяем тип и преобразуем в строку если нужно
        if not isinstance(request, str):
            request = str(request)
        
        if not self.ollama_client:
            logger.warning("Ollama client not available for code generation")
            return None
        
        try:
            # Первый запрос с полным промптом
            prompt = f"""Напиши полный рабочий Python-код для: {request}

Требования:
- Используй 4 пробела для отступов
- Проверь импорты и синтаксис
- Верни ТОЛЬКО код в блоке ```python
- Код должен быть полным и рабочим
- Добавь main функцию если нужно

```python
"""
            
            response = self.ollama_client.generate(prompt)
            logger.info(f"Ollama response received: {response[:200] if response else 'None'}")
            
            # Извлекаем код из ответа
            if response and response.strip():
                code = self._extract_code_from_response(response)
                if code and code.strip():
                    return code
            
            # Второй запрос с более простым промптом
            logger.warning("First attempt failed, trying simpler prompt...")
            prompt = f"Напиши только код для: {request}\n\n```python\n"
            
            response = self.ollama_client.generate(prompt)
            logger.info(f"Second Ollama response: {response[:200] if response else 'None'}")
            
            if response and response.strip():
                code = self._extract_code_from_response(response)
                if code and code.strip():
                    return code
            
            # Третий запрос - максимально простой
            logger.warning("Second attempt failed, trying minimal prompt...")
            prompt = f"Python код для {request}:"
            
            response = self.ollama_client.generate(prompt)
            if response and response.strip():
                code = self._extract_code_from_response(response)
                if code and code.strip():
                    return code
            
            logger.error("All attempts to generate code failed")
            return None
            
        except Exception as e:
            logger.error(f"Error generating code with Ollama: {e}")
            return None
    
    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Извлекает код из ответа Ollama"""
        if not response or not response.strip():
            return None
        
        # Ищем блок ```python
        if '```python' in response:
            start = response.find('```python') + 9
            end = response.find('```', start)
            if end != -1:
                code = response[start:end].strip()
                if self._validate_python_code(code):
                    return code
        
        # Если есть ```python но нет закрывающего ```
        if '```python' in response and '```' not in response[response.find('```python')+9:]:
            start = response.find('```python') + 9
            code = response[start:].strip()
            
            # Исправляем обрезанный код
            lines = code.split('\n')
            if lines and lines[0].startswith('    '):
                first_line = lines[0].lstrip()
                if first_line.startswith('response') or first_line.startswith('soup'):
                    code = f"def get_articles(url):\n    response = requests.get(url)\n" + code
            
            # Добавляем импорты если нужно
            if code and 'import' not in code:
                code = "import requests\nfrom bs4 import BeautifulSoup\n\n" + code
            
            return code
        
        # Ищем блок ```` (CodeLlama формат)
        if '````' in response:
            lines = response.split('\n')
            code_lines = []
            in_code_block = False
            
            for line in lines:
                if line.strip().startswith('````'):
                    in_code_block = not in_code_block
                    continue
                elif in_code_block:
                    code_lines.append(line)
            
            if code_lines:
                code = '\n'.join(code_lines).strip()
                if self._validate_python_code(code):
                    return code
        
        # Если ответ содержит import statements - это код
        if 'import ' in response or 'def ' in response:
            lines = response.split('\n')
            code_lines = []
            for line in lines:
                if line.strip() and not line.startswith('#') and not line.startswith('//'):
                    code_lines.append(line)
            
            if code_lines:
                code = '\n'.join(code_lines).strip()
                return code
        
        return None
    
    def _validate_python_code(self, code: str) -> bool:
        """Проверяет базовый синтаксис Python кода"""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
    
    def _extract_code_from_description(self, description) -> str:
        """Извлекает чистый код из описания"""
        # Проверяем тип и преобразуем в строку если нужно
        if not isinstance(description, str):
            description = str(description)
        
        if ':' in description:
            parts = description.split(':', 1)
            if len(parts) > 1:
                code = parts[1].strip()
                # Удаляем лишние префиксы
                for prefix in ['код ', 'code ', 'программу ']:
                    if code.lower().startswith(prefix):
                        code = code[len(prefix):].strip()
                return code
        return description.strip()
    
    def _summarize_search_results(self, search_data: Dict[str, Any]) -> str:
        """Суммаризирует результаты поиска"""
        try:
            heading = search_data.get("Heading", "")
            abstract = search_data.get("AbstractText", "")
            abstract_url = search_data.get("AbstractURL", "")
            related = search_data.get("RelatedTopics", [])
            
            # Собираем ссылки
            links = []
            if isinstance(related, list):
                for item in related:
                    if isinstance(item, dict) and "FirstURL" in item and "Text" in item:
                        links.append(f"- {item.get('Text')} -> {item.get('FirstURL')}")
                    elif isinstance(item, dict) and isinstance(item.get("Topics"), list):
                        for sub in item.get("Topics"):
                            if isinstance(sub, dict) and "FirstURL" in sub and "Text" in sub:
                                links.append(f"- {sub.get('Text')} -> {sub.get('FirstURL')}")
            
            # Формируем промпт для суммаризации
            prompt = SUMMARIZER_PROMPT_TEMPLATE.format(
                heading=heading,
                abstract=abstract,
                abstract_url=abstract_url,
                links='\\n'.join(links[:5])
            )
            
            # Используем Ollama для суммаризации
            summary = self.ollama_client.generate(prompt)
            if summary:
                return summary
            else:
                return self._fallback_summary(search_data)
                
        except Exception as e:
            logger.error(f"Error summarizing search results: {e}")
            return self._fallback_summary(search_data)
    
    def _fallback_summary(self, raw_data: dict) -> str:
        """Простая суммаризация без Ollama"""
        heading = raw_data.get("Heading", "Информация")
        abstract = raw_data.get("AbstractText", "")
        
        if abstract:
            # Обрезаем до 200 символов
            if len(abstract) > 200:
                abstract = abstract[:200] + "..."
            return f"**{heading}**\\n\\n{abstract}"
        else:
            return f"**{heading}**\\n\\nИнформация найдена, но подробности недоступны."
    
    def _reflect_on_failure(self, step: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Рефлексия над неудачным выполнением шага"""
        try:
            error_msg = result.get('error', '').lower()
            tool_name = step.get('tool', '')
            
            # Анализируем тип ошибки и предлагаем решение
            if 'timeout' in error_msg or 'время' in error_msg:
                return {
                    'should_retry': True, 
                    'adjustment': 'Increase timeout',
                    'corrected_step': {
                        **step,
                        'parameters': {
                            **step.get('parameters', {}),
                            'timeout': step.get('parameters', {}).get('timeout', 30) + 30
                        }
                    }
                }
            elif 'network' in error_msg or 'сеть' in error_msg or 'connection' in error_msg:
                return {
                    'should_retry': True,
                    'adjustment': 'Use local resources',
                    'corrected_step': {
                        **step,
                        'parameters': {
                            **step.get('parameters', {}),
                            'use_local': True
                        }
                    }
                }
            elif 'permission' in error_msg or 'доступ' in error_msg or 'forbidden' in error_msg:
                return {
                    'should_retry': False,
                    'adjustment': 'Check permissions or use alternative approach',
                    'lesson': f'Permission error for tool {tool_name}'
                }
            elif 'not found' in error_msg or 'не найдено' in error_msg:
                return {
                    'should_retry': True,
                    'adjustment': 'Use fallback method',
                    'corrected_step': {
                        **step,
                        'parameters': {
                            **step.get('parameters', {}),
                            'fallback': True
                        }
                    }
                }
            else:
                # Для других ошибок
                return {
                    'should_retry': False,
                    'adjustment': 'Manual intervention required',
                    'lesson': f'Unknown error: {error_msg}'
                }
                
        except Exception as e:
            logger.error(f"Error in reflection: {e}")
            return {'should_retry': False, 'adjustment': 'Reflection failed'}
    
    def evaluate_execution(self, instruction: str, result: Dict[str, Any], feedback: str) -> None:
        """Оценивает выполнение и сохраняет для улучшения"""
        try:
            # Оценка на основе feedback
            evaluation = {
                'instruction': instruction,
                'result': result,
                'feedback': feedback,
                'timestamp': time.time(),
                'success_score': 1.0 if feedback.lower() in ['good', 'отлично'] else 0.5
            }
            
            # Сохраняем в SelfImprovementSystem
            if hasattr(self, 'self_improvement'):
                self.self_improvement.add_evaluation(evaluation)
                
                # Генерируем урок из результата
                if hasattr(self, 'ollama_client'):
                    try:
                        lesson_prompt = f"Из этой задачи извлеки главный урок: {str(result)[:200]}"
                        lesson = self.ollama_client.generate(lesson_prompt)
                        if lesson:
                            self.self_improvement.add_lesson(lesson, instruction)
                    except Exception as e:
                        logger.warning(f"Failed to generate lesson: {e}")
            
            # Сохраняем оценку в память для будущего анализа
            if hasattr(self, 'memory'):
                self.memory.add_task(f"Evaluation: {instruction}", evaluation, {})
            
            logger.info(f"Execution evaluated: {feedback}")
        except Exception as e:
            logger.error(f"Error in evaluation: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику работы агента"""
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for h in self.execution_history 
                                 if h.get('result', {}).get('success', False))
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
            'memory_size': len(self.memory.instructions) if hasattr(self.memory, 'instructions') else len(self.memory.memory),
            'available_tools': list(self.tools.keys())
        }
    
    def save_state(self) -> None:
        """Сохраняет состояние агента"""
        try:
            self.memory.save_memory()
            logger.info("Agent state saved")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def load_state(self) -> None:
        """Загружает состояние агента"""
        try:
            self.memory.load_memory()
            logger.info("Agent state loaded")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
