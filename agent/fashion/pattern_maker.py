"""
Pattern Maker Module

Класс для создания лекал, расчета конструкций и управления размерами.
Использует только математические формулы без нейросетей.

БАЗОВЫЕ КОНСТРУКЦИИ ПО ТИПАМ ОДЕЖДЫ:

1. РУБАШКИ (Shirts) - Методика: ЕМКО (Единая методика конструирования одежды)
   - Основные мерки: bust, waist, height, back_length, shoulder_width
   - Ключевые формулы:
     * Ширина = bust/2 + 6.0 (прибавка на свободу)
     * Глубина проймы = bust/4
     * Ширина горловины = bust/20
     * Глубина горловины спинки = bust/40
     * Глубина горловины переда = bust/10
   - Система координат: (0,0) = верх середины спинки

2. ПЛАТЬЯ (Dresses) - Методика: Мюллер (немецкая система)
   - Основные мерки: bust, waist, hips, height, back_length
   - Ключевые формулы:
     * Ширина лифа = bust/2 + 4.0 (прибавка)
     * Положение талии = height * 0.38
     * Ширина юбки = hips/2 + 2.0 (прибавка)
     * Длина платья = height * 0.85

3. ПИДЖАКИ (Jackets) - Методика: Итальянская система
   - Основные мерки: bust, waist, hips, height, shoulder_width
   - Ключевые формулы:
     * Ширина = bust/2 + 8.0 (большая прибавка)
     * Длина пиджака = height * 0.45
     * Ширина лацкана = bust/15
     * Длина рукава = height * 0.32

4. БРЮКИ (Pants) - Методика: Американская система
   - Основные мерки: waist, hips, height, inseam
   - Ключевые формулы:
     * Ширина по талии = waist/4 + 2.0 (прибавка)
     * Ширина по бедрам = hips/4 + 1.0 (прибавка)
     * Глубина шага = height * 0.25
     * Длина ноги = height * 0.75

5. ЮБКИ (Skirts) - Методика: Французская система
   - Основные мерки: waist, hips, height
   - Ключевые формулы:
     * Ширина по талии = waist/4 + 1.0 (прибавка)
     * Ширина по бедрам = hips/4 + 2.0 (прибавка)
     * Длина юбки = height * 0.40
     * Положение линии бедер = height * 0.18

СТРУКТУРА ВОЗВРАЩАЕМОГО ОБЪЕКТА:
{
    "points": {"point_name": {"x": float, "y": float}, ...},
    "lines": {"line_name": {"start": {"x": float, "y": float}, "end": {"x": float, "y": float}}, ...},
    "curves": {"curve_name": {"start": {...}, "control1": {...}, "control2": {...}, "end": {...}}, ...},
    "pattern_type": "тип_лекала",
    "measurements": {...},
    "construction_method": "метод_конструирования",
    "fit_type": "тип_посадки"
}
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import json
import logging
from pathlib import Path
from datetime import datetime


@dataclass
class Point:
    """Точка в 2D пространстве"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """Расстояние до другой точки"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Point':
        return Point(self.x * scalar, self.y * scalar)
    
    def rotate(self, angle_degrees: float, center: 'Point' = None) -> 'Point':
        """Поворот точки вокруг центра"""
        if center is None:
            center = Point(0, 0)
        
        # Перенос в начало координат
        p = self - center
        
        # Поворот
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        new_x = p.x * cos_a - p.y * sin_a
        new_y = p.x * sin_a + p.y * cos_a
        
        # Обратный перенос
        return Point(new_x + center.x, new_y + center.y)


@dataclass
class Line:
    """Линия между двумя точками"""
    start: Point
    end: Point
    
    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)
    
    @property
    def angle(self) -> float:
        """Угол линии в градусах"""
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        return math.degrees(math.atan2(dy, dx))
    
    def midpoint(self) -> Point:
        """Середина линии"""
        return Point(
            (self.start.x + self.end.x) / 2,
            (self.start.y + self.end.y) / 2
        )
    
    def point_at_distance(self, distance: float) -> Point:
        """Точка на линии на заданном расстоянии от начала"""
        if self.length == 0:
            return self.start
        
        ratio = distance / self.length
        ratio = max(0, min(1, ratio))  # Ограничиваем от 0 до 1
        
        return Point(
            self.start.x + (self.end.x - self.start.x) * ratio,
            self.start.y + (self.end.y - self.start.y) * ratio
        )


@dataclass
class Curve:
    """Кривая Безье"""
    start: Point
    control1: Point
    control2: Point
    end: Point
    
    def point_at_t(self, t: float) -> Point:
        """Точка на кривой при параметре t (0 <= t <= 1)"""
        t = max(0, min(1, t))
        
        # Кубическая кривая Безье
        x = ((1-t)**3 * self.start.x + 
             3*(1-t)**2*t * self.control1.x + 
             3*(1-t)*t**2 * self.control2.x + 
             t**3 * self.end.x)
        
        y = ((1-t)**3 * self.start.y + 
             3*(1-t)**2*t * self.control1.y + 
             3*(1-t)*t**2 * self.control2.y + 
             t**3 * self.end.y)
        
        return Point(x, y)


class PatternType(Enum):
    """Типы лекал"""
    BODICE_FRONT = "bodice_front"
    BODICE_BACK = "bodice_back"
    SLEEVE = "sleeve"
    SKIRT_FRONT = "skirt_front"
    SKIRT_BACK = "skirt_back"
    PANTS_FRONT = "pants_front"
    PANTS_BACK = "pants_back"
    COLLAR = "collar"
    CUFF = "cuff"
    POCKET = "pocket"


class ConstructionMethod(Enum):
    """Методы конструирования"""
    STRAIGHT_CUT = "straight_cut"      # Прямой крой
    FITTED = "fitted"                 # Прилегающий
    DRAPED = "draped"                 # Драпировка
    PLEATED = "pleated"               # Плиссированный


