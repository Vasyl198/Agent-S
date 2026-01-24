"""
📐 ФАЗА 3.1 — ПРАВИЛА ИНТЕРПРЕТАЦИИ РОЛЕЙ
===============================================

📌 Правила для обработки семантики паттернов
📌 Независимы от CAD Core
📌 Идеально для ML и автоматизации
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

from .semantics import PointSemanticRole, SegmentSemanticRole, RegionType


class ProcessingRule(Enum):
    """Типы правил обработки"""
    FIT_ANALYSIS = "FIT_ANALYSIS"
    STYLE_TRANSFER = "STYLE_TRANSFER"
    AUTO_GRADING = "AUTO_GRADING"
    PATTERN_VALIDATION = "PATTERN_VALIDATION"
    CONSTRUCTION_ANALYSIS = "CONSTRUCTION_ANALYSIS"


@dataclass(frozen=True)
class RoleInterpretationRule:
    """
    📐 ПРАВИЛО ИНТЕРПРЕТАЦИИ РОЛИ
    
    📌 Определяет, как обрабатывать конкретную роль
    📌 Независимо от CAD Core
    """
    role: str
    rule_type: ProcessingRule
    priority: int
    constraints: Dict[str, any]
    transformations: Dict[str, any]
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.role:
            raise ValueError("Role cannot be empty")
        
        if self.priority < 0:
            raise ValueError("Priority must be non-negative")
    
    def applies_to_role(self, role: str) -> bool:
        """
        Проверить, применяется ли правило к роли
        
        Args:
            role: роль для проверки
            
        Returns:
            True если правило применяется
        """
        return self.role == role
    
    def get_constraint(self, key: str, default=None):
        """
        Получить ограничение по ключу
        
        Args:
            key: ключ ограничения
            default: значение по умолчанию
            
        Returns:
            значение ограничения
        """
        return self.constraints.get(key, default)
    
    def get_transformation(self, key: str, default=None):
        """
        Получить трансформацию по ключу
        
        Args:
            key: ключ трансформации
            default: значение по умолчанию
            
        Returns:
            значение трансформации
        """
        return self.transformations.get(key, default)


@dataclass(frozen=True)
class PatternInterpretationRules:
    """
    📐 НАБОР ПРАВИЛ ИНТЕРПРЕТАЦИИ ПАТТЕРНА
    
    📌 Содержит все правила для обработки семантики
    📌 Идеально для ML и автоматизации
    """
    point_rules: Dict[str, RoleInterpretationRule]
    segment_rules: Dict[str, RoleInterpretationRule]
    region_rules: Dict[str, RoleInterpretationRule]
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.point_rules:
            raise ValueError("Point rules cannot be empty")
        
        if not self.segment_rules:
            raise ValueError("Segment rules cannot be empty")
    
    def get_point_rule(self, role: str) -> Optional[RoleInterpretationRule]:
        """
        Получить правило для точки
        
        Args:
            role: роль точки
            
        Returns:
            правило или None
        """
        return self.point_rules.get(role)
    
    def get_segment_rule(self, role: str) -> Optional[RoleInterpretationRule]:
        """
        Получить правило для сегмента
        
        Args:
            role: роль сегмента
            
        Returns:
            правило или None
        """
        return self.segment_rules.get(role)
    
    def get_region_rule(self, region: str) -> Optional[RoleInterpretationRule]:
        """
        Получить правило для региона
        
        Args:
            region: регион
            
        Returns:
            правило или None
        """
        return self.region_rules.get(region)
    
    def get_rules_by_priority(self, rule_type: ProcessingRule) -> List[RoleInterpretationRule]:
        """
        Получить правила по типу и приоритету
        
        Args:
            rule_type: тип правила
            
        Returns:
            отсортированный список правил
        """
        all_rules = list(self.point_rules.values()) + \
                   list(self.segment_rules.values()) + \
                   list(self.region_rules.values())
        
        filtered_rules = [rule for rule in all_rules if rule.rule_type == rule_type]
        
        return sorted(filtered_rules, key=lambda r: r.priority)
    
    def to_dict(self) -> dict:
        """
        Преобразовать в словарь
        
        Returns:
            словарное представление правил
        """
        return {
            'point_rules': {k: v.__dict__ for k, v in self.point_rules.items()},
            'segment_rules': {k: v.__dict__ for k, v in self.segment_rules.items()},
            'region_rules': {k: v.__dict__ for k, v in self.region_rules.items()}
        }
    
    def __str__(self) -> str:
        total_rules = len(self.point_rules) + len(self.segment_rules) + len(self.region_rules)
        return f"PatternInterpretationRules({total_rules} rules)"
    
    def __repr__(self) -> str:
        return f"PatternInterpretationRules(points={len(self.point_rules)}, segments={len(self.segment_rules)}, regions={len(self.region_rules)})"


# 🎯 СТАНДАРТНЫЕ ПРАВИЛА ДЛЯ ЮБКИ
def create_skirt_interpretation_rules() -> PatternInterpretationRules:
    """
    Создать стандартные правила интерпретации для юбки
    
    Returns:
        правила интерпретации юбки
    """
    point_rules = {
        PointSemanticRole.WAIST_CENTER.value: RoleInterpretationRule(
            role=PointSemanticRole.WAIST_CENTER.value,
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=1,
            constraints={
                'must_be_center': True,
                'symmetry_axis': True,
                'closure_point': True
            },
            transformations={
                'grading_multiplier': 0.0,
                'fit_tolerance': 2.0
            }
        ),
        
        PointSemanticRole.WAIST_SIDE.value: RoleInterpretationRule(
            role=PointSemanticRole.WAIST_SIDE.value,
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=2,
            constraints={
                'must_be_side': True,
                'waist_measurement': True
            },
            transformations={
                'grading_multiplier': 1.0,
                'fit_tolerance': 3.0
            }
        ),
        
        PointSemanticRole.HEM_CENTER.value: RoleInterpretationRule(
            role=PointSemanticRole.HEM_CENTER.value,
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=3,
            constraints={
                'must_be_center': True,
                'hem_line': True
            },
            transformations={
                'grading_multiplier': 0.0,
                'fit_tolerance': 5.0
            }
        ),
        
        PointSemanticRole.HEM_SIDE.value: RoleInterpretationRule(
            role=PointSemanticRole.HEM_SIDE.value,
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=4,
            constraints={
                'must_be_side': True,
                'hem_measurement': True
            },
            transformations={
                'grading_multiplier': 1.0,
                'fit_tolerance': 5.0
            }
        )
    }
    
    segment_rules = {
        SegmentSemanticRole.WAIST.value: RoleInterpretationRule(
            role=SegmentSemanticRole.WAIST.value,
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=1,
            constraints={
                'must_be_curved': True,
                'fit_critical': True,
                'measurement_line': True
            },
            transformations={
                'grading_increment': 5.0,
                'smoothing_factor': 0.8
            }
        ),
        
        SegmentSemanticRole.SIDE.value: RoleInterpretationRule(
            role=SegmentSemanticRole.SIDE.value,
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=2,
            constraints={
                'must_be_straight': False,
                'fit_critical': True,
                'body_contour': True
            },
            transformations={
                'grading_increment': 6.0,
                'smoothing_factor': 0.6
            }
        ),
        
        SegmentSemanticRole.HEM.value: RoleInterpretationRule(
            role=SegmentSemanticRole.HEM.value,
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=3,
            constraints={
                'must_be_curved': False,
                'aesthetic_critical': True,
                'measurement_line': True
            },
            transformations={
                'grading_increment': 7.0,
                'smoothing_factor': 0.4
            }
        ),
        
        SegmentSemanticRole.CENTER.value: RoleInterpretationRule(
            role=SegmentSemanticRole.CENTER.value,
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=4,
            constraints={
                'must_be_straight': True,
                'symmetry_axis': True,
                'closure_line': True
            },
            transformations={
                'grading_increment': 0.0,
                'smoothing_factor': 1.0
            }
        )
    }
    
    region_rules = {
        'waist_region': RoleInterpretationRule(
            role='waist_region',
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=1,
            constraints={
                'fit_critical': True,
                'measurement_zone': True
            },
            transformations={
                'tightness_factor': 0.95,
                'ease_allowance': 2.0
            }
        ),
        
        'hip_region': RoleInterpretationRule(
            role='hip_region',
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=2,
            constraints={
                'fit_critical': True,
                'body_contour': True
            },
            transformations={
                'tightness_factor': 0.98,
                'ease_allowance': 3.0
            }
        ),
        
        'hem_region': RoleInterpretationRule(
            role='hem_region',
            rule_type=ProcessingRule.FIT_ANALYSIS,
            priority=3,
            constraints={
                'aesthetic_critical': True,
                'measurement_zone': True
            },
            transformations={
                'tightness_factor': 1.0,
                'ease_allowance': 5.0
            }
        )
    }
    
    return PatternInterpretationRules(
        point_rules=point_rules,
        segment_rules=segment_rules,
        region_rules=region_rules
    )


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def create_interpretation_rules(point_rules: Dict[str, RoleInterpretationRule],
                             segment_rules: Dict[str, RoleInterpretationRule],
                             region_rules: Optional[Dict[str, RoleInterpretationRule]] = None) -> PatternInterpretationRules:
    """
    Создать правила интерпретации - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        point_rules: правила для точек
        segment_rules: правила для сегментов
        region_rules: правила для регионов
        
    Returns:
        правила интерпретации
    """
    return PatternInterpretationRules(
        point_rules=point_rules,
        segment_rules=segment_rules,
        region_rules=region_rules or {}
    )


def apply_rule_to_semantics(semantics, rules: PatternInterpretationRules, 
                          rule_type: ProcessingRule) -> Dict[str, any]:
    """
    Применить правила к семантике - ЕДИНСТВЕННЫЙ СПОСОБ
    
    Args:
        semantics: семантика паттерна
        rules: правила интерпретации
        rule_type: тип правила
        
    Returns:
        результаты применения правил
    """
    results = {}
    
    # Получаем правила по типу
    applicable_rules = rules.get_rules_by_priority(rule_type)
    
    for rule in applicable_rules:
        if rule.rule_type == rule_type:
            # Применяем правило к соответствующим элементам
            if rule.role in semantics.point_roles:
                point_indices = semantics.points_by_role(rule.role)
                results[rule.role] = {
                    'type': 'point',
                    'indices': point_indices,
                    'rule': rule,
                    'constraints': rule.constraints,
                    'transformations': rule.transformations
                }
            elif rule.role in semantics.segment_roles:
                segment_indices = semantics.segments_by_role(rule.role)
                results[rule.role] = {
                    'type': 'segment',
                    'indices': segment_indices,
                    'rule': rule,
                    'constraints': rule.constraints,
                    'transformations': rule.transformations
                }
    
    return results


print("📐 PatternInterpretationRules загружен")
print("📌 Правила для обработки семантики")
print("📌 Независимы от CAD Core")
print("📌 Идеально для ML и автоматизации")
