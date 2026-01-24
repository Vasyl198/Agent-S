"""
CAD CORE - ЕДИНСТВЕННЫЙ КОНСТРУКТОР
==================================

🎯 ЦЕЛЬ: Сделать так, чтобы:
- геометрия существовала в одном месте
- winstuf не мог случайно создать "вторую реальность"
- все DXF = 100% предсказуемые

🔴 ПРОБЛЕМА №1 (КЛЮЧЕВАЯ):
Сейчас геометрия создаётся в PatternMaker, модифицируется в contour_builder,
"лечится" в proper_dxf_exporter, валидируется в validate_dxf.py
❌ Это архитектурная катастрофа при росте проекта.

✅ РЕШЕНИЕ: КАНОНИЧЕСКИЙ CAD CORE
"""

from .geometry import Point, Segment, Arc, Contour
from .contour import ContourBuilder
from .validation import GeometryValidator
from .curves import CurveProcessor

__all__ = [
    'Point',
    'Segment', 
    'Arc',
    'Contour',
    'ContourBuilder',
    'GeometryValidator',
    'CurveProcessor'
]
