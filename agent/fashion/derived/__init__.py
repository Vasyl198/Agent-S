"""
🧪 ФАЗА 4 — DERIVED GEOMETRY PIPELINE
=======================================

🧠 КЛЮЧЕВАЯ ИДЕЯ ФАЗЫ 4:
Превратить правила (manufacturing, grading) → в производную геометрию,
не меняя базовый контур, полностью воспроизводимо и объяснимо.

📌 PatternModel остаётся неизменяемым
📌 Base contour — священен
📌 Вся новая геометрия — ТОЛЬКО производная
"""

from .model import DerivedGeometry
from .processor import DerivedGeometryProcessor

__all__ = [
    'DerivedGeometry',
    'DerivedGeometryProcessor'
]
