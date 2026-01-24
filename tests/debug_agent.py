#!/usr/bin/env python3
"""
Отладка новой структуры агента
"""

import sys
import os
sys.path.append('.')

from agent import UniversalAgent

def debug_agent():
    """Отладка агента"""
    print("🔍 Отладка новой структуры агента...")
    
    try:
        # Инициализируем агента
        agent = UniversalAgent()
        
        print("\n🔧 Проверка local_env:")
        if agent.local_env:
            print(f"✅ Local env доступен")
            print(f"📊 Количество инструментов: {len(agent.local_env.tools)}")
            print(f"📋 Список инструментов: {list(agent.local_env.tools.keys())}")
        else:
            print("❌ Local env не доступен")
            return
        
        print("\n🎯 Тестирование get_tool:")
        test_tools = ['create_full_website', 'ask_grok', 'code_execution']
        for tool in test_tools:
            tool_func = agent.local_env.get_tool(tool)
            if tool_func:
                print(f"✅ {tool}: доступен")
            else:
                print(f"❌ {tool}: не найден")
        
        print("\n📝 Тестирование планировщика:")
        plan = agent.planner.create_plan("создай сайт")
        print(f"📊 План: {plan}")
        
        if plan.get('steps'):
            step = plan['steps'][0]
            tool_name = step.get('tool')
            print(f"🔧 Инструмент в плане: {tool_name}")
            
            tool_func = agent.local_env.get_tool(tool_name)
            if tool_func:
                print(f"✅ Инструмент найден в local_env")
                
                # Пробуем выполнить
                print(f"🚀 Пробуем выполнить инструмент...")
                try:
                    result = tool_func(**step.get('parameters', {}))
                    print(f"✅ Результат: {result.get('success', False)}")
                except Exception as e:
                    print(f"❌ Ошибка выполнения: {e}")
            else:
                print(f"❌ Инструмент не найден в local_env")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_agent()
