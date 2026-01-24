"""
🧠 ШАГ 2. PatternModel — СЕРДЦЕ СИСТЕМЫ (ОБНОВЛЕН ДЛЯ ФАЗЫ 3.1)
========================================================================

❗ КРИТИЧЕСКИЕ ПРАВИЛА:

❌ PatternModel НЕ создаёт точки
❌ НЕ чинит геометрию
❌ НЕ экспортирует DXF
✅ Только хранит и передаёт

📌 CAD Core отвечает за геометрию
📌 PatternModel отвечает за бизнес-логику
📌 PatternSemantics отвечает за смысл
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from agent.fashion.cad.core.geometry import Contour
from agent.fashion.cad.core.validation import is_valid_geometry, validate_geometry
from .metadata import PatternMeta
from .semantics import PatternSemantics
from .dimensions import PatternDimensions
from .grading import PatternGrading
from .manufacturing import PatternManufacturing
from agent.fashion.derived.model import DerivedGeometry


@dataclass(frozen=True)
class PatternModel:
    """
    🧠 PATTERN MODEL — СЕРДЦЕ СИСТЕМЫ (ОБНОВЛЕН ДЛЯ ФАЗЫ 4.1)
    
    📌 CAD Core отвечает за геометрию
    📌 PatternModel отвечает за бизнес-логику
    📌 PatternSemantics отвечает за смысл
    
    ❗ КРИТИЧЕСКИЕ ПРАВИЛА:
    ❌ НЕ создаёт точки
    ❌ НЕ чинит геометрию
    ❌ НЕ экспортирует DXF
    ❌ НЕ создаёт derived geometry
    ✅ Только хранит и передаёт
    """
    contour: Contour
    meta: PatternMeta
    semantics: Optional[PatternSemantics] = None
    dimensions: Optional[PatternDimensions] = None  # ФАЗА 3.2
    grading: Optional[PatternGrading] = None       # ФАЗА 3.3
    manufacturing: Optional[PatternManufacturing] = None  # ФАЗА 3.4
    derived_geometry: Optional[DerivedGeometry] = None  # ФАЗА 4.1
    
    def __post_init__(self):
        """Валидация после создания"""
        # Проверяем, что контур валиден
        if not is_valid_geometry(self.contour):
            errors = validate_geometry(self.contour)
            raise ValueError(f"Invalid contour in PatternModel: {errors}")
        
        # Проверяем метаданные
        if not self.meta:
            raise ValueError("PatternMeta cannot be None")
        
        # Проверяем семантику если она есть
        if self.semantics:
            from .semantics import validate_semantics
            if not validate_semantics(self.semantics):
                raise ValueError("Invalid semantics in PatternModel")
    
    def validate(self) -> bool:
        """
        Валидировать модель
        
        Returns:
            True если модель валидна
        """
        try:
            # Делегируем валидацию геометрии в CAD Core
            if not is_valid_geometry(self.contour):
                return False
            
            # Проверяем метаданные
            if not self.meta or not self.meta.name:
                return False
            
            # Проверяем семантику если она есть
            if self.semantics:
                from .semantics import validate_semantics
                if not validate_semantics(self.semantics):
                    return False
            
            return True
        except Exception:
            return False
    
    def get_bounds(self) -> tuple[float, float, float, float]:
        """
        Получить границы модели
        
        Returns:
            (xmin, ymin, xmax, ymax)
        """
        return self.contour.bounds
    
    def get_area(self) -> float:
        """
        Получить площадь модели
        
        Returns:
            площадь
        """
        return self.contour.area
    
    def get_perimeter(self) -> float:
        """
        Получить периметр модели
        
        Returns:
            периметр
        """
        return self.contour.length
    
    def get_segments_count(self) -> int:
        """
        Получить количество сегментов
        
        Returns:
            количество сегментов
        """
        return len(self.contour.segments)
    
    def get_arcs_count(self) -> int:
        """
        Получить количество дуг
        
        Returns:
            количество дуг
        """
        return self.contour.arc_count
    
    def get_points_count(self) -> int:
        """
        Получить количество точек
        
        Returns:
            количество точек
        """
        return len(self.contour.points)
    
    # Новые методы для работы с семантикой (ФАЗА 3.1)
    def has_semantics(self) -> bool:
        """
        Проверить наличие семантики
        
        Returns:
            True если семантика есть
        """
        return self.semantics is not None
    
    def get_point_role(self, point_index: int) -> Optional[str]:
        """
        Получить роль точки по индексу
        
        Args:
            point_index: индекс точки
            
        Returns:
            роль точки или None
        """
        if not self.semantics:
            return None
        return self.semantics.get_point_role(point_index)
    
    def get_segment_role(self, segment_index: int) -> Optional[str]:
        """
        Получить роль сегмента по индексу
        
        Args:
            segment_index: индекс сегмента
            
        Returns:
            роль сегмента или None
        """
        if not self.semantics:
            return None
        return self.semantics.get_segment_role(segment_index)
    
    def get_waist_points(self) -> list[int]:
        """
        Получить индексы точек талии
        
        Returns:
            индексы точек талии
        """
        if not self.semantics:
            return []
        return self.semantics.get_waist_points()
    
    def get_hem_points(self) -> list[int]:
        """
        Получить индексы точек низа
        
        Returns:
            индексы точек низа
        """
        if not self.semantics:
            return []
        return self.semantics.get_hem_points()
    
    def get_waist_segments(self) -> list[int]:
        """
        Получить индексы сегментов талии
        
        Returns:
            индексы сегментов талии
        """
        if not self.semantics:
            return []
        return self.semantics.get_waist_segments()
    
    def get_hem_segments(self) -> list[int]:
        """
        Получить индексы сегментов низа
        
        Returns:
            индексы сегментов низа
        """
        if not self.semantics:
            return []
        return self.semantics.get_hem_segments()
    
    # Новые методы для работы с размерами (ФАЗА 3.2)
    def has_dimensions(self) -> bool:
        """
        Проверить наличие размеров
        
        Returns:
            True если размеры есть
        """
        return self.dimensions is not None
    
    def with_dimensions(self, dimensions) -> 'PatternModel':
        """
        Создать новую модель с размерами
        
        Args:
            dimensions: размеры паттерна
            
        Returns:
            новая модель с размерами
        """
        if self.dimensions is not None:
            raise ValueError("Dimensions already set")
        
        # Создаем новую модель с размерами
        return PatternModel(
            contour=self.contour,
            meta=self.meta,
            semantics=self.semantics,
            dimensions=dimensions,
            grading=self.grading,
            manufacturing=self.manufacturing,
            derived_geometry=self.derived_geometry
        )
    
    # Новые методы для работы с градацией (ФАЗА 3.3)
    def has_grading(self) -> bool:
        """
        Проверить наличие градации
        
        Returns:
            True если градация есть
        """
        return self.grading is not None
    
    def with_grading(self, grading) -> 'PatternModel':
        """
        Создать новую модель с градацией
        
        Args:
            grading: градация паттерна
            
        Returns:
            новая модель с градацией
        """
        if self.grading is not None:
            raise ValueError("Grading already set")
        
        # Создаем новую модель с градацией
        return PatternModel(
            contour=self.contour,
            meta=self.meta,
            semantics=self.semantics,
            dimensions=self.dimensions,
            grading=grading,
            manufacturing=self.manufacturing,
            derived_geometry=self.derived_geometry
        )
    
    # Новые методы для работы с производством (ФАЗА 3.4)
    def has_manufacturing(self) -> bool:
        """
        Проверить наличие производственных правил
        
        Returns:
            True если производственные правила есть
        """
        return self.manufacturing is not None
    
    def with_manufacturing(self, manufacturing) -> 'PatternModel':
        """
        Создать новую модель с производственными правилами
        
        Args:
            manufacturing: производственные правила
            
        Returns:
            новая модель с производственными правилами
        """
        if self.manufacturing is not None:
            raise ValueError("Manufacturing already set")
        
        # Создаем новую модель с производственными правилами
        return PatternModel(
            contour=self.contour,
            meta=self.meta,
            semantics=self.semantics,
            dimensions=self.dimensions,
            grading=self.grading,
            manufacturing=manufacturing,
            derived_geometry=self.derived_geometry
        )
    
    # Новые методы для работы с производной геометрией (ФАЗА 4)
    def has_derived_geometry(self) -> bool:
        """
        Проверить наличие производной геометрии
        
        Returns:
            True если производная геометрия есть
        """
        return hasattr(self, 'derived_geometry') and self.derived_geometry is not None
    
    def with_derived_geometry(self, derived_geometry) -> 'PatternModel':
        """
        Создать новую модель с производной геометрией
        
        Args:
            derived_geometry: производная геометрия
            
        Returns:
            новая модель с производной геометрией
        """
        # Создаем новую модель с производной геометрией
        return PatternModel(
            contour=self.contour,
            meta=self.meta,
            semantics=self.semantics,
            dimensions=self.dimensions,
            grading=self.grading,
            manufacturing=self.manufacturing,
            derived_geometry=derived_geometry
        )
    
    def to_dict(self) -> dict:
        """
        Преобразовать в словарь
        
        Returns:
            словарное представление модели
        """
        result = {
            'meta': self.meta.to_dict(),
            'contour': {
                'segments_count': self.get_segments_count(),
                'arcs_count': self.get_arcs_count(),
                'points_count': self.get_points_count(),
                'length': self.get_perimeter(),
                'area': self.get_area(),
                'bounds': self.get_bounds(),
                'closed': self.contour.closed
            },
            'semantics': self.semantics.to_dict() if self.semantics else None,
            'dimensions': self.dimensions.to_dict() if self.dimensions else None,
            'grading': self.grading.to_dict() if self.grading else None,
            'manufacturing': self.manufacturing.to_dict() if self.manufacturing else None,
            'derived_geometry': self.derived_geometry.to_dict() if self.derived_geometry else None
        }
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "PatternModel":
        """
        Создать модель из словаря
            
        Args:
            data: словарное представление модели
                
        Returns:
            модель паттерна
        """
        raise NotImplementedError("PatternModel.from_dict() not implemented - contour deserialization required")
    
    def explain(self) -> dict:
        """
        Объяснить модель паттерна как агрегированные данные
        
        Returns:
            словарное представление модели паттерна
        """
        result = {
            "type": "pattern_model",
            "meta": {
                "name": self.meta.name,
                "size": self.meta.size,
                "version": self.meta.version
            }
        }
        
        # Добавляем размеры (read-only, без вычислений)
        if self.dimensions:
            result["dimensions"] = self.dimensions.to_dict()
        
        # Добавляем градацию (агрегируем explain())
        if self.grading:
            result["grading"] = self.grading.explain()
        
        # Добавляем производство (агрегируем explain())
        if self.manufacturing:
            result["manufacturing"] = self.manufacturing.explain()
        
        return result
    
    def explain_full(self) -> dict:
        """
        Объяснить модель паттерна как причинно-следственный граф
        
        Returns:
            словарное представление explain-графа от намерения до результата
        """
        result = {
            "type": "pattern_explain_graph",
            "meta": {
                "name": self.meta.name,
                "size": self.meta.size,
                "version": self.meta.version
            },
            "intent": {},
            "derived": {},
            "links": []
        }
        
        # Собираем намерения (intent)
        if self.dimensions:
            result["intent"]["dimensions"] = self.dimensions.to_dict()
        
        if self.grading:
            result["intent"]["grading"] = self.grading.explain()
        
        if self.manufacturing:
            result["intent"]["manufacturing"] = self.manufacturing.explain()
        
        # Собираем производную геометрию (derived)
        if self.has_derived_geometry() and self.derived_geometry:
            result["derived"]["geometry"] = self.derived_geometry.explain()
            
            # Строим связи (links) на основе source в derived.explain()
            derived_explain = self.derived_geometry.explain()
            
            # Связи для припусков
            for allowance in derived_explain.get("seam_allowances", []):
                result["links"].append({
                    "from": allowance["source"],
                    "to": f"derived.seam_allowances.{allowance['role']}",
                    "type": "causes"
                })
            
            # Связи для надсечек
            for notch in derived_explain.get("notches", []):
                result["links"].append({
                    "from": notch["source"],
                    "to": f"derived.notches.{notch['role']}",
                    "type": "causes"
                })
            
            # Связь для долевой линии
            grainline_info = derived_explain.get("grainline")
            if grainline_info:
                result["links"].append({
                    "from": grainline_info["source"],
                    "to": f"derived.grainline.{grainline_info['region']}",
                    "type": "causes"
                })
        
        return result
    
    def __str__(self) -> str:
        parts = []
        parts.append(f"{self.meta.name} {self.meta.size}")
        parts.append(f"{self.get_segments_count()} segments")
        
        if self.semantics:
            parts.append("semantics")
        
        if self.dimensions:
            parts.append("dimensions")
        
        if self.grading:
            parts.append("grading")
        
        if self.manufacturing:
            parts.append("manufacturing")
        
        if self.has_derived_geometry():
            parts.append("derived")
        
        return f"PatternModel({', '.join(parts)})"


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА (ОБНОВЛЕНЫ ДЛЯ ФАЗЫ 3.1)
def create_pattern_model(contour: Contour, meta: PatternMeta,
                      semantics: Optional[PatternSemantics] = None,
                      dimensions: Optional[PatternDimensions] = None,
                      grading: Optional[PatternGrading] = None,
                      manufacturing: Optional[PatternManufacturing] = None) -> PatternModel:
    """
    Создать модель паттерна - ЕДИНСТВЕННЫЙ СПОСОБ (ОБНОВЛЕН ДЛЯ ФАЗЫ 3.1)
    
    Args:
        contour: контур из CAD Core
        meta: метаданные паттерна
        semantics: семантика паттерна (НОВОЕ в ФАЗЕ 3.1)
        dimensions: авторазмеры
        grading: правила градации
        manufacturing: производственные данные
        
    Returns:
        модель паттерна
    """
    return PatternModel(
        contour=contour,
        meta=meta,
        semantics=semantics,
        dimensions=dimensions,
        grading=grading,
        manufacturing=manufacturing
    )


def validate_pattern_model(model: PatternModel) -> bool:
    """
    Валидировать модель паттерна - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        model: модель паттерна
        
    Returns:
        True если модель валидна
    """
    return model.validate()
