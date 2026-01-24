#!/usr/bin/env python3
"""Тестирование улучшенного агента v2"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from universal_agent_v2 import UniversalAgent

def test_code_execution():
    """Тестируем выполнение кода"""
    print("🧪 Тестирование code_execution...")
    
    agent = UniversalAgent(enable_local_env=True)
    
    # Тест 1: Генерация кода из запроса
    print("\n1. Тест генерации кода:")
    result = agent.execute_instruction("напиши код, который выводит числа от 1 до 5")
    print(f"Success: {result['success']}")
    if result['results']:
        print(f"Result: {result['results'][0]}")
    
    # Тест 2: Прямое выполнение кода
    print("\n2. Тест прямого выполнения:")
    result = agent.execute_instruction("запусти код: print('Hello, World!')")
    print(f"Success: {result['success']}")
    if result['results']:
        print(f"Result: {result['results'][0]}")
    
    # Тест 3: Математические операции
    print("\n3. Тест математики:")
    result = agent.execute_instruction("выполни код: x = 10; y = 20; print(f'x + y = {x + y}')")
    print(f"Success: {result['success']}")
    if result['results']:
        print(f"Result: {result['results'][0]}")
    
    # Тест 4: Поиск (должен использовать web_search)
    print("\n4. Тест поиска:")
    result = agent.execute_instruction("найди информацию о Python")
    print(f"Success: {result['success']}")
    print(f"Task type: {result['plan']['task_type']}")

def test_tool_validation():
    """Тестируем валидацию инструментов"""
    print("\n🔧 Тестирование валидации инструментов...")
    
    agent = UniversalAgent(enable_local_env=True)
    planner = agent.planner
    
    # Проверка валидных инструментов
    valid_tools = ['web_search', 'code_execution', 'file_operations']
    for tool in valid_tools:
        print(f"✅ {tool}: {planner.validate_tool(tool)}")
    
    # Проверка невалидных инструментов
    invalid_tools = ['fake_tool', 'hack_tool', 'malicious_tool']
    for tool in invalid_tools:
        print(f"❌ {tool}: {planner.validate_tool(tool)}")

def test_summarization():
    """Тестируем суммаризацию"""
    print("\n📄 Тестирование суммаризации...")
    
    from universal_agent_v2 import Summarizer
    
    # Тестовые данные
    test_data = {
        "Heading": "Python Programming",
        "AbstractText": "Python is a high-level programming language",
        "AbstractURL": "https://python.org",
        "RelatedTopics": [
            {"Text": "Python Tutorial", "FirstURL": "https://docs.python.org"},
            {"Text": "Python Downloads", "FirstURL": "https://python.org/downloads"}
        ]
    }
    
    summary = Summarizer.summarize_search_data(test_data)
    print("Суммаризация:")
    print(summary)

if __name__ == "__main__":
    print("🚀 Запуск тестов агента v2")
    print("=" * 50)
    
    try:
        test_code_execution()
        test_tool_validation()
        test_summarization()
        print("\n✅ Все тесты завершены!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