class PatternMaker:
    """
    Основной класс для создания лекал.
    
    Использует только математические формулы и стандартные методы конструирования.
    Подготовлен для будущего усложнения и расширения.
    """
    
    def __init__(self):
        """Инициализация PatternMaker"""
        self.seam_allowances = {
            "main": 1.5,  # Основная припуск на шов (см)
            "hem": 2.0,   # Припуск на подгиб (см)
            "closure": 3.0  # Припуск на застежку (см)
        }
        
        self.ease_allowances = {
            "chest": 4.0,   # Прибавка на свободу груди (см)
            "waist": 2.0,   # Прибавка на свободу талии (см)
            "hips": 4.0,    # Прибавка на свободу бедер (см)
            "length": 1.0   # Прибавка на длину (см)
        }
        
        # Хранилище созданных лекал
        self.patterns = {}
        
        # Стандартные пропорции тела
        self.body_proportions = {
            "neck_to_waist": 0.38,        # От шеи до талии от роста
            "waist_to_hips": 0.18,        # От талии до бедер от роста
            "arm_length_ratio": 0.32,    # Длина руки от роста
            "shoulder_width": 0.18,      # Ширина плеч от обхвата груди
            "neck_circumference": 0.4,    # Обхват шеи от обхвата груди
            "waist_position": 0.38            # Положение талии от роста
        }
    
    def create_basic_pattern(self, 
                           pattern_type: PatternType,
                           measurements: Dict[str, float],
                           fit_type: str = "standard_fit",
                           construction_method: ConstructionMethod = ConstructionMethod.STRAIGHT_CUT,
                           use_dataset_reference: bool = False,
                           dataset_integration=None) -> Dict[str, Any]:
        """
        Создать базовое лекало по меркам
        
        Args:
            pattern_type: Тип лекала
            measurements: Словарь с мерками (height, bust, waist, hips)
            fit_type: Тип посадки
            construction_method: Метод конструирования
            use_dataset_reference: Использовать датасет для подстройки
            dataset_integration: Экземпляр DatasetIntegration для поиска похожих паттернов
            
        Returns:
            Словарь с геометрией лекала (точки, линии, кривые)
        """
        # Если нужно использовать датасет - применяем умную подстройку
        if use_dataset_reference and dataset_integration and pattern_type in [PatternType.SKIRT_FRONT, PatternType.SKIRT_BACK]:
            return self._create_skirt_with_dataset_reference(
                pattern_type, measurements, fit_type, construction_method, dataset_integration
            )
        
        # Стандартное создание без датасета
        validated_measurements = self._validate_measurements(measurements)
        
        # Выбор метода конструирования
        if pattern_type in [PatternType.BODICE_FRONT, PatternType.BODICE_BACK]:
            # Проверяем, нужен ли пиджак (по наличию характерных прибавок)
            chest = measurements.get("bust", 96)
            jacket_width = chest / 2 + 8.0  # Итальянская система для пиджаков
            shirt_width = chest / 2 + 6.0   # ЕМКО для рубашек
            
            # Если в мерках есть указание на пиджак или большая прибавка
            if "garment_type" in measurements and measurements["garment_type"] == "jacket":
                geometry = self.build_jacket_base(pattern_type, measurements)
            else:
                geometry = self.build_shirt_base(measurements)
        elif pattern_type == PatternType.SLEEVE:
            geometry = self._create_sleeve_pattern(validated_measurements, fit_type, construction_method)
        elif pattern_type in [PatternType.SKIRT_FRONT, PatternType.SKIRT_BACK]:
            geometry = self._create_skirt_pattern(pattern_type, validated_measurements, fit_type, construction_method)
        elif pattern_type in [PatternType.PANTS_FRONT, PatternType.PANTS_BACK]:
            geometry = self._create_pants_pattern(pattern_type, validated_measurements, fit_type, construction_method)
        else:
            geometry = self._create_simple_pattern(pattern_type, validated_measurements)
        
        # Добавление служебной информации
        geometry.update({
            "pattern_type": pattern_type.value,
            "measurements": validated_measurements,
            "fit_type": fit_type,
            "construction_method": construction_method.value,
            "seam_allowance": self.seam_allowances["main"],
            "created_at": "2026-01-06T17:00:00",
            "dataset_adjusted": False
        })
        
        # Сохранение лекала в память
        pattern_id = f"{pattern_type.value}_{fit_type}_{hash(str(validated_measurements))}"
        self.patterns[pattern_id] = geometry.copy()
        
        return geometry
    
    def _create_skirt_with_dataset_reference(self, 
                                        pattern_type: PatternType,
                                        measurements: Dict[str, float],
                                        fit_type: str,
                                        construction_method: ConstructionMethod,
                                        dataset_integration) -> Dict[str, Any]:
        """
        Создание юбки с подстройкой под датасет
        
        Алгоритм:
        1. Построить базовую юбку (алгоритмически)
        2. Найти похожие паттерны из датасета
        3. Если найдены - масштабировать точки под реальные мерки
        4. Вернуть измененный паттерн
        """
        logging.info(f"Creating skirt with dataset reference for {pattern_type.value}")
        
        # Шаг 1: Находим похожие паттерны из датасета
        similar_patterns = self._find_similar_skirt_patterns(measurements, dataset_integration)
        
        # Шаг 2: Проверяем есть ли похожие паттерны
        if not similar_patterns:
            logging.warning("No similar patterns found in dataset, using base pattern")
            # Создаем базовую юбку без датасета
            base_pattern = self._create_skirt_pattern(
                pattern_type, measurements, fit_type, construction_method,
                dataset_integration=None,
                similar_patterns=None
            )
            return self._finalize_pattern(base_pattern, False, {})
        
        # Шаг 3: Создаем юбку с усреднением паттернов из датасета
        base_pattern = self._create_skirt_pattern(
            pattern_type, measurements, fit_type, construction_method,
            dataset_integration=dataset_integration,
            similar_patterns=similar_patterns
        )
        
        # Шаг 4: Возвращаем результат (должен быть уже с dataset_adjusted=True)
        return self._finalize_pattern(base_pattern, True, {})
    
    def _find_similar_skirt_patterns(self, measurements: Dict[str, float], dataset_integration) -> List[Dict]:
        """Находит 3-5 похожих паттернов юбок из датасета"""
        try:
            # Создаем эмбеддинг для запроса на основе мерок
            query_pattern = {
                'pattern_type': 'skirt',
                'measurements': measurements,
                'description': f"skirt waist_{measurements.get('waist', 0)} hips_{measurements.get('hips', 0)} height_{measurements.get('height', 0)}"
            }
            
            # Ищем похожие паттерны
            similar_patterns = dataset_integration.search_similar_patterns(
                query_pattern, 
                top_k=5
            )
            
            # Загружаем полные данные паттернов
            loaded_patterns = []
            for pattern_info, similarity in similar_patterns[:5]:  # Берем максимум 5
                try:
                    # Извлекаем путь из метаданных
                    pattern_path = pattern_info.get('source_file', '') or pattern_info.get('path', '')
                    if pattern_path:
                        full_pattern = dataset_integration.load_gpg_pattern(pattern_path)
                        loaded_patterns.append({
                            'pattern': full_pattern,
                            'similarity': similarity,
                            'path': pattern_path
                        })
                except Exception as e:
                    logging.warning(f"Failed to load pattern {pattern_path}: {e}")
                    continue
            
            return loaded_patterns
            
        except Exception as e:
            logging.error(f"Failed to find similar patterns: {e}")
            return []
    
    def _average_construction_rules(self, rules_list: List[Dict[str, float]]) -> Dict[str, float]:
        """Усредняет конструктивные правила из нескольких паттернов"""
        if not rules_list:
            return {}
        
        averaged = {}
        
        # Числовые параметры усредняем
        numeric_keys = [
            'waist_width', 'hip_width', 'hem_width', 
            'side_seam_curve', 'front_back_difference',
            'hip_to_waist_ratio', 'hem_to_waist_ratio', 'flare_ratio'
        ]
        
        for key in numeric_keys:
            values = [rules.get(key, 0) for rules in rules_list if rules.get(key, 0) > 0]
            if values:
                averaged[key] = sum(values) / len(values)
            else:
                averaged[key] = 0.0
        
        # Для silhouette_type используем наиболее частое значение
        silhouette_types = [rules.get('silhouette_type', 'unknown') for rules in rules_list]
        if silhouette_types:
            from collections import Counter
            most_common = Counter(silhouette_types).most_common(1)[0][0]
            averaged['silhouette_type'] = most_common
        else:
            averaged['silhouette_type'] = 'unknown'
        
        # Добавляем статистику
        averaged['source_patterns_count'] = len(rules_list)
        averaged['averaging_method'] = 'arithmetic_mean'
        
        logging.info(f"Averaged construction rules from {len(rules_list)} patterns")
        return averaged
    
    def _apply_dataset_corrections(self, 
                                 base_pattern: Dict[str, Any], 
                                 averaged_rules: Dict[str, float],
                                 measurements: Dict[str, float],
                                 pattern_type: PatternType) -> Dict[str, Any]:
        """Применяет корректировки на основе усредненных правил датасета"""
        
        # Копируем базовый паттерн
        corrected = base_pattern.copy()
        corrected_points = corrected['points'].copy()
        
        # 1. Корректировка ширины талии
        target_waist_width = measurements.get('waist', 0) / 4  # Ширина одной половинки
        dataset_waist_width = averaged_rules.get('waist_width', 0) / 2  # Усредненная ширина половинки
        
        if dataset_waist_width > 0:
            waist_correction_factor = target_waist_width / dataset_waist_width
            logging.info(f"Waist correction factor: {waist_correction_factor:.3f}")
            
            # Применяем корректировку к точкам талии
            for point_name, point_data in corrected_points.items():
                if 'waist' in point_name.lower():
                    point_data['x'] *= waist_correction_factor
        
        # 2. Корректировка ширины бедер
        target_hip_width = measurements.get('hips', 0) / 4
        dataset_hip_width = averaged_rules.get('hip_width', 0) / 2
        
        if dataset_hip_width > 0:
            hip_correction_factor = target_hip_width / dataset_hip_width
            logging.info(f"Hip correction factor: {hip_correction_factor:.3f}")
            
            # Применяем корректировку к точкам бедер
            for point_name, point_data in corrected_points.items():
                if 'hip' in point_name.lower():
                    point_data['x'] *= hip_correction_factor
        
        # 3. Корректировка ширины подола на основе flare_ratio
        target_hem_width = target_waist_width * (1 + averaged_rules.get('flare_ratio', 0.2))
        
        # Применяем к точкам подола
        for point_name, point_data in corrected_points.items():
            if 'hem' in point_name.lower() or 'bottom' in point_name.lower():
                current_x = abs(point_data['x'])
                if current_x > 0:
                    hem_correction_factor = target_hem_width / current_x
                    point_data['x'] *= hem_correction_factor
        
        # 4. Корректировка бокового шва (кривизны)
        side_seam_curve = averaged_rules.get('side_seam_curve', 0)
        if side_seam_curve > 5:  # Если есть значительная кривизна
            # Добавляем кривизну к боковым линиям
            for line_name, line_data in corrected.get('lines', {}).items():
                if 'side' in line_name.lower():
                    # Преобразуем прямую линию в кривую
                    start = line_data.get('start', {})
                    end = line_data.get('end', {})
                    if start and end:
                        # Создаем контрольные точки для кривой Безье
                        mid_x = (start['x'] + end['x']) / 2
                        mid_y = (start['y'] + end['y']) / 2
                        
                        # Добавляем прогиб в зависимости от кривизны
                        curve_offset = side_seam_curve * 0.3
                        
                        corrected['curves'][f"{line_name}_curved"] = {
                            'start': start,
                            'control1': {'x': mid_x, 'y': mid_y - curve_offset},
                            'control2': {'x': mid_x, 'y': mid_y + curve_offset},
                            'end': end
                        }
                        # Удаляем прямую линию
                        del corrected['lines'][line_name]
        
        # 5. Корректировка баланса перед/спинка
        front_back_diff = averaged_rules.get('front_back_difference', 0)
        if front_back_diff > 10 and pattern_type == PatternType.SKIRT_BACK:
            # Смещаем заднюю половинку для баланса
            for point_name, point_data in corrected_points.items():
                if 'center' in point_name.lower() or 'back' in point_name.lower():
                    point_data['y'] += front_back_diff * 0.1  # Небольшая корректировка
        
        corrected['points'] = corrected_points
        corrected['dataset_corrections'] = {
            'waist_correction_factor': waist_correction_factor if dataset_waist_width > 0 else 1.0,
            'hip_correction_factor': hip_correction_factor if dataset_hip_width > 0 else 1.0,
            'target_hem_width': target_hem_width,
            'side_seam_curve_applied': side_seam_curve > 5,
            'front_back_balance_applied': front_back_diff > 10
        }
        
        return corrected
    
    def _rebuild_skirt_pattern(self, 
                             corrected_pattern: Dict[str, Any],
                             pattern_type: PatternType,
                             measurements: Dict[str, float],
                             fit_type: str,
                             construction_method: ConstructionMethod) -> Dict[str, Any]:
        """Перестраивает лекала с учетом корректировок"""
        
        # Используем скорректированные точки как основу
        # Но пересчитываем конструктивные линии для целостности
        
        points = corrected_pattern['points']
        lines = {}
        curves = corrected_pattern.get('curves', {})
        
        # Восстанавливаем основные конструктивные линии
        if pattern_type == PatternType.SKIRT_FRONT:
            # Линии передней половинки
            lines.update({
                'waist_line': {
                    'start': points.get('front_waist_left', {'x': -100, 'y': 0}),
                    'end': points.get('front_waist_right', {'x': 100, 'y': 0})
                },
                'center_front_line': {
                    'start': points.get('front_waist_center', {'x': 0, 'y': 0}),
                    'end': points.get('front_hem_center', {'x': 0, 'y': 300})
                },
                'hem_line': {
                    'start': points.get('front_hem_left', {'x': -120, 'y': 300}),
                    'end': points.get('front_hem_right', {'x': 120, 'y': 300})
                }
            })
            
        elif pattern_type == PatternType.SKIRT_BACK:
            # Линии задней половинки
            lines.update({
                'waist_line': {
                    'start': points.get('back_waist_left', {'x': -100, 'y': 20}),
                    'end': points.get('back_waist_right', {'x': 100, 'y': 20})
                },
                'center_back_line': {
                    'start': points.get('back_waist_center', {'x': 0, 'y': 20}),
                    'end': points.get('back_hem_center', {'x': 0, 'y': 320})
                },
                'hem_line': {
                    'start': points.get('back_hem_left', {'x': -120, 'y': 320}),
                    'end': points.get('back_hem_right', {'x': 120, 'y': 320})
                }
            })
        
        # Боковые линии (могут быть кривыми)
        side_lines = ['left_side', 'right_side']
        for side in side_lines:
            side_prefix = f'front_{side}' if pattern_type == PatternType.SKIRT_FRONT else f'back_{side}'
            
            waist_point = points.get(f'{side_prefix}_top', {})
            hem_point = points.get(f'{side_prefix}_bottom', {})
            
            if waist_point and hem_point:
                # Проверяем, нет ли уже кривой для этого бокового шва
                curve_key = f'{side}_seam_curved'
                if curve_key not in curves:
                    # Создаем прямую линию
                    lines[f'{side}_side_line'] = {
                        'start': waist_point,
                        'end': hem_point
                    }
        
        return {
            'points': points,
            'lines': lines,
            'curves': curves,
            'construction_method': f"{construction_method.value}_dataset_adjusted",
            'garment_type': 'skirt',
            'pattern_half': pattern_type.value,
            'rebuilt': True
        }
    
    def _finalize_pattern(self, pattern: Dict[str, Any], dataset_adjusted: bool, rules: Dict[str, float]) -> Dict[str, Any]:
        """Финализация паттерна с добавлением метаданных"""
        
        pattern.update({
            "pattern_type": pattern.get("pattern_type", "skirt"),
            "fit_type": "standard_fit",
            "seam_allowance": self.seam_allowances["main"],
            "created_at": "2026-01-08T10:20:00",
            "dataset_adjusted": dataset_adjusted,
            "construction_rules_applied": rules if dataset_adjusted else {}
        })
        
        return pattern
    
    def _validate_measurements(self, measurements: Dict[str, float]) -> Dict[str, float]:
        """Валидация и дополнение мерок"""
        validated = measurements.copy()
        
        # Проверяем тип одежды по наличию специфичных мерок
        garment_type = validated.get("garment_type", "")
        
        # Обязательные мерки для разных типов одежды
        if garment_type == "skirt":
            # Для юбок достаточно waist, hips, height
            required = ["height", "waist", "hips"]
        elif garment_type == "pants":
            # Для брюк нужны waist, hips, height
            required = ["height", "waist", "hips"]
        else:
            # Для остальной одежды (рубашки, пиджаки и т.д.)
            required = ["height", "bust", "waist", "hips"]
        
        for key in required:
            if key not in validated or validated[key] <= 0:
                raise ValueError(f"Required measurement '{key}' is missing or invalid")
        
        # Расчет дополнительных мерок если отсутствуют
        if "back_length" not in validated:
            validated["back_length"] = validated["height"] * self.body_proportions["neck_to_waist"]
        
        if "shoulder_width" not in validated:
            if "bust" in validated:
                validated["shoulder_width"] = validated["bust"] * self.body_proportions["shoulder_width"]
            else:
                # Для юбок и брюк используем пропорции от талии
                validated["shoulder_width"] = validated["waist"] * 0.3
        
        if "arm_length" not in validated:
            validated["arm_length"] = validated["height"] * self.body_proportions["arm_length_ratio"]
        
        return validated
    
    def build_shirt_base(self, measurements: Dict[str, float]) -> Dict[str, Any]:
        """
        Построение базовой конструкции рубашки по методике ЕМКО
        
        Методика: ЕМКО (Единая методика конструирования одежды)
        Применяется для классических рубашек с приталенным силуэтом
        
        Ключевые мерки:
        - bust: обхват груди (основная мерка)
        - back_length: длина спины до талии
        - shoulder_width: ширина плеч
        
        Ключевые формулы ЕМКО:
        1. Ширина сетки = bust/2 + Пг, где Пг = 6.0 см (прибавка на свободу)
        2. Глубина проймы = bust/4 + Пспр, где Пспр = 0.5 см
        3. Ширина горловины = bust/20 + 0.2 см
        4. Глубина горловины спинки = bust/40
        5. Глубина горловины переда = bust/10 + 0.5 см
        6. Наклон плеча = 2-3 см (стандартный)
        
        Пример расчета для bust = 96 см:
        - Ширина = 96/2 + 6.0 = 54.0 см
        - Глубина проймы = 96/4 + 0.5 = 24.5 см
        - Ширина горловины = 96/20 + 0.2 = 5.0 см
        - Глубина горловины спинки = 96/40 = 2.4 см
        - Глубина горловины переда = 96/10 + 0.5 = 10.1 см
        
        Система координат:
        - Начало (0,0) = верхняя точка середины спинки
        - Ось X → вправо (ширина изделия)
        - Ось Y → вниз (длина изделия)
        """
        
        # Основные мерки и расчеты по ЕМКО
        chest = measurements["bust"]
        back_length = measurements.get("back_length", chest * 0.4)
        
        # Ключевые формулы ЕМКО
        half_chest = chest / 2
        ease_chest = 6.0  # Прибавка на свободу по груди
        width = half_chest + ease_chest  # Общая ширина сетки
        
        # Расчет конструктивных линий
        armhole_depth = chest / 4 + 0.5  # Глубина проймы
        neckline_width = chest / 20 + 0.2  # Ширина горловины
        neckline_depth_back = chest / 40  # Глубина горловины спинки
        neckline_depth_front = chest / 10 + 0.5  # Глубина горловины переда
        shoulder_slope = 2.5  # Наклон плеча
        
        # Расчет положения линий
        chest_line = back_length * 0.3  # Линия груди
        waist_line = back_length  # Линия талии
        hip_line = back_length * 1.2  # Линия бедер (для удлинения)
        
        """
        КЛЮЧЕВЫЕ ТОЧКИ КОНСТРУКЦИИ:
        
        СПИНКА (Back):
        1. A (0, 0) - верх середины спинки, базовая точка
        2. B (-width/2, 0) - левый верхний угол (плечевая точка)
        3. C (width/2, 0) - правый верхний угол (плечевая точка)
        4. D (-width/2, chest_line) - левая точка линии груди
        5. E (width/2, chest_line) - правая точка линии груди
        6. F (-neckline_width/2, -neckline_depth_back) - левая точка горловины
        7. G (neckline_width/2, -neckline_depth_back) - правая точка горловины
        
        ПЕРЕД (Front):
        8. H (width, 0) - верх середины переда (смещен для удобства)
        9. I (width/2, 0) - левый верхний угол переда
        10. J (width*1.5, 0) - правый верхний угол переда
        11. K (width/2, chest_line) - левая точка линии груди переда
        12. L (width*1.5, chest_line) - правая точка линии груди переда
        13. M (width/2 - neckline_width/2, -neckline_depth_front) - левая точка горловины переда
        14. N (width/2 + neckline_width/2, -neckline_depth_front) - правая точка горловины переда
        """
        
        # СПИНКА - основные точки
        back_center_top = Point(0, 0)  # Точка A
        back_left_top = Point(-width / 2, 0)  # Точка B
        back_right_top = Point(width / 2, 0)  # Точка C
        
        # Линия груди
        back_chest_left = Point(-width / 2, chest_line)  # Точка D
        back_chest_right = Point(width / 2, chest_line)  # Точка E
        
        # Горловина спинки
        back_neckline_left = Point(-neckline_width / 2, -neckline_depth_back)  # Точка F
        back_neckline_right = Point(neckline_width / 2, -neckline_depth_back)  # Точка G
        
        # Плечевые точки с учетом наклона
        back_shoulder_left = Point(-width / 2 - shoulder_slope, chest_line * 0.1)
        back_shoulder_right = Point(width / 2 + shoulder_slope, chest_line * 0.1)
        
        # Точки проймы
        back_armhole_left = Point(-width / 2, armhole_depth)
        back_armhole_right = Point(width / 2, armhole_depth)
        
        # ПЕРЕД - основные точки (смещены по горизонтали)
        front_center_top = Point(width, 0)  # Точка H
        front_left_top = Point(width / 2, 0)  # Точка I
        front_right_top = Point(width * 1.5, 0)  # Точка J
        
        # Линия груди переда
        front_chest_left = Point(width / 2, chest_line)  # Точка K
        front_chest_right = Point(width * 1.5, chest_line)  # Точка L
        
        # Горловина переда (глубже спинки)
        front_neckline_left = Point(width / 2 - neckline_width / 2, -neckline_depth_front)  # Точка M
        front_neckline_right = Point(width / 2 + neckline_width / 2, -neckline_depth_front)  # Точка N
        
        # Плечевые точки переда
        front_shoulder_left = Point(width / 2 - shoulder_slope, chest_line * 0.1)
        front_shoulder_right = Point(width * 1.5 + shoulder_slope, chest_line * 0.1)
        
        # Точки проймы переда
        front_armhole_left = Point(width / 2, armhole_depth)
        front_armhole_right = Point(width * 1.5, armhole_depth)
        
        """
        КОНСТРУКТИВНЫЕ ЛИНИИ:
        
        Линии спинки:
        - top_line: верхняя линия от B до C
        - neckline: горловина от F до G
        - shoulder_left: левое плечо от B до плечевой точки
        - shoulder_right: правое плечо от C до плечевой точки
        - armhole_left: левая пройма
        - armhole_right: правая пройма
        - center_back: средний шов спинки
        
        Линии переда:
        - top_line: верхняя линия от I до J
        - neckline: горловина переда от M до N
        - shoulder_left: левое плечо переда
        - shoulder_right: правое плечо переда
        - armhole_left: левая пройма переда
        - armhole_right: правая пройма переда
        - center_front: средний шов переда
        """
        
        # Линии спинки
        back_lines = [
            {
                "name": "top_line",
                "start": {"x": back_left_top.x, "y": back_left_top.y},
                "end": {"x": back_right_top.x, "y": back_right_top.y},
                "type": "construction"
            },
            {
                "name": "neckline",
                "start": {"x": back_neckline_left.x, "y": back_neckline_left.y},
                "end": {"x": back_neckline_right.x, "y": back_neckline_right.y},
                "type": "curve"
            },
            {
                "name": "shoulder_left",
                "start": {"x": back_left_top.x, "y": back_left_top.y},
                "end": {"x": back_shoulder_left.x, "y": back_shoulder_left.y},
                "type": "straight"
            },
            {
                "name": "shoulder_right",
                "start": {"x": back_right_top.x, "y": back_right_top.y},
                "end": {"x": back_shoulder_right.x, "y": back_shoulder_right.y},
                "type": "straight"
            },
            {
                "name": "armhole_left",
                "start": {"x": back_shoulder_left.x, "y": back_shoulder_left.y},
                "end": {"x": back_armhole_left.x, "y": back_armhole_left.y},
                "type": "curve"
            },
            {
                "name": "armhole_right",
                "start": {"x": back_shoulder_right.x, "y": back_shoulder_right.y},
                "end": {"x": back_armhole_right.x, "y": back_armhole_right.y},
                "type": "curve"
            },
            {
                "name": "center_back",
                "start": {"x": back_center_top.x, "y": back_center_top.y},
                "end": {"x": 0, "y": waist_line},
                "type": "straight"
            }
        ]
        
        # Линии переда
        front_lines = [
            {
                "name": "top_line",
                "start": {"x": front_left_top.x, "y": front_left_top.y},
                "end": {"x": front_right_top.x, "y": front_right_top.y},
                "type": "construction"
            },
            {
                "name": "neckline",
                "start": {"x": front_neckline_left.x, "y": front_neckline_left.y},
                "end": {"x": front_neckline_right.x, "y": front_neckline_right.y},
                "type": "curve"
            },
            {
                "name": "shoulder_left",
                "start": {"x": front_left_top.x, "y": front_left_top.y},
                "end": {"x": front_shoulder_left.x, "y": front_shoulder_left.y},
                "type": "straight"
            },
            {
                "name": "shoulder_right",
                "start": {"x": front_right_top.x, "y": front_right_top.y},
                "end": {"x": front_shoulder_right.x, "y": front_shoulder_right.y},
                "type": "straight"
            },
            {
                "name": "armhole_left",
                "start": {"x": front_shoulder_left.x, "y": front_shoulder_left.y},
                "end": {"x": front_armhole_left.x, "y": front_armhole_left.y},
                "type": "curve"
            },
            {
                "name": "armhole_right",
                "start": {"x": front_shoulder_right.x, "y": front_shoulder_right.y},
                "end": {"x": front_armhole_right.x, "y": front_armhole_right.y},
                "type": "curve"
            },
            {
                "name": "center_front",
                "start": {"x": front_center_top.x, "y": front_center_top.y},
                "end": {"x": width, "y": waist_line},
                "type": "straight"
            }
        ]
        
        return {
            "back": {
                "lines": back_lines,
                "construction": "EMKO_shirt_back"
            },
            "front": {
                "lines": front_lines,
                "construction": "EMKO_shirt_front"
            },
            "measurements": measurements,
            "construction_method": "EMKO",
            "garment_type": "shirt",
            "calculations": {
                "width": width,
                "armhole_depth": armhole_depth,
                "neckline_width": neckline_width,
                "neckline_depth_back": neckline_depth_back,
                "neckline_depth_front": neckline_depth_front,
                "shoulder_slope": shoulder_slope
            }
        }
    
    def _create_sleeve_pattern(self, 
                              measurements: Dict[str, float],
                              fit_type: str,
                              construction_method: ConstructionMethod) -> Dict[str, Any]:
        """
        Создание лекала рукава по методике ЕМКО
        
        Методика: ЕМКО (Единая методика конструирования одежды)
        Применяется для классических втачных рукавов
        
        Ключевые мерки:
        - bust: обхват груди (для расчета ширины рукава)
        - arm_length: длина руки
        - armhole_length: длина проймы (из основной конструкции)
        
        Ключевые формулы ЕМКО для рукавов:
        1. Ширина рукава = bust * 0.4 (пропорционально груди)
        2. Высота оката = armhole_length / 3 (соотношение с проймой)
        3. Ширина внизу = bust * 0.15 (пропорционально груди)
        4. Длина рукава = arm_length
        
        Пример расчета для bust = 96 см, armhole_length = 45 см:
        - Ширина рукава = 96 * 0.4 = 38.4 см
        - Высота оката = 45 / 3 = 15.0 см
        - Ширина внизу = 96 * 0.15 = 14.4 см
        - Длина рукава = 60 см (стандартная)
        
        Система координат:
        - Начало (0,0) = верхняя точка оката рукава
        - Ось X → вправо (ширина рукава)
        - Ось Y → вниз (длина рукава)
        """
        
        bust = measurements["bust"]
        arm_length = measurements["arm_length"]
        
        # Расчет размеров рукава по ЕМКО
        sleeve_width = bust * 0.4        # Ширина рукава в самой широкой части
        sleeve_cap_height = bust * 0.15   # Высота оката
        wrist_width = bust * 0.15       # Ширина запястья
        
        """
        КЛЮЧЕВЫЕ ТОЧКИ КОНСТРУКЦИИ РУКАВА:
        
        Окат рукава (Cap):
        1. A (0, 0) - верхняя точка оката
        2. B (-sleeve_width/2, -sleeve_cap_height * 0.3) - левая передняя точка оката
        3. C (sleeve_width/2, -sleeve_cap_height * 0.3) - правая задняя точка оката
        4. D (-wrist_width/2, -arm_length) - левая нижняя точка
        5. E (wrist_width/2, -arm_length) - правая нижняя точка
        
        Контрольные точки для кривой Безье (окат):
        - F (-sleeve_width * 0.3, -sleeve_cap_height * 0.2) - контроль1 передней части
        - G (-sleeve_width * 0.4, -sleeve_cap_height * 0.7) - контроль2 передней части
        - H (sleeve_width * 0.4, -sleeve_cap_height * 0.7) - контроль1 задней части
        - I (sleeve_width * 0.3, -sleeve_cap_height * 0.2) - контроль2 задней части
        """
        
        # Основные точки рукава
        sleeve_cap_top = Point(0, 0)  # Точка A
        sleeve_cap_front = Point(-sleeve_width / 2, -sleeve_cap_height * 0.3)  # Точка B
        sleeve_cap_back = Point(sleeve_width / 2, -sleeve_cap_height * 0.3)  # Точка C
        sleeve_hem_front = Point(-wrist_width / 2, -arm_length)  # Точка D
        sleeve_hem_back = Point(wrist_width / 2, -arm_length)  # Точка E
        
        # Контрольные точки для кривой Безье (окат рукава)
        cap_control_front1 = Point(-sleeve_width * 0.3, -sleeve_cap_height * 0.2)  # Точка F
        cap_control_front2 = Point(-sleeve_width * 0.4, -sleeve_cap_height * 0.7)  # Точка G
        cap_control_back1 = Point(sleeve_width * 0.4, -sleeve_cap_height * 0.7)  # Точка H
        cap_control_back2 = Point(sleeve_width * 0.3, -sleeve_cap_height * 0.2)  # Точка I
        
        # Создаем линии рукава
        lines = {
            "front_seam": {
                "start": {"x": sleeve_cap_front.x, "y": sleeve_cap_front.y},
                "end": {"x": sleeve_hem_front.x, "y": sleeve_hem_front.y},
                "type": "straight",
                "seam_type": "main"
            },
            "back_seam": {
                "start": {"x": sleeve_cap_back.x, "y": sleeve_cap_back.y},
                "end": {"x": sleeve_hem_back.x, "y": sleeve_hem_back.y},
                "type": "straight",
                "seam_type": "main"
            },
            "hem": {
                "start": {"x": sleeve_hem_front.x, "y": sleeve_hem_front.y},
                "end": {"x": sleeve_hem_back.x, "y": sleeve_hem_back.y},
                "type": "straight",
                "seam_type": "hem"
            }
        }
        
        # Окат рукава (кривая Безье)
        curves = {
            "sleeve_cap": {
                "start": {"x": sleeve_cap_front.x, "y": sleeve_cap_front.y},
                "control1": {"x": cap_control_front1.x, "y": cap_control_front1.y},
                "control2": {"x": cap_control_front2.x, "y": cap_control_front2.y},
                "end": {"x": sleeve_cap_top.x, "y": sleeve_cap_top.y},
                "type": "bezier",
                "seam_type": "main"
            },
            "sleeve_cap_back": {
                "start": {"x": sleeve_cap_top.x, "y": sleeve_cap_top.y},
                "control1": {"x": cap_control_back1.x, "y": cap_control_back1.y},
                "control2": {"x": cap_control_back2.x, "y": cap_control_back2.y},
                "end": {"x": sleeve_cap_back.x, "y": sleeve_cap_back.y},
                "type": "bezier",
                "seam_type": "main"
            }
        }
        
        points = {
            "cap_top": {"x": sleeve_cap_top.x, "y": sleeve_cap_top.y, "type": "construction"},
            "cap_front": {"x": sleeve_cap_front.x, "y": sleeve_cap_front.y, "type": "construction"},
            "cap_back": {"x": sleeve_cap_back.x, "y": sleeve_cap_back.y, "type": "construction"},
            "hem_front": {"x": sleeve_hem_front.x, "y": sleeve_hem_front.y, "type": "construction"},
            "hem_back": {"x": sleeve_hem_back.x, "y": sleeve_hem_back.y, "type": "construction"}
        }
        
        return {
            "points": points,
            "lines": lines,
            "curves": curves,
            "construction_method": "EMKO",
            "garment_type": "sleeve",
            "calculations": {
                "sleeve_width": sleeve_width,
                "sleeve_cap_height": sleeve_cap_height,
                "wrist_width": wrist_width,
                "arm_length": arm_length
            }
        }
    
    def build_jacket_base(self, pattern_type: PatternType, measurements: Dict[str, float]) -> Dict[str, Any]:
        """
        Построение базовой конструкции пиджака по итальянской системе
        
        Методика: Итальянская система конструирования пиджаков
        Применяется для классических мужских и женских пиджаков
        
        Ключевые мерки:
        - bust: обхват груди (основная мерка)
        - height: рост
        - shoulder_width: ширина плеч
        - back_length: длина спины до талии
        
        Ключевые формулы итальянской системы:
        1. Ширина = bust/2 + 8.0 см (большая прибавка на свободу)
        2. Глубина проймы = bust/3 + 2.0 см
        3. Длина пиджака = height * 0.45
        4. Ширина лацкана = bust/15 см (по умолчанию)
        5. Длина рукава = height * 0.32
        
        Пример расчета для bust = 96 см, height = 178 см:
        - Ширина = 96/2 + 8.0 = 56.0 см
        - Глубина проймы = 96/3 + 2.0 = 34.0 см
        - Длина пиджака = 178 * 0.45 = 80.1 см
        - Ширина лацкана = 96/15 = 6.4 см
        
        Система координат:
        - Начало (0,0) = верхняя точка середины спинки
        - Ось X → вправо (ширина изделия)
        - Ось Y → вниз (длина изделия)
        
        Лацканы (по умолчанию notch):
        - M, N: точки начала лацканов
        - O, P: точки конца лацканов
        """
        
        # Основные мерки и расчеты по итальянской системе
        chest = measurements["bust"]
        height = measurements["height"]
        back_length = measurements.get("back_length", height * 0.38)
        
        # Ключевые формулы итальянской системы
        half_chest = chest / 2
        ease_chest = 8.0  # Прибавка на свободу по груди для пиджаков
        width = half_chest + ease_chest  # Общая ширина сетки
        
        # Расчет конструктивных линий
        armhole_depth = chest / 3 + 2.0  # Глубина проймы
        jacket_length = height * 0.45  # Длина пиджака
        lapel_width = chest / 15  # Ширина лацкана
        lapel_length = chest / 8  # Длина лацкана
        
        # Расчет положения линий
        chest_line = back_length * 0.3  # Линия груди
        waist_line = back_length  # Линия талии
        hip_line = back_length * 1.2  # Линия бедер
        
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        if pattern_type == PatternType.BODICE_BACK:
            """
            СПИНКА ПИДЖАКА (Bodice Back):
            
            Ключевые точки:
            A (0, 0) - верх середины спинки, базовая точка
            B (-width/2, 0) - левый верхний угол (плечевая точка)
            C (width/2, 0) - правый верхний угол (плечевая точка)
            D (-width/2, armhole_depth) - левая точка проймы
            E (width/2, armhole_depth) - правая точка проймы
            F (0, jacket_length) - низ спинки
            
            Дополнительные точки для точности:
            G (-width/2, chest_line) - левая точка линии груди
            H (width/2, chest_line) - правая точка линии груди
            I (-width/2, waist_line) - левая точка талии
            J (width/2, waist_line) - правая точка талии
            K (-width/2, hip_line) - левая точка бедер
            L (width/2, hip_line) - правая точка бедер
            """
            
            # Основные точки спинки
            A = Point(0, 0)  # верх середины спинки
            B = Point(-width / 2, 0)  # левый верхний угол
            C = Point(width / 2, 0)  # правый верхний угол
            D = Point(-width / 2, armhole_depth)  # левая точка проймы
            E = Point(width / 2, armhole_depth)  # правая точка проймы
            F = Point(0, jacket_length)  # низ спинки
            
            # Дополнительные точки для точности
            G = Point(-width / 2, chest_line)  # левая точка линии груди
            H = Point(width / 2, chest_line)  # правая точка линии груди
            I = Point(-width / 2, waist_line)  # левая точка талии
            J = Point(width / 2, waist_line)  # правая точка талии
            K = Point(-width / 2, hip_line)  # левая точка бедер
            L = Point(width / 2, hip_line)  # правая точка бедер
            
            # Точки для горловины спинки
            neckline_width = chest / 20
            neckline_depth = chest / 40
            M = Point(-neckline_width / 2, -neckline_depth)  # левая точка горловины
            N = Point(neckline_width / 2, -neckline_depth)  # правая точка горловины
            
            # Точки плечевых швов
            shoulder_slope = 3.0  # наклон плеча для пиджака
            O = Point(-width / 2 - shoulder_slope, chest_line * 0.1)  # левая плечевая точка
            P = Point(width / 2 + shoulder_slope, chest_line * 0.1)  # правая плечевая точка
            
            # Точки проймы (более точные)
            Q = Point(-width / 2, armhole_depth * 0.8)  # левая точка проймы
            R = Point(width / 2, armhole_depth * 0.8)  # правая точка проймы
            
            # Точки боковых швов
            S = Point(-width / 2 + 2.0, jacket_length)  # левая точка низа
            T = Point(width / 2 - 2.0, jacket_length)  # правая точка низа
            
            # Линии спинки
            lines = {
                "top_line": {
                    "start": {"x": B.x, "y": B.y},
                    "end": {"x": C.x, "y": C.y},
                    "type": "construction"
                },
                "neckline": {
                    "start": {"x": M.x, "y": M.y},
                    "end": {"x": N.x, "y": N.y},
                    "type": "curve"
                },
                "shoulder_left": {
                    "start": {"x": B.x, "y": B.y},
                    "end": {"x": O.x, "y": O.y},
                    "type": "straight"
                },
                "shoulder_right": {
                    "start": {"x": C.x, "y": C.y},
                    "end": {"x": P.x, "y": P.y},
                    "type": "straight"
                },
                "armhole_left": {
                    "start": {"x": O.x, "y": O.y},
                    "end": {"x": Q.x, "y": Q.y},
                    "type": "curve"
                },
                "armhole_right": {
                    "start": {"x": P.x, "y": P.y},
                    "end": {"x": R.x, "y": R.y},
                    "type": "curve"
                },
                "side_left": {
                    "start": {"x": Q.x, "y": Q.y},
                    "end": {"x": S.x, "y": S.y},
                    "type": "straight"
                },
                "side_right": {
                    "start": {"x": R.x, "y": R.y},
                    "end": {"x": T.x, "y": T.y},
                    "type": "straight"
                },
                "center_back": {
                    "start": {"x": A.x, "y": A.y},
                    "end": {"x": F.x, "y": F.y},
                    "type": "straight"
                },
                "hem": {
                    "start": {"x": S.x, "y": S.y},
                    "end": {"x": T.x, "y": T.y},
                    "type": "straight"
                }
            }
            
            # Кривые проймы (Bezier)
            curves = {
                "armhole_left": {
                    "start": {"x": O.x, "y": O.y},
                    "control1": {"x": O.x - 5.0, "y": O.y + 10.0},
                    "control2": {"x": Q.x - 5.0, "y": Q.y - 5.0},
                    "end": {"x": Q.x, "y": Q.y},
                    "type": "bezier"
                },
                "armhole_right": {
                    "start": {"x": P.x, "y": P.y},
                    "control1": {"x": P.x + 5.0, "y": P.y + 10.0},
                    "control2": {"x": R.x + 5.0, "y": R.y - 5.0},
                    "end": {"x": R.x, "y": R.y},
                    "type": "bezier"
                },
                "neckline": {
                    "start": {"x": M.x, "y": M.y},
                    "control1": {"x": M.x - 2.0, "y": M.y - 1.0},
                    "control2": {"x": N.x + 2.0, "y": N.y - 1.0},
                    "end": {"x": N.x, "y": N.y},
                    "type": "bezier"
                }
            }
            
            # Точки спинки
            points = {
                "A": {"x": A.x, "y": A.y, "type": "construction"},
                "B": {"x": B.x, "y": B.y, "type": "construction"},
                "C": {"x": C.x, "y": C.y, "type": "construction"},
                "D": {"x": D.x, "y": D.y, "type": "construction"},
                "E": {"x": E.x, "y": E.y, "type": "construction"},
                "F": {"x": F.x, "y": F.y, "type": "construction"},
                "G": {"x": G.x, "y": G.y, "type": "construction"},
                "H": {"x": H.x, "y": H.y, "type": "construction"},
                "I": {"x": I.x, "y": I.y, "type": "construction"},
                "J": {"x": J.x, "y": J.y, "type": "construction"},
                "K": {"x": K.x, "y": K.y, "type": "construction"},
                "L": {"x": L.x, "y": L.y, "type": "construction"},
                "M": {"x": M.x, "y": M.y, "type": "construction"},
                "N": {"x": N.x, "y": N.y, "type": "construction"},
                "O": {"x": O.x, "y": O.y, "type": "construction"},
                "P": {"x": P.x, "y": P.y, "type": "construction"},
                "Q": {"x": Q.x, "y": Q.y, "type": "construction"},
                "R": {"x": R.x, "y": R.y, "type": "construction"},
                "S": {"x": S.x, "y": S.y, "type": "construction"},
                "T": {"x": T.x, "y": T.y, "type": "construction"}
            }
            
            logger.info(f"Создано bodice_back: {len(points)} точек")
            
            repattern = {
                "points": points,
                "lines": lines,
                "curves": curves,
                "dataset_adjusted": True,
                "source": "dataset_averaged_transfer",
                "scaling_factors": {
                    "scale_x": 1.0,
                    "scale_y": 1.0,
                    "reference_waist": chest,
                    "reference_hips": chest * 1.2,
                    "patterns_averaged": 1
                },
                "dataset_corrections": {
                    "front_back_balance_applied": False
                }
            }
            
            return repattern
            
        else:  # PatternType.BODICE_FRONT
            """
            ПЕРЕД ПИДЖАКА (Bodice Front):
            
            Ключевые точки:
            G (width, 0) - верх середины переда
            H (width/2, 0) - левый верхний угол переда
            I (width*1.5, 0) - правый верхний угол переда
            J (width/2, armhole_depth) - левая точка проймы
            K (width*1.5, armhole_depth) - правая точка проймы
            L (width, jacket_length) - низ переда
            
            Лацканы (по умолчанию notch):
            M (width/2 - lapel_width, 0) - левая точка начала лацкана
            N (width*1.5 + lapel_width, 0) - правая точка начала лацкана
            O (width/2, lapel_length) - левая точка конца лацкана
            P (width*1.5, lapel_length) - правая точка конца лацкана
            """
            
            # Основные точки переда
            G = Point(width, 0)  # верх середины переда
            H = Point(width / 2, 0)  # левый верхний угол переда
            I = Point(width * 1.5, 0)  # правый верхний угол переда
            J = Point(width / 2, armhole_depth)  # левая точка проймы
            K = Point(width * 1.5, armhole_depth)  # правая точка проймы
            L = Point(width, jacket_length)  # низ переда
            
            # Дополнительные точки для точности
            M = Point(width / 2, chest_line)  # левая точка линии груди
            N = Point(width * 1.5, chest_line)  # правая точка линии груди
            O = Point(width / 2, waist_line)  # левая точка талии
            P = Point(width * 1.5, waist_line)  # правая точка талии
            Q = Point(width / 2, hip_line)  # левая точка бедер
            R = Point(width * 1.5, hip_line)  # правая точка бедер
            
            # Точки для горловины переда
            neckline_width = chest / 20
            neckline_depth = chest / 10 + 0.5
            S = Point(width / 2 - neckline_width / 2, -neckline_depth)  # левая точка горловины
            T = Point(width / 2 + neckline_width / 2, -neckline_depth)  # правая точка горловины
            
            # Точки плечевых швов
            shoulder_slope = 3.0  # наклон плеча для пиджака
            U = Point(width / 2 - shoulder_slope, chest_line * 0.1)  # левая плечевая точка
            V = Point(width * 1.5 + shoulder_slope, chest_line * 0.1)  # правая плечевая точка
            
            # Точки проймы (более точные)
            W = Point(width / 2, armhole_depth * 0.8)  # левая точка проймы
            X = Point(width * 1.5, armhole_depth * 0.8)  # правая точка проймы
            
            # Точки боковых швов
            Y = Point(width / 2 + 2.0, jacket_length)  # левая точка низа
            Z = Point(width * 1.5 - 2.0, jacket_length)  # правая точка низа
            
            # Точки лацканов (notch по умолчанию)
            lapel_start_left = Point(width / 2 - lapel_width, 0)  # M
            lapel_start_right = Point(width * 1.5 + lapel_width, 0)  # N
            lapel_end_left = Point(width / 2, lapel_length)  # O
            lapel_end_right = Point(width * 1.5, lapel_length)  # P
            
            # Линии переда
            lines = {
                "top_line": {
                    "start": {"x": H.x, "y": H.y},
                    "end": {"x": I.x, "y": I.y},
                    "type": "construction"
                },
                "neckline": {
                    "start": {"x": S.x, "y": S.y},
                    "end": {"x": T.x, "y": T.y},
                    "type": "curve"
                },
                "shoulder_left": {
                    "start": {"x": H.x, "y": H.y},
                    "end": {"x": U.x, "y": U.y},
                    "type": "straight"
                },
                "shoulder_right": {
                    "start": {"x": I.x, "y": I.y},
                    "end": {"x": V.x, "y": V.y},
                    "type": "straight"
                },
                "armhole_left": {
                    "start": {"x": U.x, "y": U.y},
                    "end": {"x": W.x, "y": W.y},
                    "type": "curve"
                },
                "armhole_right": {
                    "start": {"x": V.x, "y": V.y},
                    "end": {"x": X.x, "y": X.y},
                    "type": "curve"
                },
                "side_left": {
                    "start": {"x": W.x, "y": W.y},
                    "end": {"x": Y.x, "y": Y.y},
                    "type": "straight"
                },
                "side_right": {
                    "start": {"x": X.x, "y": X.y},
                    "end": {"x": Z.x, "y": Z.y},
                    "type": "straight"
                },
                "center_front": {
                    "start": {"x": G.x, "y": G.y},
                    "end": {"x": L.x, "y": L.y},
                    "type": "straight"
                },
                "hem": {
                    "start": {"x": Y.x, "y": Y.y},
                    "end": {"x": Z.x, "y": Z.y},
                    "type": "straight"
                },
                # Линии лацканов
                "lapel_left": {
                    "start": {"x": lapel_start_left.x, "y": lapel_start_left.y},
                    "end": {"x": lapel_end_left.x, "y": lapel_end_left.y},
                    "type": "curve"
                },
                "lapel_right": {
                    "start": {"x": lapel_start_right.x, "y": lapel_start_right.y},
                    "end": {"x": lapel_end_right.x, "y": lapel_end_right.y},
                    "type": "curve"
                }
            }
            
            # Кривые проймы и лацканов (Bezier)
            curves = {
                "armhole_left": {
                    "start": {"x": U.x, "y": U.y},
                    "control1": {"x": U.x - 5.0, "y": U.y + 10.0},
                    "control2": {"x": W.x - 5.0, "y": W.y - 5.0},
                    "end": {"x": W.x, "y": W.y},
                    "type": "bezier"
                },
                "armhole_right": {
                    "start": {"x": V.x, "y": V.y},
                    "control1": {"x": V.x + 5.0, "y": V.y + 10.0},
                    "control2": {"x": X.x + 5.0, "y": X.y - 5.0},
                    "end": {"x": X.x, "y": X.y},
                    "type": "bezier"
                },
                "neckline": {
                    "start": {"x": S.x, "y": S.y},
                    "control1": {"x": S.x - 2.0, "y": S.y - 1.0},
                    "control2": {"x": T.x + 2.0, "y": T.y - 1.0},
                    "end": {"x": T.x, "y": T.y},
                    "type": "bezier"
                },
                "lapel_left": {
                    "start": {"x": lapel_start_left.x, "y": lapel_start_left.y},
                    "control1": {"x": lapel_start_left.x - 1.0, "y": lapel_start_left.y + lapel_length * 0.3},
                    "control2": {"x": lapel_end_left.x - 1.0, "y": lapel_end_left.y - lapel_length * 0.3},
                    "end": {"x": lapel_end_left.x, "y": lapel_end_left.y},
                    "type": "bezier"
                },
                "lapel_right": {
                    "start": {"x": lapel_start_right.x, "y": lapel_start_right.y},
                    "control1": {"x": lapel_start_right.x + 1.0, "y": lapel_start_right.y + lapel_length * 0.3},
                    "control2": {"x": lapel_end_right.x + 1.0, "y": lapel_end_right.y - lapel_length * 0.3},
                    "end": {"x": lapel_end_right.x, "y": lapel_end_right.y},
                    "type": "bezier"
                }
            }
            
            # Точки переда
            points = {
                "G": {"x": G.x, "y": G.y, "type": "construction"},
                "H": {"x": H.x, "y": H.y, "type": "construction"},
                "I": {"x": I.x, "y": I.y, "type": "construction"},
                "J": {"x": J.x, "y": J.y, "type": "construction"},
                "K": {"x": K.x, "y": K.y, "type": "construction"},
                "L": {"x": L.x, "y": L.y, "type": "construction"},
                "M": {"x": M.x, "y": M.y, "type": "construction"},
                "N": {"x": N.x, "y": N.y, "type": "construction"},
                "O": {"x": O.x, "y": O.y, "type": "construction"},
                "P": {"x": P.x, "y": P.y, "type": "construction"},
                "Q": {"x": Q.x, "y": Q.y, "type": "construction"},
                "R": {"x": R.x, "y": R.y, "type": "construction"},
                "S": {"x": S.x, "y": S.y, "type": "construction"},
                "T": {"x": T.x, "y": T.y, "type": "construction"},
                "U": {"x": U.x, "y": U.y, "type": "construction"},
                "V": {"x": V.x, "y": V.y, "type": "construction"},
                "W": {"x": W.x, "y": W.y, "type": "construction"},
                "X": {"x": X.x, "y": X.y, "type": "construction"},
                "Y": {"x": Y.x, "y": Y.y, "type": "construction"},
                "Z": {"x": Z.x, "y": Z.y, "type": "construction"},
                # Точки лацканов
                "lapel_start_left": {"x": lapel_start_left.x, "y": lapel_start_left.y, "type": "construction"},
                "lapel_start_right": {"x": lapel_start_right.x, "y": lapel_start_right.y, "type": "construction"},
                "lapel_end_left": {"x": lapel_end_left.x, "y": lapel_end_left.y, "type": "construction"},
                "lapel_end_right": {"x": lapel_end_right.x, "y": lapel_end_right.y, "type": "construction"}
            }
            
            logger.info(f"Создано bodice_front: {len(points)} точек")
            
            return {
                "points": points,
                "lines": lines,
                "curves": curves,
                "construction_method": "Italian",
                "garment_type": "jacket",
                "pattern_half": "front",
                "calculations": {
                    "width": width,
                    "armhole_depth": armhole_depth,
                    "jacket_length": jacket_length,
                    "lapel_width": lapel_width,
                    "lapel_length": lapel_length,
                    "chest_line": chest_line,
                    "waist_line": waist_line,
                    "hip_line": hip_line
                }
            }
    
    def _create_skirt_pattern(self, 
                              pattern_type: PatternType,
                              measurements: Dict[str, float],
                              fit_type: str,
                              construction_method: ConstructionMethod,
                              dataset_integration=None,
                              similar_patterns=None) -> Dict[str, Any]:
        """
        Создание лекала юбки по Французской методике
        
        Методика: Французская система конструирования
        Применяется для классических прямых юбок
        
        Ключевые мерки:
        - waist: обхват талии
        - hips: обхват бедер
        - height: рост (для расчета длины)
        
        Ключевые формулы Французской системы:
        1. Ширина по талии = waist/4 + 1.0 см (прибавка)
        2. Ширина по бедрам = hips/4 + 2.0 см (прибавка)
        3. Длина юбки = height * 0.40
        4. Положение линии бедер = height * 0.18
        5. Глубина вытачек = (hips - waist) / 8
        
        Пример расчета для waist = 68 см, hips = 94 см, height = 164 см:
        - Ширина по талии = 68/4 + 1.0 = 18.0 см
        - Ширина по бедрам = 94/4 + 2.0 = 25.5 см
        - Длина юбки = 164 * 0.40 = 65.6 см
        - Положение линии бедер = 164 * 0.18 = 29.5 см
        - Глубина вытачек = (94 - 68) / 8 = 3.25 см
        
        Система координат:
        - Начало (0,0) = верх середины юбки (линия талии)
        - Ось X → вправо (ширина юбки)
        - Ось Y → вниз (длина юбки)
        """
        
        waist = measurements["waist"]
        hips = measurements["hips"]
        height = measurements["height"]
        
        # ПАТЧ №4: Реальное влияние датасета на лекала
        # Если найдены похожие паттерны - усредняем 3-5 лучших
        if similar_patterns:
            # Берем 3-5 лучших паттернов для усреднения
            patterns_to_average = similar_patterns[:min(5, len(similar_patterns))]
            
            # Усредняем точки из нескольких паттернов
            averaged_points = {}
            all_point_names = set()
            
            # Собираем все имена точек из всех паттернов
            for pattern_info in patterns_to_average:
                pattern = pattern_info["pattern"]
                all_point_names.update(pattern.get("points", {}).keys())
            
            # Усредняем координаты для каждой точки
            for point_name in all_point_names:
                x_coords = []
                y_coords = []
                types = []
                
                for pattern_info in patterns_to_average:
                    pattern = pattern_info["pattern"]
                    point = pattern.get("points", {}).get(point_name)
                    if point:
                        x_coords.append(point.get("x", 0))
                        y_coords.append(point.get("y", 0))
                        types.append(point.get("type", "construction"))
                
                if x_coords and y_coords:
                    averaged_points[point_name] = {
                        "x": sum(x_coords) / len(x_coords),
                        "y": sum(y_coords) / len(y_coords),
                        "type": types[0] if types else "construction"  # Берем наиболее частый тип
                    }
            
            # Усредняем метаданные для масштабирования
            ref_measures = []
            for pattern_info in patterns_to_average:
                pattern = pattern_info["pattern"]
                metadata = pattern.get("metadata", {})
                ref_measures.append({
                    "waist": metadata.get("waist", 68),
                    "hips": metadata.get("hips", 94)
                })
            
            # Вычисляем средние измерения
            avg_waist = sum(m["waist"] for m in ref_measures) / len(ref_measures)
            avg_hips = sum(m["hips"] for m in ref_measures) / len(ref_measures)
            
            # Рассчитываем коэффициенты масштабирования
            scale_x = measurements["hips"] / avg_hips if avg_hips > 0 else 1.0
            scale_y = measurements["waist"] / avg_waist if avg_waist > 0 else 1.0
            
            # Применяем масштабирование к усредненным точкам
            final_points = {}
            for p_name, p_data in averaged_points.items():
                final_points[p_name] = {
                    "x": p_data["x"] * scale_x,
                    "y": p_data["y"] * scale_y,
                    "type": p_data.get("type", "construction")
                }
            
            # БАЛАНС ПЕРЕД/СПИНКА: Вычисляем длину бокового шва и корректируем Y-смещение
            if pattern_type == PatternType.SKIRT_BACK:
                # Находим боковые точки для вычисления длины бокового шва
                side_points = []
                for p_name, p_data in final_points.items():
                    if 'side' in p_name.lower() or 'hip' in p_name.lower():
                        side_points.append((p_name, p_data))
                
                if len(side_points) >= 2:
                    # Вычисляем длину бокового шва (разница Y между крайними точками)
                    y_coords = [p[1].get('y', 0) for p in side_points]
                    side_seam_length = max(y_coords) - min(y_coords) if len(y_coords) > 1 else 0
                    
                    # Корректируем Y-смещение задней половинки для баланса
                    balance_correction = side_seam_length * 0.05  # 5% от длины бокового шва
                    
                    # Применяем корректировку к центральным точкам задней половинки
                    for p_name, p_data in final_points.items():
                        if 'center' in p_name.lower() or 'back' in p_name.lower():
                            p_data['y'] += balance_correction
                    
                    print(f"Applied front/back balance: correction={balance_correction:.1f}, side_seam={side_seam_length:.1f}")
            
            # Усредняем линии и кривые (БЕЗ усреднения - берем из первого паттерна)
            ref_pattern = patterns_to_average[0]["pattern"]
            averaged_lines = ref_pattern.get("lines", {})
            all_curves = ref_pattern.get("curves", {})
            
            print(f"Using dataset averaged transfer: scale_x={scale_x:.3f}, scale_y={scale_y:.3f}, patterns={len(patterns_to_average)}")
            
            # Определяем баланс перед/спинка для метаданных
            balance_applied = pattern_type == PatternType.SKIRT_BACK
            
            # Генерируем CAD constraints на основе топологии точек
            constraints = self._generate_pattern_constraints(final_points, pattern_type)
            
            pattern = {
                "points": final_points,
                "lines": averaged_lines,
                "curves": all_curves,
                "constraints": constraints,
                "dataset_adjusted": True,
                "source": "dataset_averaged_transfer",
                "scaling_factors": {
                    "scale_x": scale_x,
                    "scale_y": scale_y,
                    "reference_waist": avg_waist,
                    "reference_hips": avg_hips,
                    "patterns_averaged": len(patterns_to_average)
                },
                "dataset_corrections": {
                    "front_back_balance_applied": balance_applied
                }
            }
            
            return pattern
        
        # Расчет размеров юбки по Французской методике
        width_waist = waist / 4 + 1.0  # Ширина по талии с прибавкой
        width_hips = hips / 4 + 2.0   # Ширина по бедрам с прибавкой
        skirt_length = height * 0.40     # Длина юбки
        hip_line_y = height * 0.18       # Положение линии бедер
        
        # Ширина низа (легкий клёш)
        hem_width = width_hips + 5.0
        
        # Глубина вытачек на талии
        dart_depth = (hips - waist) / 8
        
        # Смещение для задней половинки
        back_offset = width_waist * 2.5
        
        # Передняя половинка юбки (skirt_front)
        if pattern_type == PatternType.SKIRT_FRONT:
            # Основные точки передней половинки
            point_A = Point(0, 0)                                    # A - середина талии переда
            point_B = Point(-width_waist, 0)                           # B - левый бок талии
            point_C = Point(width_waist, 0)                            # C - правый бок талии
            point_D = Point(-width_hips, hip_line_y)                    # D - левый бок бедер
            point_E = Point(width_hips, hip_line_y)                     # E - правый бок бедер
            point_F = Point(-hem_width, skirt_length)                   # F - левый бок низа
            point_G = Point(hem_width, skirt_length)                    # G - правый бок низа
            
            # Вытачки на талии (дополнительные точки для >15 точек)
            dart_left_start = Point(-width_waist * 0.3, 0)           # Начало левой вытачки
            dart_left_end = Point(-width_waist * 0.3, dart_depth)    # Конец левой вытачки
            dart_right_start = Point(width_waist * 0.3, 0)           # Начало правой вытачки
            dart_right_end = Point(width_waist * 0.3, dart_depth)     # Конец правой вытачки
            
            # Дополнительные конструктивные точки
            hip_center = Point(0, hip_line_y)                        # Центр линии бедер
            hem_center = Point(0, skirt_length)                       # Центр низа
            side_left_mid = Point(-width_waist, hip_line_y * 0.5)     # Середина левого бока
            side_right_mid = Point(width_waist, hip_line_y * 0.5)     # Середина правого бока
            
            # Дополнительные точки для >15
            waist_left_mid = Point(-width_waist * 0.5, 0)           # Середина левого участка талии
            waist_right_mid = Point(width_waist * 0.5, 0)          # Середина правого участка талии
            hip_left_mid = Point(-width_hips * 0.5, hip_line_y)      # Середина левого участка бедер
            hip_right_mid = Point(width_hips * 0.5, hip_line_y)       # Середина правого участка бедер
            hem_left_mid = Point(-hem_width * 0.5, skirt_length)    # Середина левого участка низа
            hem_right_mid = Point(hem_width * 0.5, skirt_length)     # Середина правого участка низа
            
            # Линии передней половинки
            lines = {
                "waist_line": {
                    "start": {"x": point_B.x, "y": point_B.y},
                    "end": {"x": point_C.x, "y": point_C.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "center_front": {
                    "start": {"x": point_A.x, "y": point_A.y},
                    "end": {"x": hem_center.x, "y": hem_center.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "left_side": {
                    "start": {"x": point_B.x, "y": point_B.y},
                    "end": {"x": point_F.x, "y": point_F.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "right_side": {
                    "start": {"x": point_C.x, "y": point_C.y},
                    "end": {"x": point_G.x, "y": point_G.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "hip_line": {
                    "start": {"x": point_D.x, "y": point_D.y},
                    "end": {"x": point_E.x, "y": point_E.y},
                    "type": "straight",
                    "seam_type": "construction"
                },
                "hem_line": {
                    "start": {"x": point_F.x, "y": point_F.y},
                    "end": {"x": point_G.x, "y": point_G.y},
                    "type": "straight",
                    "seam_type": "hem"
                },
                "dart_left": {
                    "start": {"x": dart_left_start.x, "y": dart_left_start.y},
                    "end": {"x": dart_left_end.x, "y": dart_left_end.y},
                    "type": "straight",
                    "seam_type": "dart"
                },
                "dart_right": {
                    "start": {"x": dart_right_start.x, "y": dart_right_start.y},
                    "end": {"x": dart_right_end.x, "y": dart_right_end.y},
                    "type": "straight",
                    "seam_type": "dart"
                }
            }
            
            # Точки передней половинки
            points = {
                "A": {"x": point_A.x, "y": point_A.y, "type": "construction"},
                "B": {"x": point_B.x, "y": point_B.y, "type": "construction"},
                "C": {"x": point_C.x, "y": point_C.y, "type": "construction"},
                "D": {"x": point_D.x, "y": point_D.y, "type": "construction"},
                "E": {"x": point_E.x, "y": point_E.y, "type": "construction"},
                "F": {"x": point_F.x, "y": point_F.y, "type": "construction"},
                "G": {"x": point_G.x, "y": point_G.y, "type": "construction"},
                "dart_left_start": {"x": dart_left_start.x, "y": dart_left_start.y, "type": "construction"},
                "dart_left_end": {"x": dart_left_end.x, "y": dart_left_end.y, "type": "construction"},
                "dart_right_start": {"x": dart_right_start.x, "y": dart_right_start.y, "type": "construction"},
                "dart_right_end": {"x": dart_right_end.x, "y": dart_right_end.y, "type": "construction"},
                "hip_center": {"x": hip_center.x, "y": hip_center.y, "type": "construction"},
                "hem_center": {"x": hem_center.x, "y": hem_center.y, "type": "construction"},
                "side_left_mid": {"x": side_left_mid.x, "y": side_left_mid.y, "type": "construction"},
                "side_right_mid": {"x": side_right_mid.x, "y": side_right_mid.y, "type": "construction"},
                "waist_left_mid": {"x": waist_left_mid.x, "y": waist_left_mid.y, "type": "construction"},
                "waist_right_mid": {"x": waist_right_mid.x, "y": waist_right_mid.y, "type": "construction"},
                "hip_left_mid": {"x": hip_left_mid.x, "y": hip_left_mid.y, "type": "construction"},
                "hip_right_mid": {"x": hip_right_mid.x, "y": hip_right_mid.y, "type": "construction"},
                "hem_left_mid": {"x": hem_left_mid.x, "y": hem_left_mid.y, "type": "construction"},
                "hem_right_mid": {"x": hem_right_mid.x, "y": hem_right_mid.y, "type": "construction"}
            }
            
            # Логирование
            import logging
            logging.info(f"Создано skirt_front: {len(points)} точек")
            
            # Генерируем CAD constraints для базового паттерна
            constraints = self._generate_pattern_constraints(points, pattern_type)
            
            return {
                "points": points,
                "lines": lines,
                "curves": {},
                "constraints": constraints,
                "construction_method": "French",
                "garment_type": "skirt",
                "pattern_half": pattern_type.value,
                "calculations": {
                    "width_waist": width_waist,
                    "width_hips": width_hips,
                    "skirt_length": skirt_length,
                    "hip_line_y": hip_line_y,
                    "hem_width": hem_width,
                    "dart_depth": dart_depth,
                    "back_offset": back_offset
                }
            }
            
        # Задняя половинка юбки (skirt_back)
        else:  # PatternType.SKIRT_BACK
            # Расчет размеров для задней половинки
            back_waist_width = width_waist
            back_hip_width = width_hips
            back_hem_width = hem_width
            
            # Основные точки задней половинки
            point_H = Point(back_offset, 0)                                         # H - середина талии спинки
            point_I = Point(back_offset - back_waist_width, 0)                        # I - левый бок талии
            point_J = Point(back_offset + back_waist_width, 0)                        # J - правый бок талии
            point_K = Point(back_offset - back_hip_width, hip_line_y)                   # K - левый бок бедер
            point_L = Point(back_offset + back_hip_width, hip_line_y)                    # L - правый бок бедер
            point_M = Point(back_offset - back_hem_width, skirt_length)                  # M - левый бок низа
            point_N = Point(back_offset + back_hem_width, skirt_length)                   # N - правый бок низа
            
            # Вытачки на талии спинки (более глубокие)
            back_dart_depth = dart_depth * 1.2
            dart_back_left_start = Point(back_offset - back_waist_width * 0.3, 0)      # Начало левой вытачки
            dart_back_left_end = Point(back_offset - back_waist_width * 0.3, back_dart_depth)   # Конец левой вытачки
            dart_back_right_start = Point(back_offset + back_waist_width * 0.3, 0)     # Начало правой вытачки
            dart_back_right_end = Point(back_offset + back_waist_width * 0.3, back_dart_depth) # Конец правой вытачки
            
            # Дополнительные конструктивные точки
            hip_back_center = Point(back_offset, hip_line_y)               # Центр линии бедер спинки
            hem_back_center = Point(back_offset, skirt_length)              # Центр низа спинки
            side_back_left_mid = Point(back_offset - back_waist_width, hip_line_y * 0.5)  # Середина левого бока
            side_back_right_mid = Point(back_offset + back_waist_width, hip_line_y * 0.5) # Середина правого бока
            
            # Дополнительные точки для >15
            waist_back_left_mid = Point(back_offset - back_waist_width * 0.5, 0)     # Середина левого участка талии
            waist_back_right_mid = Point(back_offset + back_waist_width * 0.5, 0)    # Середина правого участка талии
            hip_back_left_mid = Point(back_offset - back_hip_width * 0.5, hip_line_y)      # Середина левого участка бедер
            hip_back_right_mid = Point(back_offset + back_hip_width * 0.5, hip_line_y)       # Середина правого участка бедер
            hem_back_left_mid = Point(back_offset - back_hem_width * 0.5, skirt_length)    # Середина левого участка низа
            hem_back_right_mid = Point(back_offset + back_hem_width * 0.5, skirt_length)     # Середина правого участка низа
            
            # Линии задней половинки
            lines = {
                "waist_line": {
                    "start": {"x": point_I.x, "y": point_I.y},
                    "end": {"x": point_J.x, "y": point_J.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "center_back": {
                    "start": {"x": point_H.x, "y": point_H.y},
                    "end": {"x": hem_back_center.x, "y": hem_back_center.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "left_side": {
                    "start": {"x": point_I.x, "y": point_I.y},
                    "end": {"x": point_M.x, "y": point_M.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "right_side": {
                    "start": {"x": point_J.x, "y": point_J.y},
                    "end": {"x": point_N.x, "y": point_N.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "hip_line": {
                    "start": {"x": point_K.x, "y": point_K.y},
                    "end": {"x": point_L.x, "y": point_L.y},
                    "type": "straight",
                    "seam_type": "construction"
                },
                "hem_line": {
                    "start": {"x": point_M.x, "y": point_M.y},
                    "end": {"x": point_N.x, "y": point_N.y},
                    "type": "straight",
                    "seam_type": "hem"
                },
                "dart_left": {
                    "start": {"x": dart_back_left_start.x, "y": dart_back_left_start.y},
                    "end": {"x": dart_back_left_end.x, "y": dart_back_left_end.y},
                    "type": "straight",
                    "seam_type": "dart"
                },
                "dart_right": {
                    "start": {"x": dart_back_right_start.x, "y": dart_back_right_start.y},
                    "end": {"x": dart_back_right_end.x, "y": dart_back_right_end.y},
                    "type": "straight",
                    "seam_type": "dart"
                }
            }
            
            # Точки задней половинки
            points = {
                "H": {"x": point_H.x, "y": point_H.y, "type": "construction"},
                "I": {"x": point_I.x, "y": point_I.y, "type": "construction"},
                "J": {"x": point_J.x, "y": point_J.y, "type": "construction"},
                "K": {"x": point_K.x, "y": point_K.y, "type": "construction"},
                "L": {"x": point_L.x, "y": point_L.y, "type": "construction"},
                "M": {"x": point_M.x, "y": point_M.y, "type": "construction"},
                "N": {"x": point_N.x, "y": point_N.y, "type": "construction"},
                "dart_back_left_start": {"x": dart_back_left_start.x, "y": dart_back_left_start.y, "type": "construction"},
                "dart_back_left_end": {"x": dart_back_left_end.x, "y": dart_back_left_end.y, "type": "construction"},
                "dart_back_right_start": {"x": dart_back_right_start.x, "y": dart_back_right_start.y, "type": "construction"},
                "dart_back_right_end": {"x": dart_back_right_end.x, "y": dart_back_right_end.y, "type": "construction"},
                "hip_back_center": {"x": hip_back_center.x, "y": hip_back_center.y, "type": "construction"},
                "hem_back_center": {"x": hem_back_center.x, "y": hem_back_center.y, "type": "construction"},
                "side_back_left_mid": {"x": side_back_left_mid.x, "y": side_back_left_mid.y, "type": "construction"},
                "side_back_right_mid": {"x": side_back_right_mid.x, "y": side_back_right_mid.y, "type": "construction"},
                "waist_back_left_mid": {"x": waist_back_left_mid.x, "y": waist_back_left_mid.y, "type": "construction"},
                "waist_back_right_mid": {"x": waist_back_right_mid.x, "y": waist_back_right_mid.y, "type": "construction"},
                "hip_back_left_mid": {"x": hip_back_left_mid.x, "y": hip_back_left_mid.y, "type": "construction"},
                "hip_back_right_mid": {"x": hip_back_right_mid.x, "y": hip_back_right_mid.y, "type": "construction"},
                "hem_back_left_mid": {"x": hem_back_left_mid.x, "y": hem_back_left_mid.y, "type": "construction"},
                "hem_back_right_mid": {"x": hem_back_right_mid.x, "y": hem_back_right_mid.y, "type": "construction"}
            }
            
            # Логирование
            import logging
            logging.info(f"Создано skirt_back: {len(points)} точек")
        
        # Генерируем CAD constraints для базового паттерна
        constraints = self._generate_pattern_constraints(points, pattern_type)
        
        return {
            "points": points,
            "lines": lines,
            "curves": {},
            "constraints": constraints,
            "construction_method": "French",
            "garment_type": "skirt",
            "pattern_half": pattern_type.value,
            "calculations": {
                "width_waist": width_waist,
                "width_hips": width_hips,
                "skirt_length": skirt_length,
                "hip_line_y": hip_line_y,
                "hem_width": hem_width,
                "dart_depth": dart_depth,
                "back_offset": back_offset if pattern_type == PatternType.SKIRT_BACK else 0
            }
        }
    
    def _create_pants_pattern(self, 
                              pattern_type: PatternType,
                              measurements: Dict[str, float],
                              fit_type: str,
                              construction_method: ConstructionMethod) -> Dict[str, Any]:
        """
        Создание лекала брюк по Американской методике
        
        Методика: Американская система конструирования
        Применяется для классических прямых брюк
        
        Ключевые мерки:
        - waist: обхват талии
        - hips: обхват бедер
        - height: рост (для расчета длины)
        - inseam: длина ноги по внутреннему шву (опционально)
        
        Ключевые формулы Американской системы:
        1. Ширина по талии = waist/4 + 2.0 см (прибавка)
        2. Ширина по бедрам = hips/4 + 1.0 см (прибавка)
        3. Глубина шага = height * 0.25
        4. Длина ноги = height * 0.75
        5. Ширина шага = hips/8 + 1.0 см
        
        Пример расчета для waist = 82 см, hips = 96 см, height = 174 см:
        - Ширина по талии = 82/4 + 2.0 = 22.5 см
        - Ширина по бедрам = 96/4 + 1.0 = 25.0 см
        - Глубина шага = 174 * 0.25 = 43.5 см
        - Длина ноги = 174 * 0.75 = 130.5 см
        - Ширина шага = 96/8 + 1.0 = 13.0 см
        
        Система координат:
        - Начало (0,0) = верх середины переда/спинки (линия талии)
        - Ось X → вправо (ширина брюк)
        - Ось Y → вниз (длина брюк)
        """
        
        waist = measurements["waist"]
        hips = measurements["hips"]
        height = measurements["height"]
        
        # Прибавки на свободу
        ease_waist = 2.0  # Прибавка на талию
        ease_hips = 1.0   # Прибавка на бедра
        
        # Расчет размеров брюк по Американской методике
        waist_with_ease = waist + ease_waist
        hips_with_ease = hips + ease_hips
        
        # Размеры для половинки брюк
        front_waist_width = waist_with_ease / 4
        front_hip_width = hips_with_ease / 4
        back_waist_width = waist_with_ease / 4
        back_hip_width = hips_with_ease / 4
        
        # Длина и положение линий
        crotch_depth = height * 0.25  # Глубина шага
        leg_length = height * 0.75     # Длина ноги
        total_length = crotch_depth + leg_length  # Общая длина
        
        # Ширина шага
        front_crotch_width = hips / 8 + 1.0
        back_crotch_width = hips / 6 + 2.0  # Задняя часть шире
        
        # Ширина низа (щиколотка)
        front_ankle_width = (waist_with_ease / 4) * 0.8
        back_ankle_width = (waist_with_ease / 4) * 0.9
        
        """
        КЛЮЧЕВЫЕ ТОЧКИ КОНСТРУКЦИИ БРЮК:
        
        Передняя половинка (Front):
        1. A (0, 0) - верх середины переда
        2. B (-front_waist_width, 0) - левый бок талии
        3. C (front_waist_width, 0) - правый бок талии
        4. D (-front_hip_width, crotch_depth) - левый бок бедер
        5. E (front_hip_width, crotch_depth) - правый бок бедер
        6. F (0, crotch_depth) - середина шага
        7. G (-front_ankle_width, total_length) - левая щиколотка
        8. H (front_ankle_width, total_length) - правая щиколотка
        
        Задняя половинка (Back):
        9. I (back_offset, 0) - верх середины спинки (со смещением)
        10. J (-back_waist_width + back_offset, 0) - левый бок талии спинки
        11. K (back_waist_width + back_offset, 0) - правый бок талии спинки
        12. L (-back_hip_width + back_offset, crotch_depth) - левый бок бедер спинки
        13. M (back_hip_width + back_offset, crotch_depth) - правый бок бедер спинки
        14. N (back_offset, crotch_depth) - середина шага спинки
        15. O (-back_ankle_width + back_offset, total_length) - левая щиколотка спинки
        16. P (back_ankle_width + back_offset, total_length) - правая щиколотка спинки
        """
        
        # Смещение для задней половинки
        back_offset = front_waist_width * 2.5
        
        # Передняя половинка брюк
        if pattern_type == PatternType.PANTS_FRONT:
            # Основные точки переда
            waist_center = Point(0, 0)  # Точка A
            waist_left = Point(-front_waist_width, 0)  # Точка B
            waist_right = Point(front_waist_width, 0)  # Точка C
            
            hip_left = Point(-front_hip_width, crotch_depth)  # Точка D
            hip_right = Point(front_hip_width, crotch_depth)  # Точка E
            crotch_center = Point(0, crotch_depth)  # Точка F
            
            ankle_left = Point(-front_ankle_width, total_length)  # Точка G
            ankle_right = Point(front_ankle_width, total_length)  # Точка H
            
            # Линии передней половинки
            lines = {
                "waist": {
                    "start": {"x": waist_left.x, "y": waist_left.y},
                    "end": {"x": waist_right.x, "y": waist_right.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "center_front": {
                    "start": {"x": waist_center.x, "y": waist_center.y},
                    "end": {"x": crotch_center.x, "y": crotch_center.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "side_seam": {
                    "start": {"x": waist_right.x, "y": waist_right.y},
                    "end": {"x": ankle_right.x, "y": ankle_right.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "inseam": {
                    "start": {"x": crotch_center.x, "y": crotch_center.y},
                    "end": {"x": ankle_right.x, "y": ankle_right.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "hem": {
                    "start": {"x": ankle_left.x, "y": ankle_left.y},
                    "end": {"x": ankle_right.x, "y": ankle_right.y},
                    "type": "straight",
                    "seam_type": "hem"
                },
                "crotch_curve": {
                    "start": {"x": hip_right.x, "y": hip_right.y},
                    "end": {"x": crotch_center.x, "y": crotch_center.y},
                    "type": "curve",
                    "seam_type": "main"
                }
            }
            
            points = {
                "waist_center": {"x": waist_center.x, "y": waist_center.y, "type": "construction"},
                "waist_left": {"x": waist_left.x, "y": waist_left.y, "type": "construction"},
                "waist_right": {"x": waist_right.x, "y": waist_right.y, "type": "construction"},
                "hip_left": {"x": hip_left.x, "y": hip_left.y, "type": "construction"},
                "hip_right": {"x": hip_right.x, "y": hip_right.y, "type": "construction"},
                "crotch_center": {"x": crotch_center.x, "y": crotch_center.y, "type": "construction"},
                "ankle_left": {"x": ankle_left.x, "y": ankle_left.y, "type": "construction"},
                "ankle_right": {"x": ankle_right.x, "y": ankle_right.y, "type": "construction"}
            }
        
        # Задняя половинка брюк
        else:  # PatternType.PANTS_BACK
            # Основные точки спинки
            waist_center = Point(back_offset, 0)  # Точка I
            waist_left = Point(-back_waist_width + back_offset, 0)  # Точка J
            waist_right = Point(back_waist_width + back_offset, 0)  # Точка K
            
            hip_left = Point(-back_hip_width + back_offset, crotch_depth)  # Точка L
            hip_right = Point(back_hip_width + back_offset, crotch_depth)  # Точка M
            crotch_center = Point(back_offset, crotch_depth)  # Точка N
            
            ankle_left = Point(-back_ankle_width + back_offset, total_length)  # Точка O
            ankle_right = Point(back_ankle_width + back_offset, total_length)  # Точка P
            
            # Линии задней половинки
            lines = {
                "waist": {
                    "start": {"x": waist_left.x, "y": waist_left.y},
                    "end": {"x": waist_right.x, "y": waist_right.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "center_back": {
                    "start": {"x": waist_center.x, "y": waist_center.y},
                    "end": {"x": crotch_center.x, "y": crotch_center.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "side_seam": {
                    "start": {"x": waist_right.x, "y": waist_right.y},
                    "end": {"x": ankle_right.x, "y": ankle_right.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "inseam": {
                    "start": {"x": crotch_center.x, "y": crotch_center.y},
                    "end": {"x": ankle_right.x, "y": ankle_right.y},
                    "type": "straight",
                    "seam_type": "main"
                },
                "hem": {
                    "start": {"x": ankle_left.x, "y": ankle_left.y},
                    "end": {"x": ankle_right.x, "y": ankle_right.y},
                    "type": "straight",
                    "seam_type": "hem"
                },
                "crotch_curve": {
                    "start": {"x": hip_right.x, "y": hip_right.y},
                    "end": {"x": crotch_center.x, "y": crotch_center.y},
                    "type": "curve",
                    "seam_type": "main"
                }
            }
            
            points = {
                "waist_center": {"x": waist_center.x, "y": waist_center.y, "type": "construction"},
                "waist_left": {"x": waist_left.x, "y": waist_left.y, "type": "construction"},
                "waist_right": {"x": waist_right.x, "y": waist_right.y, "type": "construction"},
                "hip_left": {"x": hip_left.x, "y": hip_left.y, "type": "construction"},
                "hip_right": {"x": hip_right.x, "y": hip_right.y, "type": "construction"},
                "crotch_center": {"x": crotch_center.x, "y": crotch_center.y, "type": "construction"},
                "ankle_left": {"x": ankle_left.x, "y": ankle_left.y, "type": "construction"},
                "ankle_right": {"x": ankle_right.x, "y": ankle_right.y, "type": "construction"}
            }
        
        return {
            "points": points,
            "lines": lines,
            "curves": {},
            "construction_method": "American",
            "garment_type": "pants",
            "pattern_half": pattern_type.value,
            "calculations": {
                "waist_width": front_waist_width if pattern_type == PatternType.PANTS_FRONT else back_waist_width,
                "hip_width": front_hip_width if pattern_type == PatternType.PANTS_FRONT else back_hip_width,
                "crotch_depth": crotch_depth,
                "leg_length": leg_length,
                "total_length": total_length,
                "ankle_width": front_ankle_width if pattern_type == PatternType.PANTS_FRONT else back_ankle_width
            }
        }
    
    def _create_simple_pattern(self, 
                              pattern_type: PatternType,
                              measurements: Dict[str, float]) -> Dict[str, Any]:
        """Создание простого лекала (воротник, манжета, карман)"""
        
        if pattern_type == PatternType.COLLAR:
            return self._create_collar_pattern(measurements)
        elif pattern_type == PatternType.CUFF:
            return self._create_cuff_pattern(measurements)
        elif pattern_type == PatternType.POCKET:
            return self._create_pocket_pattern(measurements)
        
        return {"points": {}, "lines": {}, "curves": {}}
    
    def _create_collar_pattern(self, measurements: Dict[str, float]) -> Dict[str, Any]:
        """Создание лекала воротника"""
        neck_circumference = measurements["bust"] * 0.4
        collar_width = 5.0
        
        points = {
            "center_back": Point(0, 0),
            "center_front": Point(neck_circumference / 2, 0),
            "outer_back": Point(0, collar_width),
            "outer_front": Point(neck_circumference / 2 + 2, collar_width)
        }
        
        lines = {
            "inner_seam": Line(points["center_back"], points["center_front"]),
            "outer_seam": Line(points["outer_back"], points["outer_front"]),
            "back": Line(points["center_back"], points["outer_back"]),
            "front": Line(points["center_front"], points["outer_front"])
        }
        
        return {
            "points": {k: {"x": v.x, "y": v.y} for k, v in points.items()},
            "lines": {k: {"start": {"x": v.start.x, "y": v.start.y}, 
                         "end": {"x": v.end.x, "y": v.end.y}} for k, v in lines.items()},
            "curves": {}
        }
    
    def _create_cuff_pattern(self, measurements: Dict[str, float]) -> Dict[str, Any]:
        """Создание лекала манжеты"""
        wrist_circumference = measurements.get("wrist", 20.0)
        cuff_length = 8.0
        
        points = {
            "bottom_left": Point(0, 0),
            "bottom_right": Point(wrist_circumference + 2, 0),
            "top_left": Point(0, cuff_length),
            "top_right": Point(wrist_circumference + 2, cuff_length)
        }
        
        lines = {
            "bottom": Line(points["bottom_left"], points["bottom_right"]),
            "top": Line(points["top_left"], points["top_right"]),
            "left": Line(points["bottom_left"], points["top_left"]),
            "right": Line(points["bottom_right"], points["top_right"])
        }
        
        return {
            "points": {k: {"x": v.x, "y": v.y} for k, v in points.items()},
            "lines": {k: {"start": {"x": v.start.x, "y": v.start.y}, 
                         "end": {"x": v.end.x, "y": v.end.y}} for k, v in lines.items()},
            "curves": {}
        }
    
    def _create_pocket_pattern(self, measurements: Dict[str, float]) -> Dict[str, Any]:
        """Создание лекала кармана"""
        pocket_width = 15.0
        pocket_depth = 18.0
        
        points = {
            "top_left": Point(0, 0),
            "top_right": Point(pocket_width, 0),
            "bottom_left": Point(0, pocket_depth),
            "bottom_right": Point(pocket_width, pocket_depth)
        }
        
        lines = {
            "top": Line(points["top_left"], points["top_right"]),
            "bottom": Line(points["bottom_left"], points["bottom_right"]),
            "left": Line(points["top_left"], points["bottom_left"]),
            "right": Line(points["top_right"], points["bottom_right"])
        }
        
        return {
            "points": {k: {"x": v.x, "y": v.y} for k, v in points.items()},
            "lines": {k: {"start": {"x": v.start.x, "y": v.start.y}, 
                         "end": {"x": v.end.x, "y": v.end.y}} for k, v in lines.items()},
            "curves": {}
        }
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Получить лекало по ID"""
        return self.patterns.get(pattern_id)
    
    def list_patterns(self) -> List[Dict[str, Any]]:
        """Получить список всех лекал (заглушка для будущего хранения)"""
        return []
    
    def grade_pattern(self, pattern_data: Dict[str, Any], target_sizes: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Градация лекал на разные размеры
        
        Args:
            pattern_data: Данные лекала
            target_sizes: Целевые размеры
            
        Returns:
            Словарь с отградированными лекалами
        """
        graded_patterns = {}
        
        # Базовые градации (упрощенные)
        size_grades = {
            "XS": 0.9,
            "S": 0.95,
            "M": 1.0,
            "L": 1.05,
            "XL": 1.1,
            "XXL": 1.15
        }
        
        for size in target_sizes:
            if size in size_grades:
                scale_factor = size_grades[size]
                
                # Копирование и масштабирование геометрии
                graded_pattern = pattern_data.copy()
                
                # Масштабирование точек
                if "points" in graded_pattern:
                    for point_name, point_data in graded_pattern["points"].items():
                        point_data["x"] *= scale_factor
                        point_data["y"] *= scale_factor
                
                # Масштабирование линий
                if "lines" in graded_pattern:
                    for line_name, line_data in graded_pattern["lines"].items():
                        line_data["start"]["x"] *= scale_factor
                        line_data["start"]["y"] *= scale_factor
                        line_data["end"]["x"] *= scale_factor
                        line_data["end"]["y"] *= scale_factor
                
                # Масштабирование кривых
                if "curves" in graded_pattern:
                    for curve_name, curve_data in graded_pattern["curves"].items():
                        for point in ["start", "control1", "control2", "end"]:
                            curve_data[point]["x"] *= scale_factor
                            curve_data[point]["y"] *= scale_factor
                
                graded_patterns[size] = graded_pattern
        
        return graded_patterns
    
    def calculate_pattern_area(self, pattern_data: Dict[str, Any]) -> float:
        """
        Расчет площади лекала
        
        Args:
            pattern_data: Данные лекала
            
        Returns:
            Площадь в квадратных сантиметрах
        """
        area = 0.0
        
        # Упрощенный расчет площади через ограничивающий прямоугольник
        if "points" in pattern_data and pattern_data["points"]:
            x_coords = [p["x"] for p in pattern_data["points"].values()]
            y_coords = [p["y"] for p in pattern_data["points"].values()]
            
            if x_coords and y_coords:
                width = max(x_coords) - min(x_coords)
                height = max(y_coords) - min(y_coords)
                area = width * height
        
        return area
    
    def validate_pattern(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация лекала
        
        Args:
            pattern_data: Данные лекала
            
        Returns:
            Результат валидации
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Проверка наличия обязательных полей
        required_fields = ["points", "lines"]
        for field in required_fields:
            if field not in pattern_data:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Проверка геометрии
        if "points" in pattern_data:
            for point_name, point_data in pattern_data["points"].items():
                if not isinstance(point_data, dict) or "x" not in point_data or "y" not in point_data:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Invalid point data for: {point_name}")
        
        if "lines" in pattern_data:
            for line_name, line_data in pattern_data["lines"].items():
                if not isinstance(line_data, dict) or "start" not in line_data or "end" not in line_data:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Invalid line data for: {line_name}")
        
        return validation_result
    
    def build_shirt_sleeve(self, measurements: Dict[str, float], armhole_length: float) -> Dict[str, Any]:
        """
        Построение базового втачного рукава
        
        Args:
            measurements: Мерки тела
            armhole_length: Длина проймы (спинка + перед)
            
        Returns:
            Словарь с линиями рукава
        """
        # Основные мерки
        chest = measurements["bust"]
        height = measurements["height"]
        
        # Расчеты рукава
        sleeve_width = chest * 0.4  # Ширина рукава в самой широкой части
        sleeve_length = height * 0.35  # Длина рукава до низа
        cap_height = armhole_length / 3  # Высота оката
        
        # Система координат: (0,0) = верх оката
        # X → ширина, Y → вниз
        
        # Окат рукава (плавная дуга)
        # Контрольные точки для кривой Безье
        cap_top = Point(0, 0)  # Верхняя точка оката
        cap_front_high = Point(sleeve_width * 0.3, cap_height * 0.3)
        cap_front_low = Point(sleeve_width * 0.4, cap_height * 0.7)
        cap_side = Point(sleeve_width / 2, cap_height)  # Боковая точка оката
        cap_back_low = Point(sleeve_width * 0.6, cap_height * 0.7)
        cap_back_high = Point(sleeve_width * 0.7, cap_height * 0.3)
        cap_bottom = Point(sleeve_width, 0)  # Нижняя точка оката
        
        # Боковые линии
        # Передняя сторона
        front_top = Point(sleeve_width * 0.3, cap_height * 0.8)  # Точка соединения с окатом
        front_bottom = Point(sleeve_width * 0.2, sleeve_length)  # Нижняя точка
        
        # Задняя сторона
        back_top = Point(sleeve_width * 0.7, cap_height * 0.8)  # Точка соединения с окатом
        back_bottom = Point(sleeve_width * 0.8, sleeve_length)  # Нижняя точка
        
        # Линия низа
        bottom_left = Point(sleeve_width * 0.2, sleeve_length)
        bottom_right = Point(sleeve_width * 0.8, sleeve_length)
        
        # Создаем линии рукава
        sleeve_lines = [
            # Окат рукава (состоит из нескольких сегментов для плавности)
            {
                "name": "cap_front_1",
                "start": {"x": cap_top.x, "y": cap_top.y},
                "end": {"x": cap_front_high.x, "y": cap_front_high.y}
            },
            {
                "name": "cap_front_2", 
                "start": {"x": cap_front_high.x, "y": cap_front_high.y},
                "end": {"x": cap_front_low.x, "y": cap_front_low.y}
            },
            {
                "name": "cap_front_3",
                "start": {"x": cap_front_low.x, "y": cap_front_low.y},
                "end": {"x": cap_side.x, "y": cap_side.y}
            },
            {
                "name": "cap_back_1",
                "start": {"x": cap_side.x, "y": cap_side.y},
                "end": {"x": cap_back_low.x, "y": cap_back_low.y}
            },
            {
                "name": "cap_back_2",
                "start": {"x": cap_back_low.x, "y": cap_back_low.y},
                "end": {"x": cap_back_high.x, "y": cap_back_high.y}
            },
            {
                "name": "cap_back_3",
                "start": {"x": cap_back_high.x, "y": cap_back_high.y},
                "end": {"x": cap_bottom.x, "y": cap_bottom.y}
            },
            
            # Передняя боковая линия
            {
                "name": "front_seam",
                "start": {"x": front_top.x, "y": front_top.y},
                "end": {"x": front_bottom.x, "y": front_bottom.y}
            },
            
            # Задняя боковая линия
            {
                "name": "back_seam",
                "start": {"x": back_top.x, "y": back_top.y},
                "end": {"x": back_bottom.x, "y": back_bottom.y}
            },
            
            # Линия низа
            {
                "name": "bottom_hem",
                "start": {"x": bottom_left.x, "y": bottom_left.y},
                "end": {"x": bottom_right.x, "y": bottom_right.y}
            }
        ]
        
        # Дополнительная информация о рукаве
        sleeve_info = {
            "sleeve_width": sleeve_width,
            "sleeve_length": sleeve_length,
            "cap_height": cap_height,
            "armhole_length": armhole_length,
            "construction": "basic_set_in_sleeve"
        }
        
        return {
            "lines": sleeve_lines,
            "info": sleeve_info,
            "construction": "basic_set_in_sleeve"
        }
    
    def _generate_pattern_constraints(self, points: Dict[str, Dict], pattern_type) -> Dict[str, Any]:
        """
        Генерирует CAD constraints на основе топологии точек
        
        Constraints определяют:
        - Линии (WAIST_LINE, HEM_LINE, etc.) с припусками
        - Оси симметрии (CENTER_FRONT, CENTER_BACK)
        - Направления (GRAINLINE)
        - Связи между точками
        """
        constraints = {
            "lines": {},
            "axes": {},
            "directions": {},
            "symmetries": {},
            "measurements": {}
        }
        
        # Анализируем точки для определения линий
        point_names = list(points.keys())
        
        if pattern_type == PatternType.SKIRT_FRONT:
            # Определяем линии для передней половинки юбки
            waist_points = [name for name in point_names if 'waist' in name.lower()]
            hem_points = [name for name in point_names if 'hem' in name.lower()]
            hip_points = [name for name in point_names if 'hip' in name.lower()]
            side_points = [name for name in point_names if 'side' in name.lower()]
            center_points = [name for name in point_names if 'center' in name.lower() or 'front' in name.lower()]
            
            # Линии с припусками по типам
            if waist_points:
                constraints["lines"]["WAIST_LINE"] = {
                    "points": waist_points[:3],
                    "seam_allowance": 12,  # 12 мм для талии
                    "type": "waist"
                }
            if hem_points:
                constraints["lines"]["HEM_LINE"] = {
                    "points": hem_points[:3],
                    "seam_allowance": 20,  # 20 мм для низа
                    "type": "hem"
                }
            if hip_points:
                constraints["lines"]["HIP_LINE"] = {
                    "points": hip_points[:3],
                    "seam_allowance": 10,  # 10 мм для бедер
                    "type": "hip"
                }
            if side_points:
                constraints["lines"]["SIDE_SEAM"] = {
                    "points": side_points[:2],
                    "seam_allowance": 10,  # 10 мм для боковых швов
                    "type": "side"
                }
            if center_points:
                constraints["lines"]["CENTER_FRONT"] = {
                    "points": center_points[:2],
                    "seam_allowance": 15,  # 15 мм для середины переда
                    "type": "center"
                }
            
            # Оси симметрии
            if center_points and len(center_points) >= 2:
                constraints["axes"]["CENTER_FRONT"] = center_points[:2]
            
            # Направления
            constraints["directions"]["GRAINLINE"] = "vertical"  # Для юбки - вертикальное
            
        elif pattern_type == PatternType.SKIRT_BACK:
            # Определяем линии для задней половинки юбки
            waist_points = [name for name in point_names if 'waist' in name.lower()]
            hem_points = [name for name in point_names if 'hem' in name.lower()]
            hip_points = [name for name in point_names if 'hip' in name.lower()]
            side_points = [name for name in point_names if 'side' in name.lower()]
            center_points = [name for name in point_names if 'center' in name.lower() or 'back' in name.lower()]
            
            # Линии с припусками по типам
            if waist_points:
                constraints["lines"]["WAIST_LINE"] = {
                    "points": waist_points[:3],
                    "seam_allowance": 12,  # 12 мм для талии
                    "type": "waist"
                }
            if hem_points:
                constraints["lines"]["HEM_LINE"] = {
                    "points": hem_points[:3],
                    "seam_allowance": 20,  # 20 мм для низа
                    "type": "hem"
                }
            if hip_points:
                constraints["lines"]["HIP_LINE"] = {
                    "points": hip_points[:3],
                    "seam_allowance": 10,  # 10 мм для бедер
                    "type": "hip"
                }
            if side_points:
                constraints["lines"]["SIDE_SEAM"] = {
                    "points": side_points[:2],
                    "seam_allowance": 10,  # 10 мм для боковых швов
                    "type": "side"
                }
            if center_points:
                constraints["lines"]["CENTER_BACK"] = {
                    "points": center_points[:2],
                    "seam_allowance": 15,  # 15 мм для середины спинки
                    "type": "center"
                }
            
            # Оси симметрии
            if center_points and len(center_points) >= 2:
                constraints["axes"]["CENTER_BACK"] = center_points[:2]
            
            # Направления
            constraints["directions"]["GRAINLINE"] = "vertical"
        
        # Измерения (для автоградации)
        if "WAIST_LINE" in constraints["lines"] and len(constraints["lines"]["WAIST_LINE"]["points"]) >= 2:
            constraints["measurements"]["WAIST_WIDTH"] = {
                "points": constraints["lines"]["WAIST_LINE"]["points"][:2],
                "type": "distance"
            }
        
        if "HEM_LINE" in constraints["lines"] and len(constraints["lines"]["HEM_LINE"]["points"]) >= 2:
            constraints["measurements"]["HEM_WIDTH"] = {
                "points": constraints["lines"]["HEM_LINE"]["points"][:2],
                "type": "distance"
            }
        
        if "HIP_LINE" in constraints["lines"] and len(constraints["lines"]["HIP_LINE"]["points"]) >= 2:
            constraints["measurements"]["HIP_WIDTH"] = {
                "points": constraints["lines"]["HIP_LINE"]["points"][:2],
                "type": "distance"
            }
        
        # Симметрии (для проверки)
        if pattern_type == PatternType.SKIRT_FRONT:
            constraints["symmetries"]["FRONT_SYMMETRY"] = {
                "axis": "CENTER_FRONT",
                "type": "mirror"
            }
        elif pattern_type == PatternType.SKIRT_BACK:
            constraints["symmetries"]["BACK_SYMMETRY"] = {
                "axis": "CENTER_BACK", 
                "type": "mirror"
            }
        
        # Метаданные для CAD экспорта
        constraints["metadata"] = {
            "pattern_type": pattern_type.value,
            "cad_ready": True,
            "export_formats": ["DXF", "Seamly2D"],
            "auto_check": True,
            "symmetry_check": True,
            "gradation_ready": True,
            "seam_allowance_ready": True  # Готовность к припускам
        }
        
        return constraints
    
    def assemble_full_pattern(self, parts: list[dict]) -> dict:
        """
        Объединяет части (front, back, waistband и т.д.) в один layout
        
        Args:
            parts: Список частей паттерна (front, back, waistband и т.д.)
            
        Returns:
            dict: Общая картина изделия с layout
        """
        if not parts:
            return {
                "assembly": {
                    "parts": [],
                    "alignment_lines": [],
                    "notches": [],
                    "labels": [],
                    "metadata": {
                        "total_parts": 0,
                        "layout_width": 0,
                        "layout_height": 0,
                        "assembly_type": "full_pattern"
                    }
                }
            }
        
        # Анализ размеров частей
        part_bounds = []
        for i, part in enumerate(parts):
            points = part.get('points', {})
            if points:
                x_coords = [p['x'] for p in points.values()]
                y_coords = [p['y'] for p in points.values()]
                
                bounds = {
                    'min_x': min(x_coords),
                    'max_x': max(x_coords),
                    'min_y': min(y_coords),
                    'max_y': max(y_coords),
                    'width': max(x_coords) - min(x_coords),
                    'height': max(y_coords) - min(y_coords),
                    'part_index': i,
                    'part_name': part.get('metadata', {}).get('pattern_type', f'part_{i}')
                }
                part_bounds.append(bounds)
        
        if not part_bounds:
            return {
                "assembly": {
                    "parts": [],
                    "alignment_lines": [],
                    "notches": [],
                    "labels": [],
                    "metadata": {
                        "total_parts": 0,
                        "layout_width": 0,
                        "layout_height": 0,
                        "assembly_type": "full_pattern"
                    }
                }
            }
        
        # Расчет layout
        max_width = max(b['width'] for b in part_bounds)
        max_height = max(b['height'] for b in part_bounds)
        
        # Позиционирование частей
        assembled_parts = []
        current_x = 0
        current_y = 0
        
        for i, (part, bounds) in enumerate(zip(parts, part_bounds)):
            # Смещение для части
            offset_x = current_x
            offset_y = current_y
            
            # Front в центре, back справа
            if bounds['part_name'] == 'skirt_front':
                offset_x = max_width * 0.1  # Небольшой отступ слева
            elif bounds['part_name'] == 'skirt_back':
                offset_x = max_width + 50  # Справа с отступом 5 см
            elif 'waistband' in bounds['part_name'].lower():
                offset_x = max_width * 0.5  # Посередине
                offset_y = max_height + 50  # Выше с отступом 5 см
            
            # Смещаем все точки части
            shifted_points = {}
            for point_name, point_data in part.get('points', {}).items():
                shifted_points[point_name] = {
                    'x': point_data['x'] + offset_x,
                    'y': point_data['y'] + offset_y
                }
            
            # Смещаем линии
            shifted_lines = {}
            for line_name, line_data in part.get('lines', {}).items():
                # Проверяем формат line_data
                if isinstance(line_data, dict):
                    # Получаем координаты точек по именам
                    start_name = line_data['start']
                    end_name = line_data['end']
                    
                    # Ищем координаты в points
                    start_point = shifted_points.get(start_name)
                    end_point = shifted_points.get(end_name)
                    
                    if start_point and end_point:
                        shifted_lines[line_name] = {
                            'start': {
                                'x': start_point['x'],
                                'y': start_point['y']
                            },
                            'end': {
                                'x': end_point['x'],
                                'y': end_point['y']
                            }
                        }
                    else:
                        # Пропускаем если точки не найдены
                        continue
                else:
                    # Пропускаем нестандартный формат
                    continue
            
            # Смещаем кривые
            shifted_curves = {}
            for curve_name, curve_data in part.get('curves', {}).items():
                # Проверяем формат curve_data
                if isinstance(curve_data, dict):
                    # Получаем координаты точек по именам
                    start_name = curve_data['start']
                    end_name = curve_data['end']
                    
                    # Ищем координаты в points
                    start_point = shifted_points.get(start_name)
                    end_point = shifted_points.get(end_name)
                    
                    if start_point and end_point:
                        shifted_curves[curve_name] = {
                            'start': start_name,
                            'control1': {
                                'x': curve_data['control1']['x'] + offset_x,
                                'y': curve_data['control1']['y'] + offset_y
                            },
                            'control2': {
                                'x': curve_data['control2']['x'] + offset_x,
                                'y': curve_data['control2']['y'] + offset_y
                            },
                            'end': end_name
                        }
                    else:
                        # Пропускаем если точки не найдены
                        continue
                else:
                    # Пропускаем нестандартный формат
                    continue
            
            assembled_parts.append({
                'part_index': i,
                'part_name': bounds['part_name'],
                'original_part': part,
                'points': shifted_points,
                'lines': shifted_lines,
                'curves': shifted_curves,
                'offset': {'x': offset_x, 'y': offset_y},
                'bounds': {
                    'min_x': bounds['min_x'] + offset_x,
                    'max_x': bounds['max_x'] + offset_x,
                    'min_y': bounds['min_y'] + offset_y,
                    'max_y': bounds['max_y'] + offset_y,
                    'width': bounds['width'],
                    'height': bounds['height']
                }
            })
            
            # Обновляем позицию для следующей части
            current_x = max(current_x, offset_x + bounds['width'] + 20)
            current_y = max(current_y, offset_y + bounds['height'] + 20)
        
        # Создаем линии совмещения (пунктир между notches)
        alignment_lines = []
        notches = []
        
        # Находим notches в частях
        for part in assembled_parts:
            part_name = part['part_name']
            
            # Создаем notches для совмещения
            if 'front' in part_name.lower():
                # Notches на боковых швах передней части
                for line_name, line_data in part['lines'].items():
                    if 'side' in line_name.lower():
                        mid_x = (line_data['start']['x'] + line_data['end']['x']) / 2
                        mid_y = (line_data['start']['y'] + line_data['end']['y']) / 2
                        
                        notches.append({
                            'x': mid_x,
                            'y': mid_y,
                            'type': 'alignment',
                            'part': part_name,
                            'line': line_name,
                            'id': f"notch_{part_name}_{line_name}"
                        })
            
            elif 'back' in part_name.lower():
                # Notches на боковых швах задней части
                for line_name, line_data in part['lines'].items():
                    if 'side' in line_name.lower():
                        mid_x = (line_data['start']['x'] + line_data['end']['x']) / 2
                        mid_y = (line_data['start']['y'] + line_data['end']['y']) / 2
                        
                        notches.append({
                            'x': mid_x,
                            'y': mid_y,
                            'type': 'alignment',
                            'part': part_name,
                            'line': line_name,
                            'id': f"notch_{part_name}_{line_name}"
                        })
        
        # Создаем линии совмещения между notches
        front_notches = [n for n in notches if 'front' in n['part']]
        back_notches = [n for n in notches if 'back' in n['part']]
        
        for front_notch in front_notches:
            for back_notch in back_notches:
                # Соединяем notches пунктирной линией
                alignment_lines.append({
                    'start': {'x': front_notch['x'], 'y': front_notch['y']},
                    'end': {'x': back_notch['x'], 'y': back_notch['y']},
                    'type': 'dashed',
                    'purpose': 'alignment',
                    'connects': [front_notch['id'], back_notch['id']]
                })
        
        # Добавляем метки "Full Assembly View"
        labels = []
        if assembled_parts:
            # Общие границы layout
            all_x = []
            all_y = []
            for part in assembled_parts:
                bounds = part['bounds']
                all_x.extend([bounds['min_x'], bounds['max_x']])
                all_y.extend([bounds['min_y'], bounds['max_y']])
            
            layout_bounds = {
                'min_x': min(all_x),
                'max_x': max(all_x),
                'min_y': min(all_y),
                'max_y': max(all_y),
                'width': max(all_x) - min(all_x),
                'height': max(all_y) - min(all_y)
            }
            
            # Метка вверху по центру
            labels.append({
                'text': 'Full Assembly View',
                'x': layout_bounds['min_x'] + layout_bounds['width'] / 2,
                'y': layout_bounds['min_y'] - 30,
                'type': 'title',
                'size': 'large'
            })
            
            # Метки частей
            for part in assembled_parts:
                bounds = part['bounds']
                labels.append({
                    'text': part['part_name'].replace('_', ' ').title(),
                    'x': bounds['min_x'] + bounds['width'] / 2,
                    'y': bounds['max_y'] + 15,
                    'type': 'part_label',
                    'size': 'medium'
                })
        
        # Собираем результат
        assembly = {
            'parts': assembled_parts,
            'alignment_lines': alignment_lines,
            'notches': notches,
            'labels': labels,
            'metadata': {
                'total_parts': len(assembled_parts),
                'layout_width': max(all_x) - min(all_x) if all_x else 0,
                'layout_height': max(all_y) - min(all_y) if all_y else 0,
                'assembly_type': 'full_pattern',
                'created_at': str(datetime.now()),
                'parts_list': [p['part_name'] for p in assembled_parts]
            }
        }
        
        return {
            'assembly': assembly,
            'original_parts': parts,
            'layout_info': {
                'max_width': max_width,
                'max_height': max_height,
                'total_bounds': layout_bounds if 'layout_bounds' in locals() else None
            }
        }
