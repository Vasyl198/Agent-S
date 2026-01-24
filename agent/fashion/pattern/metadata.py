"""
🧠 ШАГ 1. PatternMeta (МИНИМУМ, НО ЖЁСТКО)
=================================================

📌 frozen=True — защита от случайных правок
📌 ML и версии скажут спасибо
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PatternMeta:
    """
    🏷️ МЕТАДАННЫЕ ПАТТЕРНА
    
    📌 frozen=True — защита от случайных правок
    📌 ML и версии скажут спасибо
    """
    name: str
    size: str          # M, L, XL
    version: str       # v1.0
    author: str = "agent"
    description: Optional[str] = None
    created_at: Optional[str] = None
    tags: Optional[list] = None
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.name or not self.name.strip():
            raise ValueError("Pattern name cannot be empty")
        
        if not self.size or not self.size.strip():
            raise ValueError("Pattern size cannot be empty")
        
        if not self.version or not self.version.strip():
            raise ValueError("Pattern version cannot be empty")
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'name': self.name,
            'size': self.size,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'created_at': self.created_at,
            'tags': self.tags or []
        }
    
    def __str__(self) -> str:
        return f"PatternMeta({self.name} {self.size} {self.version})"


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_pattern_meta(name: str, size: str, version: str = "v1.0", 
                      author: str = "agent", description: str = None) -> PatternMeta:
    """
    Создать метаданные паттерна - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        name: название паттерна
        size: размер
        version: версия
        author: автор
        description: описание
        
    Returns:
        метаданные паттерна
    """
    return PatternMeta(
        name=name,
        size=size,
        version=version,
        author=author,
        description=description,
        created_at=None,  # Будет установлено автоматически
        tags=None
    )


import logging
logger = logging.getLogger(__name__)

logger.debug("PatternMeta loaded")
