#!/usr/bin/env python3
"""
Прямой тест интеграции с Copilot для создания игры "Крестики-нолики"
"""

from universal_agent import UniversalAgent

def test_copilot_tic_tac_toe():
    """Тестируем создание игры Крестики-нолики через Copilot"""
    print("🎮 Тестирование создания игры 'Крестики-нолики' через Copilot...")
    
    # Создаем агента
    agent = UniversalAgent(enable_local_env=True)
    
    # Тестируем генерацию кода для игры
    print("\n🤖 Запрашиваем у Copilot создание игры 'Крестики-нолики'...")
    
    try:
        result = agent.copilot_generate(
            "создай игру крестик нолик для двух игроков с графическим интерфейсом",
            "python",
            "игра с полем 3x3, проверка победителя, возможность перезапуска"
        )
        
        if result.get('success'):
            print("✅ Copilot успешно сгенерировал код!")
            print("🎮 Сгенерированный код:")
            print("=" * 50)
            
            generated_code = result.get('generated_code', '')
            # Показываем первые 30 строк кода
            lines = generated_code.split('\n')
            for i, line in enumerate(lines[:30], 1):
                print(f"{i:2d}: {line}")
            
            if len(lines) > 30:
                print(f"... и еще {len(lines) - 30} строк")
            
            print("=" * 50)
            
            # Сохраняем код в файл
            with open('tic_tac_toe_copilot.py', 'w', encoding='utf-8') as f:
                f.write(generated_code)
            print("💾 Код сохранен в файл: tic_tac_toe_copilot.py")
            
            return True
        else:
            print(f"❌ Ошибка генерации кода: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при генерации кода: {e}")
        return False

def test_copilot_status():
    """Проверяем статус Copilot"""
    print("\n📊 Проверка статуса GitHub Copilot...")
    
    agent = UniversalAgent(enable_local_env=True)
    
    try:
        result = agent.copilot_status()
        if result.get('success'):
            print("✅ Copilot доступен!")
            print(f"📋 Статус: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Copilot недоступен: {result.get('error')}")
            print("💡 Установите GitHub Copilot CLI:")
            print("   npm install -g @githubnext/github-copilot-cli")
            print("   copilot auth")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки статуса: {e}")
        return False

def test_copilot_auth():
    """Тестируем аутентификацию"""
    print("\n🔐 Тест аутентификации в GitHub Copilot...")
    
    agent = UniversalAgent(enable_local_env=True)
    
    try:
        result = agent.copilot_authenticate()
        if result.get('success'):
            print("✅ Аутентификация успешна!")
            print(f"👤 Пользователь: {result.get('user_info', 'N/A')}")
            return True
        else:
            print(f"❌ Ошибка аутентификации: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Исключение при аутентификации: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Прямой тест интеграции с GitHub Copilot")
    print("🎮 Цель: Создание игры 'Крестики-нолики'\n")
    
    # Шаг 1: Проверяем доступность
    status_ok = test_copilot_status()
    
    if status_ok:
        # Шаг 2: Аутентификация
        auth_ok = test_copilot_auth()
        
        if auth_ok:
            # Шаг 3: Генерация игры
            game_ok = test_copilot_tic_tac_toe()
            
            if game_ok:
                print("\n🎉 Успех! Игра 'Крестики-нолики' создана через Copilot!")
                print("💡 Запустите игру: python tic_tac_toe_copilot.py")
            else:
                print("\n❌ Не удалось создать игру")
        else:
            print("\n❌ Проблемы с аутентификацией")
    else:
        print("\n❌ Copilot недоступен")
        print("\n📋 Инструкция по установке:")
        print("1. Установите Node.js: https://nodejs.org")
        print("2. Установите Copilot CLI: npm install -g @githubnext/github-copilot-cli")
        print("3. Аутентифицируйтесь: copilot auth")
        print("4. Проверьте статус: copilot whoami")
