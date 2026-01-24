"""
🟡 PROCESSORS — ИСПОЛЬЗУЮТ CORE, НО НЕ СОЗДАЮТ ГЕОМЕТРИЮ
========================================================

📁 agent/fashion/cad/processors/

Процессоры используют CAD Core для:
- Градации размеров
- Производственных элементов  
- Раскладки лекал
- Размеров
- Припусков

📌 Правило:
❌ НЕ создают геометрию
✅ Принимают Contour из CAD Core
✅ Возвращают Contour в CAD Core
"""

from .grading_processor import GradingProcessor
from .manufacturing_processor import ManufacturingProcessor
from .marker_processor import MarkerProcessor
from .dimension_processor import DimensionProcessor
from .offset_processor import OffsetProcessor

__all__ = [
    'GradingProcessor',
    'ManufacturingProcessor', 
    'MarkerProcessor',
    'DimensionProcessor',
    'OffsetProcessor'
]
