#!/usr/bin/env python3
"""Финальный тест code_execution"""

import sys
sys.path.append('.')
from universal_agent import ExtendedLocalEnv

def test_code_execution():
    """Тестируем выполнение кода"""
    env = ExtendedLocalEnv()
    
    # Тест 1: Простые числа
    print("Тест 1: Вывод чисел от 1 до 5")
    code = '''
for i in range(1, 6):
    print(f"Number: {i}")
'''
    result = env.code_execution(code)
    print(f"Success: {result['success']}")
    print(f"Output: {result['output']}")
    print()
    
    # Тест 2: Математика
    print("Тест 2: Простые вычисления")
    code = '''
x = 10
y = 5
print(f"x + y = {x + y}")
print(f"x * y = {x * y}")
print(f"x ** 2 = {x ** 2}")
'''
    result = env.code_execution(code)
    print(f"Success: {result['success']}")
    print(f"Output: {result['output']}")
    print()
    
    # Тест 3: Списки
    print("Тест 3: Работа со списками")
    code = '''
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
print(f"Original: {numbers}")
print(f"Squared: {squared}")
print(f"Sum: {sum(squared)}")
'''
    result = env.code_execution(code)
    print(f"Success: {result['success']}")
    print(f"Output: {result['output']}")
    print()
    
    # Тест 4: Ошибка
    print("Тест 4: Обработка ошибок")
    code = '''
print(undefined_variable)
'''
    result = env.code_execution(code)
    print(f"Success: {result['success']}")
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Output: {result['output']}")

if __name__ == "__main__":
    test_code_execution()
