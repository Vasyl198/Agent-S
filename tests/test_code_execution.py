#!/usr/bin/env python3
"""Тестирование инструмента code_execution"""

import os
import sys
sys.path.append('.')

from universal_agent import ExtendedLocalEnv

def test_code_execution():
    """Тестируем выполнение кода"""
    env = ExtendedLocalEnv()
    
    # Тест 1: Простой вывод
    print("Тест 1: Простой вывод")
    result = env.code_execution('print("Hello, World!")')
    print(f"Результат: {result}")
    
    # Тест 2: Математические операции
    print("\nТест 2: Математические операции")
    result = env.code_execution('''
x = 10
y = 20
print(f"x + y = {x + y}")
print(f"x * y = {x * y}")
''')
    print(f"Результат: {result}")
    
    # Тест 3: Цикл
    print("\nТест 3: Цикл")
    result = env.code_execution('''
for i in range(5):
    print(f"Число: {i}")
''')
    print(f"Результат: {result}")
    
    # Тест 4: Ошибка в коде
    print("\nТест 4: Ошибка в коде")
    result = env.code_execution('print(undefined_variable)')
    print(f"Результат: {result}")

if __name__ == "__main__":
    test_code_execution()
