#!/usr/bin/env python3
"""
Тестирование полноценного генератора сайтов
"""

from universal_agent import UniversalAgent

def test_create_full_website():
    """Тестирует создание полноценного сайта"""
    print("🚀 Тестирование создания полноценного сайта...")
    
    # Создаем агента
    agent = UniversalAgent(enable_local_env=True)
    
    # Тестируем создание сайта
    try:
        result = agent.create_full_website(
            theme="technology",
            pages_count=5,
            framework="bootstrap"
        )
        
        if result.get('success'):
            print("✅ Сайт успешно создан!")
            print(f"📁 Папка: {result.get('site_path')}")
            print(f"📄 Страниц: {result.get('pages_count')}")
            print(f"🎨 Фреймворк: {result.get('framework')}")
            print(f"🌐 Сервер: {result.get('server_url')}")
            print(f"📋 Статус: {result.get('status')}")
            
            print("\n📄 Созданные страницы:")
            for page in result.get('generated_pages', []):
                print(f"  - {page}")
                
            return True
        else:
            print(f"❌ Ошибка создания сайта: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при создании сайта: {e}")
        return False

def test_planner():
    """Тестирует планировщик"""
    print("\n🧠 Тестирование планировщика...")
    
    agent = UniversalAgent(enable_local_env=True)
    
    # Тестовые команды
    test_commands = [
        "создай полноценный сайт-магазин гаджетов",
        "полноценный многостраничный сайт про технологии",
        "создай сайт-магазин с каталогом",
        "многостраничный сайт с блогом"
    ]
    
    for cmd in test_commands:
        print(f"\n🔍 Тест команды: '{cmd}'")
        plan = agent.planner.create_plan(cmd)
        
        if plan.get('task_type') == 'full_website':
            print("✅ Распознано как полноценный сайт!")
            steps = plan.get('steps', [])
            if steps:
                step = steps[0]
                print(f"  🛠️ Инструмент: {step.get('tool')}")
                print(f"  📝 Описание: {step.get('description')}")
                params = step.get('parameters', {})
                print(f"  🎨 Тема: {params.get('theme')}")
                print(f"  📄 Страниц: {params.get('pages_count')}")
                print(f"  ⚙️ Фреймворк: {params.get('framework')}")
        else:
            print(f"❌ Не распознано. Тип: {plan.get('task_type')}")

if __name__ == "__main__":
    print("🧪 Запуск тестов полноценного генератора сайтов\n")
    
    # Тестируем планировщик
    test_planner()
    
    # Тестируем создание сайта
    success = test_create_full_website()
    
    print(f"\n📊 Результат тестов: {'✅ УСПЕХ' if success else '❌ НЕУДАЧА'}")
    
    if success:
        print("\n🎉 Полноценный генератор сайтов работает корректно!")
        print("💡 Используйте GUI или CLI для создания сайтов")
