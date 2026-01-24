"""
📏 ФАЗА 3.2 — DIMENSIONS AS DERIVED DATA
==============================================

🎯 СМЫСЛ ФАЗЫ 3.2:
📏 размеры НЕ хранятся в геометрии
🧠 размеры НЕ угадываются  
🔁 размеры всегда пересчитываются из:
Contour + Semantics → Dimensions

✅ критично для ML, градации, автоподгонки, валидации, сравнения
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class PatternDimensions:
    """
    📏 PATTERN DIMENSIONS — ЧИСТЫЕ ЧИСЛА
    
    ✅ нет логики
    ✅ нет геометрии
    ✅ только измерения
    ✅ идеально для ML
    """
    waist_length: float
    hem_width: float
    length: float
    hip_circumference: Optional[float] = None
    bust_circumference: Optional[float] = None
    shoulder_width: Optional[float] = None
    
    def __post_init__(self):
        """Валидация после создания"""
        if self.waist_length <= 0:
            raise ValueError("Waist length must be positive")
        
        if self.hem_width <= 0:
            raise ValueError("Hem width must be positive")
        
        if self.length <= 0:
            raise ValueError("Length must be positive")
    
    def to_dict(self) -> dict:
        """
        Преобразовать в словарь
        
        Returns:
            словарное представление размеров
        """
        return {
            "waist_length": self.waist_length,
            "hem_width": self.hem_width,
            "length": self.length,
            "hip_circumference": self.hip_circumference,
            "bust_circumference": self.bust_circumference,
            "shoulder_width": self.shoulder_width
        }
    
    def __str__(self) -> str:
        return f"PatternDimensions(waist={self.waist_length:.1f}, hem={self.hem_width:.1f}, length={self.length:.1f})"
    
    def __repr__(self) -> str:
        return f"PatternDimensions(waist_length={self.waist_length}, hem_width={self.hem_width}, length={self.length})"


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_pattern_dimensions(waist_length: float, hem_width: float, length: float,
                           hip_circumference: Optional[float] = None,
                           bust_circumference: Optional[float] = None,
                           shoulder_width: Optional[float] = None) -> PatternDimensions:
    """
    Создать размеры паттерна - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        waist_length: длина талии
        hem_width: ширина низа
        length: длина изделия
        hip_circumference: обхват бедер
        bust_circumference: обхват груди
        shoulder_width: ширина плеч
        
    Returns:
        размеры паттерна
    """
    return PatternDimensions(
        waist_length=waist_length,
        hem_width=hem_width,
        length=length,
        hip_circumference=hip_circumference,
        bust_circumference=bust_circumference,
        shoulder_width=shoulder_width
    )


def validate_dimensions(dimensions: PatternDimensions) -> bool:
    """
    Валидировать размеры - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        dimensions: размеры паттерна
        
    Returns:
        True если размеры валидны
    """
    try:
        return (dimensions.waist_length > 0 and 
                dimensions.hem_width > 0 and 
                dimensions.length > 0)
    except Exception:
        return False


import logging
logger = logging.getLogger(__name__)

logger.debug("PatternDimensions loaded")
