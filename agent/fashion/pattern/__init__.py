"""
🧠 UNIFIED PATTERN MODEL (DATA MODEL)
==================================

📌 После этой фазы:
- CAD Core — чистая математика
- PatternModel — бизнес-объект  
- Processors — чистые трансформации
- Exporters — тупой вывод

📁 agent/fashion/pattern/
├── model.py          # 🧠 PatternModel (ядро)
├── metadata.py       # имя, размер, версия
├── semantics.py      # роли точек / сегментов
├── dimensions.py     # авторазмеры
├── grading.py        # правила градации
├── manufacturing.py  # производство
├── serializer.py     # JSON ⇄ PatternModel
└── __init__.py
"""

from .model import PatternModel
from .metadata import PatternMeta

__all__ = [
    'PatternModel',
    'PatternMeta'
]
