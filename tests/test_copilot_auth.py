#!/usr/bin/env python3
"""
Тест аутентификации в GitHub Copilot
"""

from universal_agent import UniversalAgent

def test_copilot_after_auth():
    """Тестируем Copilot после аутентификации"""
    print("🔐 Тест аутентификации в GitHub Copilot...")
    print("📋 Инструкция:")
    print("1. Перейдите на: https://github.com/login/device")
    print("2. Введите код: 16BC-92DE")
    print("3. Approve доступ для GitHub Copilot CLI")
    print("4. Нажмите Enter для продолжения...")
    
    input()  # Ждем завершения аутентификации
    
    # Создаем агента
    agent = UniversalAgent(enable_local_env=True)
    
    # Тестируем статус
    print("\n📊 Проверка статуса Copilot...")
    try:
        result = agent.copilot_status()
        if result.get('success'):
            print("✅ Copilot доступен!")
            print(f"📋 Статус: {result.get('status', 'N/A')}")
        else:
            print(f"❌ Copilot недоступен: {result.get('error')}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тестируем аутентификацию
    print("\n🔐 Тест аутентификации...")
    try:
        result = agent.copilot_authenticate()
        if result.get('success'):
            print("✅ Аутентификация успешна!")
            print(f"👤 Пользователь: {result.get('user_info', 'N/A')}")
            
            # Если успешно, тестируем генерацию кода
            print("\n🎮 Тест генерации игры 'Крестики-нолики'...")
            game_result = agent.copilot_generate(
                "создай простую игру крестик нолик в консоли",
                "python"
            )
            
            if game_result.get('success'):
                print("✅ Игра успешно создана!")
                print("🎮 Сгенерированный код:")
                print("=" * 50)
                
                generated_code = game_result.get('generated_code', '')
                lines = generated_code.split('\n')
                for i, line in enumerate(lines[:20], 1):
                    print(f"{i:2d}: {line}")
                
                if len(lines) > 20:
                    print(f"... и еще {len(lines) - 20} строк")
                
                print("=" * 50)
                
                # Сохраняем код
                with open('tic_tac_toe_console.py', 'w', encoding='utf-8') as f:
                    f.write(generated_code)
                print("💾 Код сохранен в: tic_tac_toe_console.py")
                print("🚀 Запустите игру: python tic_tac_toe_console.py")
                
            else:
                print(f"❌ Ошибка генерации: {game_result.get('error')}")
                
        else:
            print(f"❌ Ошибка аутентификации: {result.get('error')}")
            print("💡 Убедитесь что вы завершили аутентификацию на GitHub")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    print("🧪 Тест GitHub Copilot после аутентификации")
    print("=" * 50)
    
    test_copilot_after_auth()
    
    print("\n" + "=" * 50)
    print("🎉 Тест завершен!")
    print("💡 Теперь можно использовать Copilot в агенте:")
    print("   - CLI: спроси у copilot [запрос]")
    print("   - GUI: кнопка '🤖 GitHub Copilot'")
