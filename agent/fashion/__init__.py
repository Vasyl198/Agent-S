"""
Fashion Design Module

Модуль для работы с дизайном одежды, лекалами и интеграцией с CAD системами.
Независимый модуль без внешних платных API.
"""

from .designer import FashionDesigner, GarmentType, DesignStyle, Material, Color, Measurement
from .pattern_maker import PatternMaker, PatternType, Point, Line, Curve, ConstructionMethod
from .exporters import FashionExporter, ExportFormat, ExportOptions
from .cad_bridge import CADBridge, CADSystem, CADConfig, ImportResult, ExportResult

# Опциональная интеграция с датасетом
try:
    from .dataset_integration import DatasetIntegration, DatasetConfig, ValidationResult
    DATASET_AVAILABLE = True
except ImportError:
    DATASET_AVAILABLE = False
    DatasetIntegration = None
    DatasetConfig = None
    ValidationResult = None

__all__ = [
    'FashionDesigner',
    'PatternMaker', 
    'FashionExporter',
    'CADBridge',
    'GarmentType',
    'DesignStyle',
    'PatternType',
    'ConstructionMethod',
    'CADSystem',
    'ExportFormat',
    'ExportOptions',
    'Material',
    'Color',
    'Measurement',
    'Point',
    'Line',
    'Curve',
    'CADConfig',
    'ImportResult',
    'ExportResult'
]

# Добавляем компоненты датасета если доступны
if DATASET_AVAILABLE:
    __all__.extend([
        'DatasetIntegration',
        'DatasetConfig', 
        'ValidationResult',
        'DATASET_AVAILABLE'
    ])

__version__ = '1.1.0'  # Обновляем версию с добавлением датасета
__author__ = 'Universal Agent Fashion Module'
