"""
🎯 TARGETS — СТАНДАРТИЗАЦИЯ ЦЕЛЕЙ ОПТИМИЗАЦИИ
===============================================

🎯 Стандартизирует "что оптимизируем" и убирает "ручные target dict" по всему коду.

📌 Вводит:
- TargetSpec (тип цели + роль + величина + политика)
- TargetLibrary (готовые цели и их валидация)
- Target→RulePaths map (какие rule paths допустимо менять для цели)
"""

try:
    from .spec import TargetSpec
    from .library import TargetLibrary
    from .mappings import TARGET_PATH_MAPPINGS
    
    __all__ = [
        'TargetSpec',
        'TargetLibrary',
        'TARGET_PATH_MAPPINGS'
    ]
except ImportError as e:
    # Fallback если модули недоступны
    print(f"Warning: Could not import targets modules: {e}")
    __all__ = []
