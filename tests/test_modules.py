"""
Модульные тесты для Universal Agent
"""

import unittest
import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestUtils(unittest.TestCase):
    """Тесты утилит"""
    
    def setUp(self):
        from agent.utils import setup_logging
        setup_logging("DEBUG")  # Включаем логи для тестов
    
    def test_clean_instruction(self):
        """Тест очистки инструкций"""
        from agent.utils import clean_instruction
        
        # Тест удаления "Similar past tasks"
        instruction = "Напиши код\\n\\nSimilar past tasks:\\n- старая задача"
        cleaned = clean_instruction(instruction)
        self.assertNotIn("Similar past tasks", cleaned)
        self.assertIn("Напиши код", cleaned)
        
        # Тест удаления префиксов
        instruction = "Please напиши код"
        cleaned = clean_instruction(instruction)
        self.assertEqual(cleaned, "напиши код")
    
    def test_is_programming_task(self):
        """Тест определения программных задач"""
        from agent.utils import is_programming_task
        
        self.assertTrue(is_programming_task("напиши код на Python"))
        self.assertTrue(is_programming_task("создай функцию"))
        self.assertTrue(is_programming_task("запусти скрипт"))
        self.assertFalse(is_programming_task("найди информацию"))
        self.assertFalse(is_programming_task("какая погода"))
    
    def test_is_search_task(self):
        """Тест определения поисковых задач"""
        from agent.utils import is_search_task
        
        self.assertTrue(is_search_task("найди информацию о AI"))
        self.assertTrue(is_search_task("поиск данных"))
        self.assertTrue(is_search_task("ищи новости"))
        self.assertFalse(is_search_task("напиши код"))
        self.assertFalse(is_search_task("создай файл"))

class TestPlanner(unittest.TestCase):
    """Тесты планировщика"""
    
    def setUp(self):
        from agent.planner import TaskPlanner
        self.planner = TaskPlanner()
    
    def test_create_code_plan(self):
        """Тест создания плана для кода"""
        plan = self.planner._create_code_plan("напиши код приветствия")
        
        self.assertEqual(plan['task_type'], 'code')
        self.assertEqual(len(plan['steps']), 1)
        self.assertEqual(plan['steps'][0]['tool'], 'code_execution')
    
    def test_create_search_plan(self):
        """Тест создания плана для поиска"""
        plan = self.planner._create_search_plan("найди информацию о Python")
        
        self.assertEqual(plan['task_type'], 'search')
        self.assertEqual(len(plan['steps']), 1)
        self.assertEqual(plan['steps'][0]['tool'], 'tavily_search')
    
    def test_validate_plan(self):
        """Тест валидации плана"""
        valid_plan = {
            'task_type': 'code',
            'steps': [{'tool': 'code_execution', 'description': 'test'}]
        }
        self.assertTrue(self.planner.validate_plan(valid_plan))
        
        invalid_plan = {
            'task_type': 'code',
            'steps': [{'tool': 'unknown_tool', 'description': 'test'}]
        }
        self.assertFalse(self.planner.validate_plan(invalid_plan))

class TestMemory(unittest.TestCase):
    """Тесты памяти"""
    
    def setUp(self):
        from agent.memory import AgentMemory
        # Используем временную память для тестов
        self.memory = AgentMemory(persist_path="test_memory", memory_size=10)
    
    def tearDown(self):
        # Очищаем тестовые файлы
        import shutil
        test_files = ["test_memory.pkl", "test_memory.faiss"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
    
    def test_add_task(self):
        """Тест добавления задачи"""
        result = {'success': True, 'data': 'test'}
        plan = {'task_type': 'test', 'steps': []}
        
        initial_count = len(self.memory.instructions)
        self.memory.add_task("test instruction", result, plan)
        
        self.assertEqual(len(self.memory.instructions), initial_count + 1)
    
    def test_recall_similar(self):
        """Тест поиска похожих задач"""
        # Добавляем тестовые задачи
        self.memory.add_task("напиши код", {}, {})
        self.memory.add_task("создай функцию", {}, {})
        
        similar = self.memory.recall_similar("напиши скрипт")
        self.assertGreater(len(similar), 0)

class TestTools(unittest.TestCase):
    """Тесты инструментов"""
    
    def setUp(self):
        from agent.tools import ExtendedLocalEnv
        self.env = ExtendedLocalEnv()
    
    def test_tool_registration(self):
        """Тест регистрации инструментов"""
        tools = self.env.list_tools()
        self.assertIn('tavily_search', tools)
        self.assertIn('code_execution', tools)
        self.assertIn('file_operations', tools)
    
    def test_code_execution(self):
        """Тест выполнения кода"""
        result = self.env.code_execution('print("hello world")')
        self.assertTrue(result['success'])
        self.assertIn('hello world', result['output'])

def run_tests():
    """Запускает все тесты"""
    # Создаем тестовый набор
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    test_classes = [TestUtils, TestPlanner, TestMemory, TestTools]
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Запускаем
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем результат
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
