"""
🧠 DIMENSION PROCESSOR — ПРАВИЛЬНЫЙ PROCESSOR
==============================================

📌 КЛЮЧЕВОЕ:
❌ не знает тип изделия
❌ не анализирует координаты напрямую
✅ использует семантику
✅ возвращает НОВЫЙ PatternModel
"""

from typing import Optional
import math

from ..model import PatternModel
from ..dimensions import PatternDimensions, create_pattern_dimensions
from ..semantics import PointSemanticRole, SegmentSemanticRole


class DimensionProcessor:
    """
    🧠 ПРОЦЕССОР РАЗМЕРОВ - ВЫЧИСЛЯЕТ ИЗ ГЕОМЕТРИИ + СЕМАНТИКИ
    
    🔁 Contour + Semantics → Dimensions
    """
    
    def process(self, pattern_model: PatternModel) -> PatternModel:
        """
        Обработать модель паттерна и вычислить размеры
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            новая модель с вычисленными размерами
        """
        if pattern_model.semantics is None:
            raise ValueError("Semantics required to compute dimensions")
        
        if pattern_model.dimensions is not None:
            raise ValueError("Dimensions already computed")
        
        # Получаем семантические индексы
        waist_segments = pattern_model.get_waist_segments()
        hem_segments = pattern_model.get_hem_segments()
        waist_points = pattern_model.get_waist_points()
        hem_points = pattern_model.get_hem_points()
        
        if not waist_segments or not hem_segments:
            raise ValueError("WAIST and HEM semantics required")
        
        # Вычисляем размеры через семантику
        waist_length = self._compute_waist_length(pattern_model, waist_segments)
        hem_width = self._compute_hem_width(pattern_model, hem_segments)
        length = self._compute_length(pattern_model, waist_points, hem_points)
        
        # Создаем размеры
        dimensions = create_pattern_dimensions(
            waist_length=round(waist_length, 2),
            hem_width=round(hem_width, 2),
            length=round(length, 2)
        )
        
        # Возвращаем новую модель с размерами
        return pattern_model.with_dimensions(dimensions)
    
    def _compute_waist_length(self, pattern_model: PatternModel, waist_indices: list) -> float:
        """Вычислить длину талии"""
        total_length = 0.0
        for i in waist_indices:
            if i < len(pattern_model.contour.segments):
                total_length += pattern_model.contour.segments[i].length
        return total_length
    
    def _compute_hem_width(self, pattern_model: PatternModel, hem_indices: list) -> float:
        """Вычислить ширину низа"""
        total_length = 0.0
        for i in hem_indices:
            if i < len(pattern_model.contour.segments):
                total_length += pattern_model.contour.segments[i].length
        return total_length
    
    def _compute_length(self, pattern_model: PatternModel, waist_points: list, hem_points: list) -> float:
        """Вычислить длину изделия"""
        if not waist_points or not hem_points:
            return 0.0
        
        # Берем первую точку талии и первую точку низа
        waist_idx = waist_points[0]
        hem_idx = hem_points[0]
        
        if waist_idx < len(pattern_model.contour.points) and hem_idx < len(pattern_model.contour.points):
            waist_point = pattern_model.contour.points[waist_idx]
            hem_point = pattern_model.contour.points[hem_idx]
            
            # Вычисляем вертикальное расстояние
            return abs(hem_point.y - waist_point.y)
        
        return 0.0


print("🧠 DimensionProcessor загружен")
print("📌 Использует семантику, возвращает новый PatternModel")
