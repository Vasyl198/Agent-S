#!/usr/bin/env python3
"""Тест полного цикла: агент пишет код и выполняет его"""

import sys
sys.path.append('.')
from universal_agent import UniversalAgent

def test_full_code_cycle():
    """Тестируем полный цикл выполнения кода через агента"""
    agent = UniversalAgent(enable_local_env=True, enable_reflection=False)
    
    # Тестовый запрос на выполнение кода
    task = "напиши код на Python, который выводит числа от 1 до 5, и запусти его"
    
    print(f"Задача: {task}")
    print("=" * 50)
    
    result = agent.execute_instruction(task)
    
    print(f"Success: {result.get('success', False)}")
    
    # Выводим результаты
    results = result.get('results', [])
    for r in results:
        if isinstance(r, dict):
            tool = r.get('tool', 'unknown')
            success = r.get('success', False)
            print(f"Tool: {tool}, Success: {success}")
            
            if tool == 'code_execution':
                data = r.get('data', {})
                print(f"Code execution result: {data}")
    
    return result

if __name__ == "__main__":
    test_full_code_cycle()
