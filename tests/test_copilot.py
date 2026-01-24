#!/usr/bin/env python3
"""
Тестирование интеграции с GitHub Copilot
"""

from universal_agent import UniversalAgent

def test_copilot_integration():
    """Тестирует интеграцию с Copilot"""
    print("🤖 Тестирование интеграции с GitHub Copilot...")
    
    # Создаем агента
    agent = UniversalAgent(enable_local_env=True)
    
    # Тест 1: Проверка доступности Copilot
    print("\n1️⃣ Тест доступности Copilot...")
    try:
        result = agent.copilot_status()
        if result.get('success'):
            print("✅ Copilot доступен")
            print(f"📊 Статус: {result.get('status', 'N/A')}")
        else:
            print(f"❌ Copilot недоступен: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки статуса: {e}")
        return False
    
    # Тест 2: Аутентификация
    print("\n2️⃣ Тест аутентификации...")
    try:
        result = agent.copilot_authenticate()
        if result.get('success'):
            print("✅ Аутентификация успешна")
            print(f"👤 Пользователь: {result.get('user_info', 'N/A')}")
        else:
            print(f"❌ Ошибка аутентификации: {result.get('error')}")
            print("💡 Убедитесь что GitHub Copilot CLI установлен и настроен")
    except Exception as e:
        print(f"❌ Ошибка аутентификации: {e}")
    
    # Тест 3: Объяснение кода
    print("\n3️⃣ Тест объяснения кода...")
    test_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
    try:
        result = agent.copilot_explain(test_code, "python")
        if result.get('success'):
            print("✅ Код успешно объяснен")
            explanation = result.get('explanation', '')
            print("📖 Объяснение:")
            for line in explanation.split('\n')[:5]:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"❌ Ошибка объяснения: {result.get('error')}")
    except Exception as e:
        print(f"❌ Ошибка объяснения кода: {e}")
    
    # Тест 4: Генерация кода
    print("\n4️⃣ Тест генерации кода...")
    try:
        result = agent.copilot_generate(
            "Создай функцию для проверки палиндрома", 
            "python"
        )
        if result.get('success'):
            print("✅ Код успешно сгенерирован")
            generated = result.get('generated_code', '')
            print("🔨 Сгенерированный код:")
            for line in generated.split('\n')[:8]:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"❌ Ошибка генерации: {result.get('error')}")
    except Exception as e:
        print(f"❌ Ошибка генерации кода: {e}")
    
    # Тест 5: Code Review
    print("\n5️⃣ Тест Code Review...")
    try:
        result = agent.copilot_review(test_code, "python")
        if result.get('success'):
            print("✅ Code Review успешно выполнен")
            review = result.get('review', '')
            print("🔍 Ревью:")
            for line in review.split('\n')[:5]:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"❌ Ошибка Code Review: {result.get('error')}")
    except Exception as e:
        print(f"❌ Ошибка Code Review: {e}")
    
    return True

def test_copilot_suggestions():
    """Тестирует предложения по улучшению кода"""
    print("\n💡 Тест предложений по улучшению кода...")
    
    agent = UniversalAgent(enable_local_env=True)
    
    # Пример кода для улучшения
    code_to_improve = '''
def calculate_sum(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    return total
'''
    
    try:
        result = agent.copilot_suggest(code_to_improve, "python", "Оптимизация производительности")
        if result.get('success'):
            print("✅ Предложения получены")
            suggestion = result.get('suggestion', '')
            print("💡 Предложения по улучшению:")
            for line in suggestion.split('\n')[:8]:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"❌ Ошибка получения предложений: {result.get('error')}")
    except Exception as e:
        print(f"❌ Ошибка предложений: {e}")

if __name__ == "__main__":
    print("🧪 Запуск тестов интеграции с GitHub Copilot\n")
    
    # Основные тесты
    success = test_copilot_integration()
    
    if success:
        # Дополнительные тесты
        test_copilot_suggestions()
        
        print(f"\n🎉 Тесты Copilot завершены!")
        print("💡 Для полноценной работы убедитесь что:")
        print("   1. GitHub Copilot CLI установлен")
        print("   2. Вы аутентифицированы в GitHub")
        print("   3. У вас есть активная подписка Copilot")
    else:
        print(f"\n❌ Тесты не пройдены")
        print("💡 Проверьте установку и настройку GitHub Copilot CLI")
