#!/usr/bin/env python3
"""
Тест CLI агента с Grok
"""

import sys
import os
sys.path.append('.')

from universal_agent import UniversalAgent

def test_agent():
    """Тестирование агента"""
    print("🚀 Запуск теста Agent S CLI...")
    
    # Инициализируем агента
    agent = UniversalAgent()
    
    # Тест 1: Обычный запрос
    print("\n📝 Тест 1: Обычный запрос")
    result = agent.execute_instruction("помоги мне создать калькулятор на python")
    print(f"✅ Результат: {result.get('success', False)}")
    print(f"📄 Ответ: {result.get('result', 'Нет ответа')[:100]}...")
    
    # Тест 2: Запрос Grok на русском
    print("\n📝 Тест 2: Команда Grok на русском")
    result = agent.execute_instruction("учи у grok создание сайта")
    print(f"✅ Результат: {result.get('success', False)}")
    print(f"📄 Ответ: {result.get('result', 'Нет ответа')[:100]}...")
    
    # Тест 3: Запрос Grok на английском
    print("\n📝 Тест 3: Команда Grok на английском")
    result = agent.execute_instruction("learn from grok web development")
    print(f"✅ Результат: {result.get('success', False)}")
    print(f"📄 Ответ: {result.get('result', 'Нет ответа')[:100]}...")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_agent()
