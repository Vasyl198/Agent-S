"""
🧠 ФАЗА 3.1 — SEMANTICS AS FIRST-CLASS DATA
=================================================

🎯 ЦЕЛЬ ФАЗЫ 3.1:
- семантика не жила в CAD Core
- семантика не вычислялась каждый раз заново
- процессоры не "угадывали", что есть талия / бок / низ
- ML мог учиться на семантике напрямую

📌 После этой фазы:
PatternModel = геометрия + смысл

🧠 КЛЮЧЕВАЯ ИДЕЯ:
Раньше было: Point(role="WAIST_CENTER"), Segment(role="WAIST")
Теперь: PatternSemantics с индексами, а не объектами
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class PointSemanticRole(Enum):
    """Семантические роли точек"""
    WAIST_CENTER = "WAIST_CENTER"
    WAIST_SIDE = "WAIST_SIDE"
    HIP_SIDE = "HIP_SIDE"
    HEM_SIDE = "HEM_SIDE"
    HEM_CENTER = "HEM_CENTER"
    CENTER_LINE = "CENTER_LINE"
    SHOULDER_POINT = "SHOULDER_POINT"
    NECK_POINT = "NECK_POINT"
    ARMHOLE_POINT = "ARMHOLE_POINT"
    UNKNOWN = "UNKNOWN"


class SegmentSemanticRole(Enum):
    """Семантические роли сегментов"""
    WAIST = "WAIST"
    SIDE = "SIDE"
    HEM = "HEM"
    CENTER = "CENTER"
    SHOULDER = "SHOULDER"
    NECKLINE = "NECKLINE"
    ARMHOLE = "ARMHOLE"
    UNKNOWN = "UNKNOWN"


class RegionType(Enum):
    """Типы регионов паттерна"""
    WAIST_REGION = "WAIST_REGION"
    HIP_REGION = "HIP_REGION"
    HEM_REGION = "HEM_REGION"
    SIDE_REGION = "SIDE_REGION"
    CENTER_REGION = "CENTER_REGION"
    UNKNOWN_REGION = "UNKNOWN_REGION"


@dataclass(frozen=True)
class PatternSemantics:
    """
    🧠 PATTERN SEMANTICS — ЯДРО ФАЗЫ 3.1
    
    📌 Индексы, а не объекты
    📌 Никакой зависимости от CAD Core
    📌 Идеально для сериализации и ML
    
    ❗ Геометрия остаётся слепой
    ❗ Смысл — в PatternSemantics
    """
    point_roles: Dict[int, str]
    segment_roles: Dict[int, str]
    region_map: Optional[Dict[str, str]] = None
    invariants: Optional[Dict[str, any]] = None
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.point_roles:
            raise ValueError("Point roles cannot be empty")
        
        if not self.segment_roles:
            raise ValueError("Segment roles cannot be empty")
        
        # Проверяем, что роли валидны
        valid_point_roles = {role.value for role in PointSemanticRole}
        valid_segment_roles = {role.value for role in SegmentSemanticRole}
        
        invalid_point_roles = set(self.point_roles.values()) - valid_point_roles
        if invalid_point_roles:
            raise ValueError(f"Invalid point roles: {invalid_point_roles}")
        
        invalid_segment_roles = set(self.segment_roles.values()) - valid_segment_roles
        if invalid_segment_roles:
            raise ValueError(f"Invalid segment roles: {invalid_segment_roles}")
    
    def points_by_role(self, role: str) -> List[int]:
        """
        Получить индексы точек по роли
        
        Args:
            role: роль точки
            
        Returns:
            список индексов точек
        """
        return [i for i, r in self.point_roles.items() if r == role]
    
    def segments_by_role(self, role: str) -> List[int]:
        """
        Получить индексы сегментов по роли
        
        Args:
            role: роль сегмента
            
        Returns:
            список индексов сегментов
        """
        return [i for i, r in self.segment_roles.items() if r == role]
    
    def get_point_role(self, point_index: int) -> Optional[str]:
        """
        Получить роль точки по индексу
        
        Args:
            point_index: индекс точки
            
        Returns:
            роль точки или None
        """
        return self.point_roles.get(point_index)
    
    def get_segment_role(self, segment_index: int) -> Optional[str]:
        """
        Получить роль сегмента по индексу
        
        Args:
            segment_index: индекс сегмента
            
        Returns:
            роль сегмента или None
        """
        return self.segment_roles.get(segment_index)
    
    def get_all_point_roles(self) -> Set[str]:
        """
        Получить все уникальные роли точек
        
        Returns:
            множество ролей точек
        """
        return set(self.point_roles.values())
    
    def get_all_segment_roles(self) -> Set[str]:
        """
        Получить все уникальные роли сегментов
        
        Returns:
            множество ролей сегментов
        """
        return set(self.segment_roles.values())
    
    def get_waist_points(self) -> List[int]:
        """Получить индексы точек талии"""
        return self.points_by_role(PointSemanticRole.WAIST_CENTER.value) + \
               self.points_by_role(PointSemanticRole.WAIST_SIDE.value)
    
    def get_hem_points(self) -> List[int]:
        """Получить индексы точек низа"""
        return self.points_by_role(PointSemanticRole.HEM_CENTER.value) + \
               self.points_by_role(PointSemanticRole.HEM_SIDE.value)
    
    def get_waist_segments(self) -> List[int]:
        """Получить индексы сегментов талии"""
        return self.segments_by_role(SegmentSemanticRole.WAIST.value)
    
    def get_hem_segments(self) -> List[int]:
        """Получить индексы сегментов низа"""
        return self.segments_by_role(SegmentSemanticRole.HEM.value)
    
    def get_side_segments(self) -> List[int]:
        """Получить индексы боковых сегментов"""
        return self.segments_by_role(SegmentSemanticRole.SIDE.value)
    
    def get_center_segments(self) -> List[int]:
        """Получить индексы центральных сегментов"""
        return self.segments_by_role(SegmentSemanticRole.CENTER.value)
    
    def to_dict(self) -> dict:
        """
        Преобразовать в словарь
        
        Returns:
            словарное представление семантики
        """
        return {
            'point_roles': self.point_roles,
            'segment_roles': self.segment_roles,
            'region_map': self.region_map,
            'invariants': self.invariants
        }
    
    def __str__(self) -> str:
        point_count = len(self.point_roles)
        segment_count = len(self.segment_roles)
        return f"PatternSemantics({point_count} points, {segment_count} segments)"
    
    def __repr__(self) -> str:
        return f"PatternSemantics(points={len(self.point_roles)}, segments={len(self.segment_roles)})"


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_pattern_semantics(point_roles: Dict[int, str], 
                         segment_roles: Dict[int, str],
                         region_map: Optional[Dict[str, str]] = None,
                         invariants: Optional[Dict[str, any]] = None) -> PatternSemantics:
    """
    Создать семантику паттерна - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        point_roles: словарь {индекс_точки: роль}
        segment_roles: словарь {индекс_сегмента: роль}
        region_map: карта регионов
        invariants: инварианты паттерна
        
    Returns:
        семантика паттерна
    """
    return PatternSemantics(
        point_roles=point_roles,
        segment_roles=segment_roles,
        region_map=region_map,
        invariants=invariants
    )


def create_skirt_semantics() -> PatternSemantics:
    """
    Создать стандартную семантику юбки - УДОБНЫЙ КОНСТРУКТОР
    
    Returns:
        семантика юбки
    """
    return create_pattern_semantics(
        point_roles={
            0: PointSemanticRole.WAIST_CENTER.value,
            1: PointSemanticRole.WAIST_SIDE.value,
            2: PointSemanticRole.WAIST_SIDE.value,
            3: PointSemanticRole.HIP_SIDE.value,
            4: PointSemanticRole.HEM_SIDE.value,
            5: PointSemanticRole.HEM_CENTER.value,
            6: PointSemanticRole.HEM_CENTER.value,
            7: PointSemanticRole.CENTER_LINE.value
        },
        segment_roles={
            0: SegmentSemanticRole.WAIST.value,
            1: SegmentSemanticRole.WAIST.value,
            2: SegmentSemanticRole.SIDE.value,
            3: SegmentSemanticRole.SIDE.value,
            4: SegmentSemanticRole.HEM.value,
            5: SegmentSemanticRole.HEM.value,
            6: SegmentSemanticRole.CENTER.value,
            7: SegmentSemanticRole.CENTER.value
        },
        region_map={
            'waist_region': '0,1,2',
            'hip_region': '2,3,4',
            'hem_region': '4,5,6',
            'side_region': '1,2,3,4',
            'center_region': '0,6,7'
        },
        invariants={
            'pattern_type': 'skirt',
            'closure': 'center_back',
            'fit': 'regular'
        }
    )


def validate_semantics(semantics: PatternSemantics) -> bool:
    """
    Валидировать семантику - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        semantics: семантика паттерна
        
    Returns:
        True если семантика валидна
    """
    try:
        # Проверяем базовые поля
        if not semantics.point_roles or not semantics.segment_roles:
            return False
        
        # Проверяем, что индексы последовательны
        if semantics.point_roles:
            max_point_index = max(semantics.point_roles.keys())
            expected_point_indices = set(range(max_point_index + 1))
            actual_point_indices = set(semantics.point_roles.keys())
            
            if actual_point_indices != expected_point_indices:
                return False
        
        if semantics.segment_roles:
            max_segment_index = max(semantics.segment_roles.keys())
            expected_segment_indices = set(range(max_segment_index + 1))
            actual_segment_indices = set(semantics.segment_roles.keys())
            
            if actual_segment_indices != expected_segment_indices:
                return False
        
        return True
        
    except Exception:
        return False


import logging
logger = logging.getLogger(__name__)

logger.debug("PatternSemantics loaded")
logger.debug("Geometry remains blind")
logger.debug("Meaning is in PatternSemantics")
