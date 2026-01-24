"""
🧭 GRAINLINE MODEL (ФАЗА 4.4)
==============================

Модель долевой линии как производного ориентира.
"""

from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class Grainline:
    """
    Долевая линия как производный ориентир.
    
    ⚠️ Grainline — не Segment, это производный ориентир, а не часть контура.
    """
    start: Dict[str, float]  # Точка начала {x, y}
    end: Dict[str, float]    # Точка конца {x, y}
    role: str                # CENTER_LINE, FRONT, BACK, etc
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'start': self.start,
            'end': self.end,
            'role': self.role
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Grainline':
        """Создать из словаря"""
        return cls(
            start=data['start'],
            end=data['end'],
            role=data['role']
        )
    
    def __eq__(self, other) -> bool:
        """Сравнение долевых линий"""
        if not isinstance(other, Grainline):
            return False
        return (
            self.start == other.start and
            self.end == other.end and
            self.role == other.role
        )
