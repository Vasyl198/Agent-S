#!/usr/bin/env python3
"""
Прямой тест Grok функциональности
"""

from universal_agent import UniversalAgent

def test_grok_direct():
    """Тестируем Grok напрямую"""
    print("🧪 Прямой тест Grok функциональности")
    print("=" * 50)
    
    # Создаем агента
    agent = UniversalAgent(enable_local_env=True)
    
    print("\n1️⃣ Тест ask_grok...")
    try:
        result = agent.ask_grok("Как создать простой веб-сайт?")
        print(f"✅ ask_grok: {result.get('success', False)}")
        if result.get('success'):
            print(f"📝 Ответ: {result.get('answer', 'N/A')[:100]}...")
        else:
            print(f"❌ Ошибка: {result.get('error', 'N/A')}")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    print("\n2️⃣ Тест learn_from_grok...")
    try:
        result = agent.learn_from_grok("создание игр на Python")
        print(f"✅ learn_from_grok: {result.get('success', False)}")
        if result.get('success'):
            print(f"📁 Файл: {result.get('filename', 'N/A')}")
            print(f"📝 Код создан: {len(result.get('generated_code', ''))} символов")
            print(f"🚀 Запуск: {result.get('execution_result', {}).get('success', False)}")
        else:
            print(f"❌ Ошибка: {result.get('error', 'N/A')}")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    print("\n3️⃣ Проверка зарегистрированных инструментов...")
    tools = agent.tools
    grok_tools = [name for name in tools.keys() if 'grok' in name]
    print(f"🔧 Найдено Grok инструментов: {grok_tools}")
    
    if len(grok_tools) >= 2:
        print("✅ Все Grok инструменты зарегистрированы!")
    else:
        print("❌ Не все Grok инструменты зарегистрированы")
    
    print("\n" + "=" * 50)
    print("🎉 Тест завершен!")

if __name__ == "__main__":
    test_grok_direct()
