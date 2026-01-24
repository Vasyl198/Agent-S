#!/usr/bin/env python3
"""Простой тест code_execution с латиницей"""

import sys
sys.path.append('.')
from universal_agent import ExtendedLocalEnv

env = ExtendedLocalEnv()

# Тест с латиницей
result = env.code_execution('''
for i in range(5):
    print(f"Number: {i}")
''')

print("Result:", result)
