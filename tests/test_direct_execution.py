#!/usr/bin/env python3
"""Прямой тест выполнения кода через агента"""

import sys
import asyncio
sys.path.append('.')
from universal_agent import UniversalAgent

def test_direct_code_execution():
    """Тестируем прямое выполнение кода"""
    agent = UniversalAgent(enable_local_env=True, enable_reflection=False)
    
    # Создаем прямой шаг для выполнения кода
    step = {
        'tool': 'code_execution',
        'description': 'Выполнить код для вывода чисел',
        'parameters': {
            'code': '''
for i in range(1, 6):
    print(f"Number: {i}")
'''
        }
    }
    
    print("Прямое выполнение кода:")
    print("=" * 40)
    
    # Выполняем шаг через синхронный метод
    result = agent._execute_step(step)
    
    print(f"Result: {result}")
    
    return result

if __name__ == "__main__":
    test_direct_code_execution()
