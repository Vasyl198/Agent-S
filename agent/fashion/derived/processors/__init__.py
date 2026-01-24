"""
🔧 DERIVED GEOMETRY PROCESSORS
================================

Модуль процессоров для создания производной геометрии паттернов.

📌 Каждый процессор:
- НЕ изменяет base contour
- НЕ пишет в PatternModel
- Возвращает чистую DerivedGeometry
"""

from .seam_allowance_processor import SeamAllowanceProcessor
from .notch_processor import NotchProcessor

__all__ = [
    'SeamAllowanceProcessor',
    'NotchProcessor'
]
