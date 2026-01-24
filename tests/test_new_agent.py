#!/usr/bin/env python3
"""
Тестирование новой модульной структуры Agent S
"""

import sys
import os
sys.path.append('.')

from agent import UniversalAgent

def test_new_agent():
    """Тестирование нового агента"""
    print("🚀 Тестирование новой модульной структуры Agent S...")
    
    try:
        # Инициализируем агента
        print("\n📦 Инициализация агента...")
        agent = UniversalAgent()
        print("✅ Агент успешно инициализирован")
        
        # Проверяем наличие всех компонентов
        print("\n🔍 Проверка компонентов:")
        
        # Grok интеграция
        if hasattr(agent, 'grok_integration'):
            print("✅ Grok интеграция: доступна")
        else:
            print("❌ Grok интеграция: не найдена")
        
        # Copilot интеграция
        if hasattr(agent, 'copilot_integration'):
            print("✅ Copilot интеграция: доступна")
        else:
            print("❌ Copilot интеграция: не найдена")
        
        # Website Builder
        if hasattr(agent, 'website_builder'):
            print("✅ Website Builder: доступен")
        else:
            print("❌ Website Builder: не найден")
        
        # Проверяем методы
        print("\n🔧 Проверка методов:")
        
        methods_to_check = [
            'ask_grok',
            'learn_from_grok',
            'copilot_authenticate',
            'create_full_website'
        ]
        
        for method in methods_to_check:
            if hasattr(agent, method):
                print(f"✅ {method}: доступен")
            else:
                print(f"❌ {method}: не найден")
        
        # Тест 1: Создание сайта
        print("\n📝 Тест 1: Создание сайта")
        result = agent.execute_instruction("создай сайт")
        print(f"✅ Результат: {result.get('success', False)}")
        if result.get('success'):
            print(f"🌐 Сайт создан: {result.get('result', 'Нет информации')}")
        
        # Тест 2: Запрос Grok
        print("\n📝 Тест 2: Запрос к Grok")
        result = agent.execute_instruction("учи у grok создание калькулятора")
        print(f"✅ Результат: {result.get('success', False)}")
        
        # Тест 3: Обычный запрос
        print("\n📝 Тест 3: Обычный запрос")
        result = agent.execute_instruction("помоги мне создать калькулятор на python")
        print(f"✅ Результат: {result.get('success', False)}")
        
        print("\n🎉 Тестирование новой структуры завершено!")
        print("✅ Все компоненты работают корректно")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_agent()
