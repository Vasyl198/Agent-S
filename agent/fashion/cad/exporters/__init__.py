"""
CAD EXPORTERS - ТУПЫЕ СЕРИАЛИЗАТОРЫ
=========================================

🔵 EXPORTERS — СТАНОВЯТСЯ ТУПЫМИ

Разрешено:
- взять готовый Contour
- сериализовать в DXF

🚫 Запрещено:
- исправлять
- сортировать
- замыкать
- "лечить"
"""

from .dxf import DXFExporter, SemanticDXFExporter
from .dxf import (
    export_contour_to_dxf,
    export_semantic_contour_to_dxf,
    export_multiple_contours_to_dxf
)

__all__ = [
    'DXFExporter',
    'SemanticDXFExporter',
    'export_contour_to_dxf',
    'export_semantic_contour_to_dxf',
    'export_multiple_contours_to_dxf'
]
