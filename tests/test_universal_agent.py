"""
Unit тесты для универсального агента
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавляем путь к модулю
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from universal_agent import (
    ExtendedLocalEnv, 
    TaskPlanner, 
    UniversalAgent,
    AGENT_S_AVAILABLE
)


class TestExtendedLocalEnv(unittest.TestCase):
    """Тесты для ExtendedLocalEnv"""
    
    def setUp(self):
        self.env = ExtendedLocalEnv()
    
    def test_web_search(self):
        """Тест веб-поиска"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"test": "data"}
            mock_get.return_value = mock_response
            
            result = self.env.web_search("python")
            
            self.assertTrue(result['success'])
            self.assertEqual(result['query'], "python")
            mock_get.assert_called_once()
    
    def test_file_operations_read(self):
        """Тест чтения файла"""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_file.read.return_value = "test content"
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = self.env.file_operations('read', 'test.txt')
            
            self.assertTrue(result['success'])
            self.assertEqual(result['data'], "test content")
    
    def test_file_operations_write(self):
        """Тест записи файла"""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = self.env.file_operations('write', 'test.txt', 'content')
            
            self.assertTrue(result['success'])
            mock_file.write.assert_called_once_with('content')
    
    def test_system_info(self):
        """Тест системной информации"""
        result = self.env.system_info()
        
        self.assertTrue(result['success'])
        self.assertIn('platform', result['data'])
        self.assertIn('python_version', result['data'])
    
    def test_email_operations(self):
        """Тест email операций"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            result = self.env.email_operations(
                'send',
                to='test@example.com',
                subject='Test',
                body='Test body',
                username='user',
                password='pass'
            )
            
            self.assertTrue(result['success'])
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    def test_image_processing(self):
        """Тест обработки изображений"""
        with patch('PIL.Image.open') as mock_open:
            mock_image = Mock()
            mock_image.width = 100
            mock_image.height = 100
            mock_open.return_value = mock_image
            
            result = self.env.image_processing('resize', 'test.jpg', width=200, height=200)
            
            self.assertTrue(result['success'])
            mock_image.resize.assert_called_once_with((200, 200))
    
    def test_async_operations(self):
        """Тест асинхронных операций"""
        async def test_async():
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.json.return_value = {"test": "data"}
                mock_get.return_value = mock_response
                
                result = await self.env.async_operations(
                    'parallel_search',
                    queries=['python', 'java']
                )
                
                self.assertTrue(result['success'])
                self.assertEqual(len(result['results']), 2)
        
        # Запускаем асинхронный тест
        asyncio.run(test_async())
    
    def test_twitter_operations(self):
        """Тест Twitter операций"""
        with patch('tweepy.OAuthHandler') as mock_auth, \
             patch('tweepy.API') as mock_api:
            
            mock_api_instance = Mock()
            mock_api.return_value = mock_api_instance
            
            # Тест отправки твита
            mock_tweet = Mock()
            mock_tweet.id = 12345
            mock_tweet.text = "Test tweet"
            mock_api_instance.update_status.return_value = mock_tweet
            
            result = self.env.twitter_operations(
                'tweet',
                api_key='test_key',
                api_secret='test_secret',
                access_token='test_token',
                access_token_secret='test_token_secret',
                text='Test tweet'
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['tweet_id'], 12345)
    
    def test_image_processing_with_url(self):
        """Тест обработки изображений с URL"""
        with patch('requests.get') as mock_get, \
             patch('PIL.Image.open') as mock_open:
            
            # Mock ответа от URL
            mock_response = Mock()
            mock_response.content = b'fake_image_data'
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Mock изображения
            mock_image = Mock()
            mock_image.width = 100
            mock_image.height = 100
            mock_open.return_value = mock_image
            
            result = self.env.image_processing(
                'resize',
                image_url='https://example.com/image.jpg',
                width=200,
                height=200
            )
            
            self.assertTrue(result['success'])
            mock_get.assert_called_once_with('https://example.com/image.jpg', timeout=10)
            mock_image.resize.assert_called_once_with((200, 200))


class TestTaskPlanner(unittest.TestCase):
    """Тесты для TaskPlanner"""
    
    def setUp(self):
        self.mock_engine = Mock()
        self.planner = TaskPlanner(self.mock_engine)
    
    def test_create_plan_with_engine(self):
        """Тест создания плана с engine"""
        self.mock_engine.generate.return_value = '{"task_type": "gui", "steps": []}'
        
        result = self.planner.create_plan("открой калькулятор")
        
        self.assertEqual(result['task_type'], 'gui')
        self.mock_engine.generate.assert_called_once()
    
    def test_create_plan_json_error(self):
        """Тест обработки JSON ошибки"""
        self.mock_engine.generate.return_value = 'invalid json'
        
        result = self.planner.create_plan("test instruction")
        
        # Должен использовать fallback план
        self.assertEqual(result['task_type'], 'code')
    
    def test_create_plan_no_engine(self):
        """Тест создания плана без engine"""
        planner = TaskPlanner(None)
        
        result = planner.create_plan("открой калькулятор")
        
        self.assertEqual(result['task_type'], 'gui')
    
    def test_fallback_plan_patterns(self):
        """Тест различных паттернов fallback плана"""
        planner = TaskPlanner(None)
        
        # GUI действия
        result = planner._fallback_plan("открой калькулятор")
        self.assertEqual(result['task_type'], 'gui')
        
        # Поиск
        result = planner._fallback_plan("найди информацию о python")
        self.assertEqual(result['task_type'], 'search')
        
        # Файлы
        result = planner._fallback_plan("создай файл test.txt")
        self.assertEqual(result['task_type'], 'file')
        
        # Email
        result = planner._fallback_plan("отправь email")
        self.assertEqual(result['task_type'], 'email')
        
        # Изображения
        result = planner._fallback_plan("измени размер картинки")
        self.assertEqual(result['task_type'], 'image')
        
        # Система
        result = planner._fallback_plan("покажи информацию о системе")
        self.assertEqual(result['task_type'], 'system')
        
        # Twitter
        result = planner._fallback_plan("отправь твит")
        self.assertEqual(result['task_type'], 'twitter')
    
    def test_extract_search_query(self):
        """Тест извлечения поискового запроса"""
        planner = TaskPlanner(None)
        
        query = planner._extract_search_query("найди информацию о python")
        self.assertEqual(query, "python")
        
        query = planner._extract_search_query("search machine learning")
        self.assertEqual(query, "machine learning")
        
        query = planner._extract_search_query("google weather forecast")
        self.assertEqual(query, "weather forecast")
    
    def test_extract_file_parameters(self):
        """Тест извлечения файловых параметров"""
        planner = TaskPlanner(None)
        
        # Тест создания файла
        params = planner._extract_file_parameters("создай файл test.txt с текстом 'Hello World'")
        self.assertEqual(params['operation'], 'write')
        self.assertEqual(params['path'], 'test.txt')
        self.assertEqual(params['content'], 'Hello World')
        
        # Тест чтения файла
        params = planner._extract_file_parameters("прочитай файл data.json")
        self.assertEqual(params['operation'], 'read')
        self.assertEqual(params['path'], 'data.json')
        
        # Тест с кавычками
        params = planner._extract_file_parameters("создай 'my document.txt' с текстом 'Important data'")
        self.assertEqual(params['operation'], 'write')
        self.assertEqual(params['path'], 'my document.txt')
        self.assertEqual(params['content'], 'Important data')


class TestUniversalAgent(unittest.TestCase):
    """Тесты для UniversalAgent"""
    
    def setUp(self):
        self.mock_engine = Mock()
        self.agent = UniversalAgent(
            engine=self.mock_engine,
            enable_local_env=True,
            enable_reflection=False  # Отключаем рефлексию для простоты тестов
        )
    
    def test_initialization(self):
        """Тест инициализации"""
        self.assertIsNotNone(self.agent.local_env)
        self.assertIsNotNone(self.agent.planner)
        self.assertEqual(self.agent.engine, self.mock_engine)
    
    def test_execute_instruction_success(self):
        """Тест успешного выполнения инструкции"""
        with patch.object(self.agent, '_execute_step') as mock_execute:
            mock_execute.return_value = {'success': True}
            
            result = self.agent.execute_instruction("открой калькулятор")
            
            self.assertTrue(result['success'])
            self.assertIn('plan', result)
            self.assertIn('results', result)
    
    def test_execute_instruction_with_reflection(self):
        """Тест выполнения инструкции с рефлексией"""
        agent = UniversalAgent(
            engine=self.mock_engine,
            enable_local_env=True,
            enable_reflection=True
        )
        
        with patch.object(agent, '_execute_step') as mock_execute:
            # Первый вызов - неудача
            mock_execute.return_value = {'success': False, 'error': 'Test error'}
            
            with patch.object(agent, '_reflect_on_execution') as mock_reflect:
                mock_reflect.return_value = {'needs_retry': False}
                
                result = agent.execute_instruction("test instruction")
                
                self.assertFalse(result['success'])
                mock_reflect.assert_called_once()
    
    def test_execute_gui_action(self):
        """Тест выполнения GUI действия"""
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.return_value = Mock()
            
            result = self.agent._execute_gui_action("открой калькулятор")
            
            self.assertTrue(result['success'])
            mock_popen.assert_called_once()
    
    def test_execute_code_safe(self):
        """Тест безопасного выполнения кода"""
        with patch('universal_agent.compile_restricted') as mock_compile:
            mock_code = Mock()
            mock_compile.return_value = mock_code
            
            with patch('builtins.exec') as mock_exec:
                result = self.agent._execute_code("print('test')")
                
                self.assertTrue(result['success'])
                mock_compile.assert_called_once()
                mock_exec.assert_called_once()
    
    def test_cross_platform_gui_actions(self):
        """Тест кросс-платформенных GUI действий"""
        platforms = ['windows', 'darwin', 'linux']
        
        for platform_name in platforms:
            with patch('platform.system', return_value=platform_name.capitalize()):
                with patch('subprocess.Popen') as mock_popen:
                    mock_popen.return_value = Mock()
                    
                    result = self.agent._open_calculator()
                    
                    self.assertTrue(result['success'])
                    mock_popen.assert_called_once()
    
    def test_reflection_with_llm(self):
        """Тест рефлексии с LLM"""
        agent = UniversalAgent(
            engine=self.mock_engine,
            enable_local_env=True,
            enable_reflection=True
        )
        
        # Настраиваем mock engine
        self.mock_engine.generate.return_value = '''
        {
            "corrected_instruction": "исправленная инструкция",
            "reasoning": "анализ ошибки",
            "needs_retry": true
        }
        '''
        
        failed_results = [{'success': False, 'error': 'Test error'}]
        
        result = agent._reflect_on_execution("test instruction", failed_results)
        
        self.assertTrue(result['needs_retry'])
        self.assertEqual(result['corrected_instruction'], 'исправленная инструкция')
        self.assertEqual(result['reasoning'], 'анализ ошибки')
    
    def test_reflection_with_api_key(self):
        """Тест рефлексии с OpenAI API ключом"""
        agent = UniversalAgent(
            engine=None,
            enable_local_env=True,
            enable_reflection=True,
            api_key='test-api-key'
        )
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '''
            {
                "corrected_instruction": "исправленная инструкция",
                "reasoning": "анализ ошибки",
                "needs_retry": true
            }
            '''
            mock_client.chat.completions.create.return_value = mock_response
            
            failed_results = [{'success': False, 'error': 'Test error'}]
            
            result = agent._reflect_on_execution("test instruction", failed_results)
            
            self.assertTrue(result['needs_retry'])
            self.assertEqual(result['corrected_instruction'], 'исправленная инструкция')
    
    def test_async_execution(self):
        """Тест асинхронного выполнения"""
        agent = UniversalAgent(
            engine=self.mock_engine,
            enable_local_env=True,
            enable_reflection=False
        )
        
        async def test_async():
            with patch.object(agent, '_execute_step_async') as mock_execute:
                mock_execute.return_value = {'success': True}
                
                result = await agent.execute_instruction_async("test instruction")
                
                self.assertTrue(result['success'])
                mock_execute.assert_called()
        
        # Запускаем асинхронный тест
        asyncio.run(test_async())
    
    def test_execution_history_clear(self):
        """Тест очистки истории после успешного выполнения"""
        agent = UniversalAgent(
            engine=self.mock_engine,
            enable_local_env=True,
            enable_reflection=False
        )
        
        # Добавляем что-то в историю
        agent.execution_history.append({'test': 'data'})
        
        with patch.object(agent, '_execute_step') as mock_execute:
            mock_execute.return_value = {'success': True}
            
            result = agent.execute_instruction("test instruction")
            
            # История должна очиститься после успешного выполнения
            self.assertEqual(len(agent.execution_history), 0)
            self.assertTrue(result['success'])
    
    def test_twitter_operations_integration(self):
        """Тест интеграции Twitter операций"""
        agent = UniversalAgent(
            engine=self.mock_engine,
            enable_local_env=True,
            enable_reflection=False
        )
        
        with patch.object(agent.local_env, 'twitter_operations') as mock_twitter:
            mock_twitter.return_value = {'success': True, 'tweet_id': 12345}
            
            step = {
                'tool': 'twitter_operations',
                'parameters': {
                    'operation': 'tweet',
                    'api_key': 'test_key',
                    'text': 'Test tweet'
                }
            }
            
            result = agent._execute_step(step)
            
            self.assertTrue(result['success'])
            mock_twitter.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""
    
    def setUp(self):
        self.agent = UniversalAgent(enable_local_env=True, enable_reflection=False)
    
    def test_full_workflow(self):
        """Тест полного рабочего процесса"""
        # Тестируем различные типы задач
        instructions = [
            "открой калькулятор",
            "найди информацию о python",
            "создай тестовый файл",
            "покажи информацию о системе"
        ]
        
        for instruction in instructions:
            result = self.agent.execute_instruction(instruction)
            
            # Проверяем базовую структуру результата
            self.assertIn('success', result)
            self.assertIn('plan', result)
            self.assertIn('results', result)
            self.assertIn('instruction', result)


if __name__ == '__main__':
    # Запуск тестов
    unittest.main(verbosity=2)
