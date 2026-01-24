#!/usr/bin/env python3
"""
Тест создания сайта
"""

import sys
import os
sys.path.append('.')

from universal_agent import UniversalAgent

def test_site_creation():
    """Тестирование создания сайта"""
    print("🚀 Тест создания сайта...")
    
    # Инициализируем агента
    agent = UniversalAgent()
    
    # Тест 1: Простая команда "создай сайт"
    print("\n📝 Тест 1: 'создай сайт'")
    result = agent.execute_instruction("создай сайт")
    print(f"✅ Результат: {result.get('success', False)}")
    print(f"📄 Ответ: {result.get('result', 'Нет ответа')[:200]}...")
    
    # Тест 2: "создай сайт о бизнесе"
    print("\n📝 Тест 2: 'создай сайт о бизнесе'")
    result = agent.execute_instruction("создай сайт о бизнесе")
    print(f"✅ Результат: {result.get('success', False)}")
    print(f"📄 Ответ: {result.get('result', 'Нет ответа')[:200]}...")
    
    # Тест 3: "создай магазин"
    print("\n📝 Тест 3: 'создай магазин'")
    result = agent.execute_instruction("создай магазин")
    print(f"✅ Результат: {result.get('success', False)}")
    print(f"📄 Ответ: {result.get('result', 'Нет ответа')[:200]}...")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_site_creation()
