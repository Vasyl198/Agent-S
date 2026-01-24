"""
Fashion Dataset Integration Module

Интеграция с Garment-Pattern-Generator Dataset для обучения и валидации лекал.
Поддержка JSON/OBJ форматов, векторная индексация через FAISS.
"""

import json
import os
import pickle
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import logging

# FAISS для векторной индексации
try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

# Sentence Transformers для эмбеддингов
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.getLogger(__name__).debug("Sentence Transformers not available. Using fallback embeddings.")

from .pattern_maker import PatternMaker, Point, Line, Curve
from .fit_analyzer import FitAnalyzer

# Порог похожести для fashion-паттернов (снижен с 0.7 до 0.3)
SIMILARITY_THRESHOLD = 0.3


@dataclass
class DatasetConfig:
    """Конфигурация датасета"""
    dataset_path: str
    index_path: str = "fashion_dataset_index.faiss"
    metadata_path: str = "fashion_dataset_metadata.pkl"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_patterns: int = 1000
    cache_embeddings: bool = True


@dataclass
class ValidationResult:
    """Результат валидации лекала"""
    score: float  # 0-100
    point_rmse: float
    symmetry_score: float
    curve_count_diff: int
    line_count_diff: int
    recommendations: List[str]
    reference_pattern: Optional[Dict[str, Any]] = None
    generated_pattern: Optional[Dict[str, Any]] = None


class DatasetIntegration:
    """Интеграция с Garment-Pattern-Generator Dataset"""
    
    def __init__(self, config: DatasetConfig):
        """
        Инициализация интеграции с датасетом
        
        Args:
            config: Конфигурация датасета
        """
        self.config = config
        self.dataset_path = Path(config.dataset_path)
        self.pattern_maker = PatternMaker()
        self.fit_analyzer = FitAnalyzer()
        
        # Инициализация FAISS индекса
        self.index = None
        self.metadata = []
        self.embedding_model = None
        
        # Загрузка или создание индекса
        self._initialize_index()
        
        # Кэш для загруженных паттернов
        self._pattern_cache = {}
        
        logging.info(f"DatasetIntegration initialized with path: {config.dataset_path}")
    
    def _initialize_index(self):
        """Инициализация FAISS индекса и модели эмбеддингов"""
        if not FAISS_AVAILABLE:
            logging.warning("FAISS not available. Dataset search will be limited.")
            return
        
        # Инициализация модели эмбеддингов
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Сначала пробуем загрузить локальную модель
                local_model_path = Path(__file__).parent.parent.parent / "models" / self.config.embedding_model
                if local_model_path.exists():
                    self.embedding_model = SentenceTransformer(str(local_model_path))
                    logging.info(f"Loaded sentence transformer model from local path: {local_model_path}")
                else:
                    # Если локальной модели нет, пробуем загрузить из интернета
                    self.embedding_model = SentenceTransformer(self.config.embedding_model)
                    logging.info(f"Loaded sentence transformer model from internet: {self.config.embedding_model}")
                    # Сохраняем локально для будущего использования
                    try:
                        local_model_path.parent.mkdir(parents=True, exist_ok=True)
                        self.embedding_model.save(str(local_model_path))
                        logging.info(f"Saved model locally to: {local_model_path}")
                    except Exception as save_error:
                        logging.warning(f"Failed to save model locally: {save_error}")
            except Exception as e:
                logging.warning(f"Failed to load sentence transformer: {e}")
                self.embedding_model = None
        
        # Загрузка существующего индекса
        index_path = Path(self.config.index_path)
        metadata_path = Path(self.config.metadata_path)
        
        if index_path.exists() and metadata_path.exists():
            try:
                self.index = faiss.read_index(str(index_path))
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logging.info(f"Loaded existing index with {len(self.metadata)} patterns")
            except Exception as e:
                logging.warning(f"Failed to load existing index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Создание нового FAISS индекса"""
        if not FAISS_AVAILABLE:
            return
        
        # Определение размерности эмбеддингов
        embedding_dim = 384  # Default for all-MiniLM-L6-v2
        if self.embedding_model:
            try:
                test_embedding = self.embedding_model.encode("test")
                embedding_dim = len(test_embedding)
            except:
                pass
        
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner Product for similarity
        self.metadata = []
        logging.info(f"Created new FAISS index with dimension {embedding_dim}")
    
    def load_gpg_pattern(self, garment_path: str) -> Dict[str, Any]:
        """
        Загружает sewing pattern из датасета (ТОЛЬКО 2D паттерны)
        
        Args:
            garment_path: Путь к файлу паттерна (.json) или папке с pattern.json
            
        Returns:
            Унифицированный dict в формате pattern_maker
        """
        garment_path = Path(garment_path)
        
        # Если это папка, ищем pattern.json или specification.json
        if garment_path.is_dir():
            pattern_json = garment_path / "pattern.json"
            spec_json = garment_path / "specification.json"
            
            if pattern_json.exists():
                garment_path = pattern_json
            elif spec_json.exists():
                garment_path = spec_json
            else:
                raise FileNotFoundError(f"Neither pattern.json nor specification.json found in folder: {garment_path}")
        
        if not garment_path.exists():
            raise FileNotFoundError(f"Pattern file not found: {garment_path}")
        
        # Проверяем кэш
        cache_key = str(garment_path.absolute())
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]
        
        try:
            print(f"Loading pattern from {garment_path.parent}")
            
            # ОТКЛЮЧАЕМ 3D ФАЙЛЫ - работаем только с 2D паттернами
            if garment_path.suffix.lower() == '.json':
                pattern_data = self._load_json_pattern(garment_path)
            else:
                # Пропускаем OBJ файлы
                raise ValueError(f"Unsupported file format: {garment_path.suffix}. Only JSON patterns are supported.")
            
            # Конвертация в унифицированный формат
            unified_pattern = self._convert_to_unified_format(pattern_data, garment_path)
            
            # Кэширование
            self._pattern_cache[cache_key] = unified_pattern
            
            return unified_pattern
            
        except Exception as e:
            logging.error(f"Failed to load pattern {garment_path}: {e}")
            raise
    
    def _load_json_pattern(self, json_path: Path) -> Dict[str, Any]:
        """Загрузка JSON паттерна"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_obj_pattern(self, obj_path: Path) -> Dict[str, Any]:
        """Загрузка OBJ паттерна"""
        vertices = []
        faces = []
        
        with open(obj_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                
                if parts[0] == 'v':
                    # Вершина: v x y z
                    if len(parts) >= 4:
                        vertices.append({
                            'x': float(parts[1]),
                            'y': float(parts[2]),
                            'z': float(parts[3]) if len(parts) > 3 else 0.0
                        })
                elif parts[0] == 'f':
                    # Грань: f v1 v2 v3 ...
                    face_vertices = []
                    for part in parts[1:]:
                        # Убираем текстурные координаты и нормали (v1/vt1/vn1)
                        vertex_idx = int(part.split('/')[0]) - 1
                        face_vertices.append(vertex_idx)
                    faces.append(face_vertices)
        
        return {
            'vertices': vertices,
            'faces': faces,
            'format': 'obj'
        }
    
    def _convert_to_unified_format(self, pattern_data: Dict[str, Any], source_path: Path) -> Dict[str, Any]:
        """
        Конвертирует паттерн в унифицированный формат pattern_maker
        
        Args:
            pattern_data: Исходные данные паттерна
            source_path: Путь к исходному файлу
            
        Returns:
            Унифицированный паттерн
        """
        # Определяем тип одежды из пути или данных
        clothing_type = self._detect_clothing_type(pattern_data, source_path)
        
        # Конвертация в зависимости от формата
        if pattern_data.get('format') == 'obj':
            return self._convert_obj_to_unified(pattern_data, clothing_type)
        else:
            return self._convert_json_to_unified(pattern_data, clothing_type)
    
    def _detect_clothing_type(self, pattern_data: Dict[str, Any], source_path: Path) -> str:
        """Определяет тип одежды из данных или пути"""
        # Из пути
        path_lower = str(source_path).lower()
        if 'skirt' in path_lower:
            return 'skirt'
        elif 'pants' in path_lower or 'trouser' in path_lower:
            return 'pants'
        elif 'shirt' in path_lower or 'blouse' in path_lower:
            return 'shirt'
        elif 'dress' in path_lower:
            return 'dress'
        elif 'jacket' in path_lower or 'coat' in path_lower:
            return 'jacket'
        
        # Из данных
        if 'garment_type' in pattern_data:
            return pattern_data['garment_type']
        elif 'type' in pattern_data:
            return pattern_data['type']
        
        # По умолчанию
        return 'unknown'
    
    def _convert_obj_to_unified(self, obj_data: Dict[str, Any], clothing_type: str) -> Dict[str, Any]:
        """Конвертация OBJ в унифицированный формат"""
        vertices = obj_data.get('vertices', [])
        faces = obj_data.get('faces', [])
        
        points = {}
        lines = {}
        curves = {}
        
        # Конвертация вершин в точки
        for i, vertex in enumerate(vertices):
            points[f'point_{i}'] = Point(
                x=vertex['x'],
                y=vertex['y']
            )
        
        # Конвертация граней в линии
        line_id = 0
        for face in faces:
            if len(face) >= 2:
                for i in range(len(face)):
                    start_idx = face[i]
                    end_idx = face[(i + 1) % len(face)]
                    
                    start_point = f'point_{start_idx}'
                    end_point = f'point_{end_idx}'
                    
                    if start_point in points and end_point in points:
                        lines[f'line_{line_id}'] = Line(
                            start=points[start_point],
                            end=points[end_point]
                        )
                        line_id += 1
        
        return {
            'points': {k: {'x': v.x, 'y': v.y} for k, v in points.items()},
            'lines': {k: {'start': {'x': v.start.x, 'y': v.start.y}, 
                         'end': {'x': v.end.x, 'y': v.end.y}} for k, v in lines.items()},
            'curves': {},
            'pattern_type': clothing_type,
            'construction_method': 'dataset_import',
            'source_format': 'obj',
            'source_vertices': len(vertices),
            'source_faces': len(faces)
        }
    
    def _convert_json_to_unified(self, json_data: Dict[str, Any], clothing_type: str) -> Dict[str, Any]:
        """Конвертация JSON в унифицированный формат"""
        points = {}
        lines = {}
        curves = {}
        
        # Проверяем, это specification.json или обычный паттерн
        if 'pattern' in json_data and 'panels' in json_data['pattern']:
            # Это specification.json из skirt_2_panels_1200
            return self._convert_specification_to_unified(json_data, clothing_type)
        
        # Обработка точек
        if 'points' in json_data:
            for point_name, point_data in json_data['points'].items():
                if isinstance(point_data, dict):
                    points[point_name] = {
                        'x': float(point_data.get('x', 0)),
                        'y': float(point_data.get('y', 0))
                    }
                elif isinstance(point_data, list) and len(point_data) >= 2:
                    points[point_name] = {
                        'x': float(point_data[0]),
                        'y': float(point_data[1])
                    }
        
        # Обработка линий
        if 'lines' in json_data:
            for line_name, line_data in json_data['lines'].items():
                if isinstance(line_data, dict):
                    start = line_data.get('start', line_data.get('from'))
                    end = line_data.get('end', line_data.get('to'))
                    
                    if start and end:
                        lines[line_name] = {
                            'start': points.get(start, {'x': 0, 'y': 0}),
                            'end': points.get(end, {'x': 0, 'y': 0})
                        }
        
        # Обработка кривых
        if 'curves' in json_data:
            for curve_name, curve_data in json_data['curves'].items():
                if isinstance(curve_data, dict):
                    curves[curve_name] = {
                        'start': curve_data.get('start', {'x': 0, 'y': 0}),
                        'control1': curve_data.get('control1', {'x': 0, 'y': 0}),
                        'control2': curve_data.get('control2', {'x': 0, 'y': 0}),
                        'end': curve_data.get('end', {'x': 0, 'y': 0})
                    }
        
        return {
            'points': points,
            'lines': lines,
            'curves': curves,
            'pattern_type': clothing_type,
            'construction_method': 'dataset_import',
            'source_format': 'json'
        }
    
    def _convert_specification_to_unified(self, spec_data: Dict[str, Any], clothing_type: str) -> Dict[str, Any]:
        """
        Конвертирует specification.json из skirt_2_panels_1200 в унифицированный формат
        
        Структура specification.json:
        {
            "pattern": {
                "panels": {
                    "front": {
                        "translation": [...],
                        "edges": [...]
                    },
                    "back": {...}
                }
            }
        }
        """
        points = {}
        lines = {}
        curves = {}
        
        pattern_data = spec_data.get('pattern', {})
        panels = pattern_data.get('panels', {})
        
        point_counter = 0
        
        # Обрабатываем каждую панель
        for panel_name, panel_data in panels.items():
            translation = panel_data.get('translation', [0, 0, 0])
            edges = panel_data.get('edges', [])
            
            panel_points = {}
            
            # Создаем точки для ребер
            for edge in edges:
                endpoints = edge.get('endpoints', [])
                curvature = edge.get('curvature', [])
                
                if len(endpoints) >= 2:
                    start_idx = endpoints[0]
                    end_idx = endpoints[1]
                    
                    # Создаем имена точек
                    start_name = f"{panel_name}_p{start_idx}"
                    end_name = f"{panel_name}_p{end_idx}"
                    
                    # Добавляем точки, если их еще нет
                    if start_name not in points:
                        # Для skirt_2_panels_1200 точки определяются индексом
                        # Используем простое преобразование индекса в координаты
                        # Это приблизительная конвертация для демонстрации
                        points[start_name] = {
                            'x': float(start_idx * 10 - 100),  # Приблизительно
                            'y': float(translation[1] if len(translation) > 1 else 0)
                        }
                    
                    if end_name not in points:
                        points[end_name] = {
                            'x': float(end_idx * 10 - 100),  # Приблизительно
                            'y': float(translation[1] if len(translation) > 1 else 0)
                        }
                    
                    # Создаем линии или кривые
                    edge_name = f"{panel_name}_edge_{start_idx}_{end_idx}"
                    
                    if curvature and len(curvature) >= 2:
                        # Это кривая Безье из датасета
                        curves[edge_name] = {
                            'start': start_name,
                            'control1': {
                                'x': points[start_name]['x'] + curvature[0] * 50, 
                                'y': points[start_name]['y'] + curvature[0] * 30  # Добавляем вертикальную компоненту
                            },
                            'control2': {
                                'x': points[end_name]['x'] + curvature[1] * 50, 
                                'y': points[end_name]['y'] + curvature[1] * 30
                            },
                            'end': end_name,
                            'curve_type': 'bezier',
                            'curve_strength': max(abs(curvature[0]), abs(curvature[1]))
                        }
                    else:
                        # Это прямая линия
                        lines[edge_name] = {
                            'start': start_name,
                            'end': end_name
                        }
            
            # Добавляем специальные точки для юбок
            if clothing_type == 'skirt':
                # Точки талии
                if panel_name == 'front':
                    points[f'{panel_name}_waist_left'] = {'x': -100, 'y': 0}
                    points[f'{panel_name}_waist_right'] = {'x': 100, 'y': 0}
                    points[f'{panel_name}_waist_center'] = {'x': 0, 'y': 0}
                elif panel_name == 'back':
                    points[f'{panel_name}_waist_left'] = {'x': -100, 'y': 20}
                    points[f'{panel_name}_waist_right'] = {'x': 100, 'y': 20}
                    points[f'{panel_name}_waist_center'] = {'x': 0, 'y': 20}
                
                # Точки подола
                points[f'{panel_name}_hem_left'] = {'x': -120, 'y': 300}
                points[f'{panel_name}_hem_right'] = {'x': 120, 'y': 300}
                points[f'{panel_name}_hem_center'] = {'x': 0, 'y': 300}
                
                # Боковые точки
                points[f'{panel_name}_side_top'] = {'x': 100, 'y': 0}
                points[f'{panel_name}_side_bottom'] = {'x': 120, 'y': 300}
                
                # Центральные точки
                points[f'{panel_name}_center_front'] = {'x': 0, 'y': 0}
                points[f'{panel_name}_center_back'] = {'x': 0, 'y': 50}
        
        # Вычисляем реальные признаки из геометрии
        waist_width = 0
        hip_width = 0
        hem_width = 0
        
        # Извлекаем измерения из точек
        waist_points = [name for name in points.keys() if 'waist' in name.lower()]
        hip_points = [name for name in points.keys() if 'hip' in name.lower()]
        hem_points = [name for name in points.keys() if 'hem' in name.lower()]
        
        if waist_points and len(waist_points) >= 2:
            waist_coords = [points[name] for name in waist_points[:2]]
            waist_width = abs(waist_coords[1]['x'] - waist_coords[0]['x']) * 2  # Удваиваем для полной ширины
            
        if hip_points and len(hip_points) >= 2:
            hip_coords = [points[name] for name in hip_points[:2]]
            hip_width = abs(hip_coords[1]['x'] - hip_coords[0]['x']) * 2
            
        if hem_points and len(hem_points) >= 2:
            hem_coords = [points[name] for name in hem_points[:2]]
            hem_width = abs(hem_coords[1]['x'] - hem_coords[0]['x']) * 2
        
        # Определяем силуэт на основе соотношений
        silhouette = "straight"
        if hem_width > hip_width * 1.2:
            silhouette = "full"
        elif hem_width < hip_width * 0.9:
            silhouette = "pencil"
        elif hem_width > hip_width * 1.1:
            silhouette = "a_line"
        
        # Создаем метаданные с реальными признаками
        metadata = {
            "garment_type": clothing_type,
            "panels": len(panels),
            "waist": round(waist_width / 10),  # Конвертируем в см (предполагаем масштаб 1:10)
            "hips": round(hip_width / 10),
            "silhouette": silhouette,
            "hem_width": round(hem_width / 10),
            "flare_ratio": round((hem_width - hip_width) / hip_width, 3) if hip_width > 0 else 0
        }
        
        return {
            'points': points,
            'lines': lines,
            'curves': curves,
            'pattern_type': clothing_type,
            'construction_method': 'skirt_2_panels_dataset',
            'source_format': 'specification_json',
            'panels_count': len(panels),
            'metadata': metadata
        }
    
    def validate_generated_pattern(self, generated: Dict[str, Any], reference: Dict[str, Any]) -> ValidationResult:
        """
        Сравнивает сгенерированное лекало с эталонным из датасета
        
        Args:
            generated: Сгенерированное лекало
            reference: Эталонное лекало из датасета
            
        Returns:
            Результат валидации с метриками и рекомендациями
        """
        try:
            # 1. Расчет RMSE для точек
            point_rmse = self._calculate_point_rmse(generated, reference)
            
            # 2. Оценка симметрии
            symmetry_score = self._calculate_symmetry_score(generated, reference)
            
            # 3. Сравнение количества элементов
            curve_count_diff = len(generated.get('curves', {})) - len(reference.get('curves', {}))
            line_count_diff = len(generated.get('lines', {})) - len(reference.get('lines', {}))
            
            # 4. Общая оценка
            score = self._calculate_overall_score(point_rmse, symmetry_score, 
                                                 curve_count_diff, line_count_diff)
            
            # 5. Рекомендации
            recommendations = self._generate_recommendations(point_rmse, symmetry_score,
                                                         curve_count_diff, line_count_diff)
            
            return ValidationResult(
                score=score,
                point_rmse=point_rmse,
                symmetry_score=symmetry_score,
                curve_count_diff=curve_count_diff,
                line_count_diff=line_count_diff,
                recommendations=recommendations,
                reference_pattern=reference,
                generated_pattern=generated
            )
            
        except Exception as e:
            logging.error(f"Pattern validation failed: {e}")
            return ValidationResult(
                score=0.0,
                point_rmse=float('inf'),
                symmetry_score=0.0,
                curve_count_diff=0,
                line_count_diff=0,
                recommendations=[f"Validation error: {e}"],
                reference_pattern=reference,
                generated_pattern=generated
            )
    
    def _calculate_point_rmse(self, generated: Dict[str, Any], reference: Dict[str, Any]) -> float:
        """Расчет Root Mean Square Error для точек"""
        generated_points = generated.get('points', {})
        reference_points = reference.get('points', {})
        
        if not generated_points or not reference_points:
            return float('inf')
        
        # Находим общие точки по именам или по ближайшим
        squared_errors = []
        
        for ref_name, ref_point in reference_points.items():
            ref_x, ref_y = ref_point.get('x', 0), ref_point.get('y', 0)
            
            # Ищем ближайшую точку в сгенерированном
            min_distance = float('inf')
            for gen_name, gen_point in generated_points.items():
                gen_x, gen_y = gen_point.get('x', 0), gen_point.get('y', 0)
                distance = np.sqrt((gen_x - ref_x)**2 + (gen_y - ref_y)**2)
                min_distance = min(min_distance, distance)
            
            if min_distance < float('inf'):
                squared_errors.append(min_distance**2)
        
        if not squared_errors:
            return float('inf')
        
        mse = np.mean(squared_errors)
        return np.sqrt(mse)
    
    def _calculate_symmetry_score(self, generated: Dict[str, Any], reference: Dict[str, Any]) -> float:
        """Расчет оценки симметрии"""
        try:
            # Используем FitAnalyzer для оценки симметрии
            generated_analysis = self.fit_analyzer.check_pattern_symmetry(generated)
            reference_analysis = self.fit_analyzer.check_pattern_symmetry(reference)
            
            gen_score = generated_analysis.get('symmetry_score', 0)
            ref_score = reference_analysis.get('symmetry_score', 0)
            
            # Оценим насколько близка симметрия к эталону
            if ref_score > 0:
                return max(0, 100 - abs(gen_score - ref_score))
            else:
                return gen_score
                
        except Exception as e:
            logging.warning(f"Symmetry calculation failed: {e}")
            return 50.0  # Средняя оценка по умолчанию
    
    def _calculate_overall_score(self, point_rmse: float, symmetry_score: float,
                                curve_diff: int, line_diff: int) -> float:
        """Расчет общей оценки качества"""
        # Нормализация RMSE (чем меньше, тем лучше)
        rmse_score = max(0, 100 - min(point_rmse * 10, 100))  # 10 см = 0 баллов
        
        # Нормализация симметрии
        symmetry_normalized = symmetry_score
        
        # Штраф за разницу в количестве элементов
        element_penalty = min(abs(curve_diff) * 5 + abs(line_diff) * 2, 30)
        
        # Общая оценка
        overall_score = (rmse_score * 0.4 + symmetry_normalized * 0.4) - element_penalty
        
        return max(0, min(100, overall_score))
    
    def _generate_recommendations(self, point_rmse: float, symmetry_score: float,
                                curve_diff: int, line_diff: int) -> List[str]:
        """Генерирует рекомендации по улучшению паттерна"""
        recommendations = []
        
        if point_rmse > 2.0:
            recommendations.append(f"Точки слишком далеко от эталона (RMSE: {point_rmse:.1f} см). Проверьте конструкцию.")
        
        if symmetry_score < 70:
            recommendations.append(f"Низкая симметрия ({symmetry_score:.1f}%). Проверьте баланс переда и спинки.")
        
        if curve_diff > 2:
            recommendations.append(f"Слишком много кривых ({curve_diff} лишних). Упростите конструкцию.")
        elif curve_diff < -2:
            recommendations.append(f"Недостаточно кривых ({abs(curve_diff)} недостает). Добавьте плавные линии.")
        
        if line_diff > 3:
            recommendations.append(f"Слишком много линий ({line_diff} лишних). Проверьте дублирование.")
        elif line_diff < -3:
            recommendations.append(f"Недостаточно линий ({abs(line_diff)} недостает). Добавьте недостающие элементы.")
        
        if not recommendations:
            recommendations.append("Конструкция близка к эталону. Минимальные корректировки.")
        
        return recommendations
    
    def get_reference_examples(self, clothing_type: str, num: int = 5) -> List[Dict[str, Any]]:
        """
        Возвращает полные эталонные лекала из датасета с кривыми и деталями
        
        Args:
            clothing_type: Тип одежды (skirt, pants, shirt, dress, jacket)
            num: Количество примеров
            
        Returns:
            Список полных эталонных лекал с точками, линиями, кривыми
        """
        try:
            # Поиск паттернов в датасете
            pattern_files = self._find_pattern_files(clothing_type)
            
            if not pattern_files:
                logging.warning(f"No patterns found for type: {clothing_type}")
                return []
            
            # Случайный выбор с предпочтением более качественным паттернам
            selected_files = random.sample(pattern_files, min(num, len(pattern_files)))
            
            examples = []
            for file_path in selected_files:
                try:
                    # Загружаем полный паттерн
                    pattern = self.load_gpg_pattern(file_path)
                    
                    # Применяем кривые если они есть
                    pattern = self.apply_dataset_curves(pattern, style="standard")
                    
                    # Добавляем метаданные о качестве
                    pattern['reference_metadata'] = {
                        'source_file': str(file_path),
                        'clothing_type': clothing_type,
                        'has_curves': len(pattern.get('curves', {})) > 0,
                        'points_count': len(pattern.get('points', {})),
                        'lines_count': len(pattern.get('lines', {})),
                        'curves_count': len(pattern.get('curves', {})),
                        'quality_score': self._calculate_pattern_quality(pattern)
                    }
                    
                    examples.append(pattern)
                except Exception as e:
                    logging.warning(f"Failed to load pattern {file_path}: {e}")
                    continue
            
            # Сортируем по качеству
            examples.sort(key=lambda x: x['reference_metadata']['quality_score'], reverse=True)
            
            return examples[:num]
            
        except Exception as e:
            logging.error(f"Failed to get reference examples: {e}")
            return []
    
    def _calculate_pattern_quality(self, pattern: Dict[str, Any]) -> float:
        """
        Расчитывает качество паттерна для выбора лучших референсов
        
        Args:
            pattern: Паттерн для оценки
            
        Returns:
            float: Оценка качества (0..1)
        """
        try:
            score = 0.0
            
            # Наличие кривых (+0.3)
            if len(pattern.get('curves', {})) > 0:
                score += 0.3
            
            # Количество точек (оптимально 10-50, +0.2)
            points_count = len(pattern.get('points', {}))
            if 10 <= points_count <= 50:
                score += 0.2
            elif points_count > 5:
                score += 0.1
            
            # Количество линий (оптимально 5-20, +0.2)
            lines_count = len(pattern.get('lines', {}))
            if 5 <= lines_count <= 20:
                score += 0.2
            elif lines_count > 3:
                score += 0.1
            
            # Наличие метаданных (+0.1)
            if pattern.get('metadata'):
                score += 0.1
            
            # Наличие constraints (+0.1)
            if pattern.get('constraints'):
                score += 0.1
            
            # Сложность (не слишком простая, не слишком сложная)
            complexity = points_count + lines_count + len(pattern.get('curves', {}))
            if 15 <= complexity <= 100:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.0
    
    def average_reference_patterns(self, reference_patterns: List[Dict[str, Any]], 
                               target_measurements: Dict[str, float]) -> Dict[str, Any]:
        """
        Усредняет точки и кривые из референсов, адаптируя под целевые мерки
        
        Args:
            reference_patterns: Список референсных паттернов
            target_measurements: Целевые мерки для адаптации
            
        Returns:
            Усредненный паттерн с адаптированными точками и кривыми
        """
        if not reference_patterns:
            return {}
        
        try:
            # Извлекаем измерения из референсов
            ref_measurements = []
            for pattern in reference_patterns:
                metadata = pattern.get('metadata', {})
                ref_meas = {
                    'waist': metadata.get('waist', 68),
                    'hips': metadata.get('hips', 94),
                    'bust': metadata.get('bust', 90),
                    'height': metadata.get('height', 168)
                }
                ref_measurements.append(ref_meas)
            
            # Рассчитываем коэффициенты масштабирования
            if ref_measurements:
                avg_ref = {
                    'waist': sum(m['waist'] for m in ref_measurements) / len(ref_measurements) if len(ref_measurements) > 0 else 68,
                    'hips': sum(m['hips'] for m in ref_measurements) / len(ref_measurements) if len(ref_measurements) > 0 else 94,
                    'bust': sum(m['bust'] for m in ref_measurements) / len(ref_measurements) if len(ref_measurements) > 0 else 90,
                    'height': sum(m['height'] for m in ref_measurements) / len(ref_measurements) if len(ref_measurements) > 0 else 168
                }
                
                # Избегаем деления на ноль
                scale_factors = {
                    'waist': target_measurements.get('waist', 68) / avg_ref['waist'] if avg_ref['waist'] > 0 else 1.0,
                    'hips': target_measurements.get('hips', 94) / avg_ref['hips'] if avg_ref['hips'] > 0 else 1.0,
                    'bust': target_measurements.get('bust', 90) / avg_ref['bust'] if avg_ref['bust'] > 0 else 1.0,
                    'height': target_measurements.get('height', 168) / avg_ref['height'] if avg_ref['height'] > 0 else 1.0
                }
            else:
                scale_factors = {'waist': 1.0, 'hips': 1.0, 'bust': 1.0, 'height': 1.0}
            
            # Усредняем точки
            averaged_pattern = {
                'points': {},
                'lines': {},
                'curves': {},
                'metadata': {}
            }
            
            # Собираем все уникальные имена точек
            all_point_names = set()
            for pattern in reference_patterns:
                all_point_names.update(pattern.get('points', {}).keys())
            
            # Усредняем координаты точек
            for point_name in all_point_names:
                points = []
                for pattern in reference_patterns:
                    if point_name in pattern.get('points', {}):
                        points.append(pattern['points'][point_name])
                
                if points:
                    # Усредняем координаты
                    avg_x = sum(p['x'] for p in points) / len(points)
                    avg_y = sum(p['y'] for p in points) / len(points)
                    
                    # Применяем масштабирование в зависимости от типа точки
                    scale_x, scale_y = self._get_point_scale_factors(point_name, scale_factors)
                    
                    averaged_pattern['points'][point_name] = {
                        'x': avg_x * scale_x,
                        'y': avg_y * scale_y
                    }
            
            # Усредняем линии (сохраняем связи между точками)
            all_line_names = set()
            for pattern in reference_patterns:
                all_line_names.update(pattern.get('lines', {}).keys())
            
            for line_name in all_line_names:
                lines = []
                for pattern in reference_patterns:
                    if line_name in pattern.get('lines', {}):
                        lines.append(pattern['lines'][line_name])
                
                if lines:
                    # Берем первую линию как основу (они должны быть похожи)
                    base_line = lines[0].copy()
                    
                    # Обновляем имена точек на усредненные
                    if 'start' in base_line and base_line['start'] in averaged_pattern['points']:
                        base_line['start'] = base_line['start']
                    if 'end' in base_line and base_line['end'] in averaged_pattern['points']:
                        base_line['end'] = base_line['end']
                    
                    averaged_pattern['lines'][line_name] = base_line
            
            # Усредняем кривые (ВАЖНО - сохраняем кривизну)
            all_curve_names = set()
            for pattern in reference_patterns:
                all_curve_names.update(pattern.get('curves', {}).keys())
            
            for curve_name in all_curve_names:
                curves = []
                for pattern in reference_patterns:
                    if curve_name in pattern.get('curves', {}):
                        curves.append(pattern['curves'][curve_name])
                
                if curves:
                    # Усредняем контрольные точки
                    base_curve = curves[0].copy()
                    
                    # Усредняем контрольные точки если они есть
                    for control_point in ['control1', 'control2']:
                        control_points = []
                        for curve in curves:
                            if control_point in curve:
                                control_points.append(curve[control_point])
                        
                        if control_points:
                            avg_cx = sum(cp['x'] for cp in control_points) / len(control_points)
                            avg_cy = sum(cp['y'] for cp in control_points) / len(control_points)
                            
                            # Применяем масштабирование
                            scale_x, scale_y = self._get_point_scale_factors(curve_name, scale_factors)
                            
                            base_curve[control_point] = {
                                'x': avg_cx * scale_x,
                                'y': avg_cy * scale_y
                            }
                    
                    # Обновляем имена точек
                    if 'start' in base_curve and base_curve['start'] in averaged_pattern['points']:
                        base_curve['start'] = base_curve['start']
                    if 'end' in base_curve and base_curve['end'] in averaged_pattern['points']:
                        base_curve['end'] = base_curve['end']
                    
                    averaged_pattern['curves'][curve_name] = base_curve
            
            # Создаем метаданные
            averaged_pattern['metadata'] = {
                'pattern_type': reference_patterns[0].get('metadata', {}).get('pattern_type', 'unknown'),
                'construction_method': 'dataset_averaged',
                'averaged_from': len(reference_patterns),
                'scale_factors': scale_factors,
                'target_measurements': target_measurements,
                'reference_quality_scores': [
                    p.get('reference_metadata', {}).get('quality_score', 0.0) 
                    for p in reference_patterns
                ]
            }
            
            return averaged_pattern
            
        except Exception as e:
            logging.error(f"Failed to average reference patterns: {e}")
            return {}
    
    def _get_point_scale_factors(self, point_name: str, scale_factors: Dict[str, float]) -> Tuple[float, float]:
        """
        Определяет коэффициенты масштабирования для точки в зависимости от ее типа
        
        Args:
            point_name: Имя точки
            scale_factors: Общие коэффициенты масштабирования
            
        Returns:
            Tuple[float, float]: Коэффициенты для X и Y
        """
        point_lower = point_name.lower()
        
        # Талия - используем масштаб талии
        if 'waist' in point_lower:
            return scale_factors.get('waist', 1.0), scale_factors.get('waist', 1.0)
        
        # Бедра - используем масштаб бедер
        elif 'hip' in point_lower:
            return scale_factors.get('hips', 1.0), scale_factors.get('hips', 1.0)
        
        # Грудь - используем масштаб груди
        elif 'bust' in point_lower or 'chest' in point_lower:
            return scale_factors.get('bust', 1.0), scale_factors.get('bust', 1.0)
        
        # Вертикальные измерения - используем масштаб высоты
        elif any(keyword in point_lower for keyword in ['hem', 'bottom', 'length']):
            return scale_factors.get('height', 1.0), scale_factors.get('height', 1.0)
        
        # Боковые точки - усреднение талии и бедер
        elif 'side' in point_lower:
            waist_scale = scale_factors.get('waist', 1.0)
            hip_scale = scale_factors.get('hips', 1.0)
            return (waist_scale + hip_scale) / 2, (waist_scale + hip_scale) / 2
        
        # Центральные точки - используем средний масштаб
        elif 'center' in point_lower:
            avg_scale = sum(scale_factors.values()) / len(scale_factors)
            return avg_scale, avg_scale
        
        # По умолчанию - усредненный масштаб
        else:
            avg_scale = sum(scale_factors.values()) / len(scale_factors)
            return avg_scale, avg_scale
    
    def _find_pattern_files(self, clothing_type: str) -> List[Path]:
        """Поиск файлов паттернов для указанного типа одежды"""
        if not self.dataset_path.exists():
            logging.warning(f"Dataset path not found: {self.dataset_path}")
            return []
        
        pattern_files = []
        clothing_variants = [clothing_type.lower()]
        
        # Поиск JSON файлов
        patterns = [f"*{clothing_type}*.json", f"{clothing_type}*.json"]
        for pattern in patterns:
            files = list(self.dataset_path.rglob(pattern))
            pattern_files.extend(files)
        
        # Рекурсивный поиск папок с pattern.json или specification.json
        for variant in [clothing_type]:
            # Ищем папки, содержащие variant в названии
            for folder in self.dataset_path.rglob(f"*{variant}*"):
                if folder.is_dir():
                    # Проверяем pattern.json
                    pattern_json = folder / "pattern.json"
                    if pattern_json.exists():
                        pattern_files.append(pattern_json)
                    else:
                        # Проверяем specification.json (для юбок)
                        spec_json = folder / "specification.json"
                        if spec_json.exists():
                            pattern_files.append(spec_json)
        
        return list(set(pattern_files))  # Удаляем дубликаты
    
    def index_dataset(self, force_rebuild: bool = False) -> bool:
        """
        Индексирует датасет в FAISS для быстрого поиска с оптимизациями
        
        Args:
            force_rebuild: Принудительная перестройка индекса
            
        Returns:
            True если успешно
        """
        if not FAISS_AVAILABLE:
            logging.warning("FAISS not available. Cannot index dataset.")
            return False
        
        if not force_rebuild and self.index and self.metadata:
            logging.info("Dataset already indexed. Use force_rebuild=True to rebuild.")
            return True
        
        try:
            logging.info("Starting optimized dataset indexing...")
            
            # Поиск всех паттернов
            all_patterns = []
            for clothing_type in ['skirt', 'pants', 'shirt', 'dress', 'jacket']:
                pattern_files = self._find_pattern_files(clothing_type)
                
                # Для юбок используем все паттерны, для остальных - ограничение
                if clothing_type == 'skirt':
                    max_for_type = len(pattern_files)
                else:
                    max_for_type = min(len(pattern_files), self.config.max_patterns // 4)  # 250 для каждого типа
                
                # ЛОГ ПРОГРЕССА: загружаем паттерны с прогрессом
                for i, file_path in enumerate(pattern_files[:max_for_type]):
                    try:
                        pattern = self.load_gpg_pattern(file_path)
                        pattern['source_file'] = str(file_path)
                        pattern['clothing_type'] = clothing_type
                        all_patterns.append(pattern)
                        
                        # ЛОГ ПРОГРЕССА: каждые 10 паттернов
                        if (i + 1) % 10 == 0:
                            logging.info(f"Indexed {i + 1} / {len(pattern_files[:max_for_type])} {clothing_type} patterns")
                        
                    except Exception as e:
                        logging.warning(f"Failed to load {file_path}: {e}")
                        continue
            
            if not all_patterns:
                logging.warning("No patterns found for indexing")
                return False
            
            logging.info(f"Total patterns to index: {len(all_patterns)}")
            
            # Создание эмбеддингов с БАТЧАМИ
            embeddings = self._create_pattern_embeddings_batch(all_patterns)
            
            if embeddings is None:
                logging.error("Failed to create embeddings")
                return False
            
            # Создание FAISS индекса
            embedding_dim = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(embedding_dim)
            
            # Нормализация эмбеддингов
            faiss.normalize_L2(embeddings)
            
            # Добавление в индекс
            self.index.add(embeddings)
            
            # Сохранение метаданных
            self.metadata = all_patterns
            
            # Сохранение индекса
            faiss.write_index(self.index, self.config.index_path)
            with open(self.config.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logging.info(f"Successfully indexed {len(all_patterns)} patterns")
            logging.info("Indexing completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Dataset indexing failed: {e}")
            return False
    
    def _create_pattern_embeddings_batch(self, patterns: List[Dict[str, Any]], batch_size: int = 16) -> Optional[np.ndarray]:
        """Создание эмбеддингов для паттернов с БАТЧАМИ для ускорения"""
        try:
            if self.embedding_model is None:
                # Fallback: простые числовые признаки
                return self._create_fallback_embeddings(patterns)
            
            all_embeddings = []
            total_patterns = len(patterns)
            
            # Обработка батчами
            for i in range(0, total_patterns, batch_size):
                batch_patterns = patterns[i:i + batch_size]
                
                # Создание текстовых описаний для батча
                descriptions = []
                for pattern in batch_patterns:
                    desc = self._create_pattern_description(pattern)
                    descriptions.append(desc)
                
                # Генерация эмбеддингов для батча
                batch_embeddings = self.embedding_model.encode(descriptions, convert_to_numpy=True)
                all_embeddings.append(batch_embeddings)
                
                # ЛОГ ПРОГРЕССА для эмбеддингов
                batch_end = min(i + batch_size, total_patterns)
                logging.info(f"Generated embeddings for {batch_end} / {total_patterns} patterns")
            
            # Объединение всех эмбеддингов
            embeddings = np.vstack(all_embeddings)
            return embeddings
            
        except Exception as e:
            logging.error(f"Failed to create batch embeddings: {e}")
            return None
    
    def _create_pattern_embeddings(self, patterns: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """Создание эмбеддингов для паттернов (старый метод для совместимости)"""
        return self._create_pattern_embeddings_batch(patterns)
    
    def _create_pattern_description(self, pattern: Dict[str, Any]) -> str:
        """Создание текстового описания паттерна для эмбеддинга с реальными признаками"""
        meta = pattern.get("metadata", {})
        
        garment = meta.get("garment_type", pattern.get('pattern_type', 'skirt'))
        panels = meta.get("panels", 2)
        waist = meta.get("waist", 0)
        hips = meta.get("hips", 0)
        silhouette = meta.get("silhouette", "straight")

        return (
            f"{garment} pattern, "
            f"{panels} panels, "
            f"waist {waist} cm, "
            f"hips {hips} cm, "
            f"silhouette {silhouette}"
        )
    
    def build_embedding_text(self, pattern: Dict[str, Any]) -> str:
        """Псевдоним для _create_pattern_description для совместимости"""
        return self._create_pattern_description(pattern)
    
    def _create_fallback_embeddings(self, patterns: List[Dict[str, Any]]) -> np.ndarray:
        """Создание простых числовых эмбеддингов (fallback)"""
        embeddings = []
        
        for pattern in patterns:
            # Числовые признаки
            features = [
                len(pattern.get('points', {})),
                len(pattern.get('lines', {})),
                len(pattern.get('curves', {})),
                hash(pattern.get('pattern_type', '')) % 100,
                hash(pattern.get('construction_method', '')) % 100
            ]
            
            # Нормализация
            features = np.array(features, dtype=np.float32)
            features = features / (np.linalg.norm(features) + 1e-8)
            
            embeddings.append(features)
        
        return np.array(embeddings, dtype=np.float32)
    
    def search_similar_patterns(self, query_pattern: Dict[str, Any], top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Поиск похожих паттернов в датасете
        
        Args:
            query_pattern: Запросный паттерн
            top_k: Количество результатов
            
        Returns:
            Список (паттерн, score) tuples
        """
        if not FAISS_AVAILABLE or self.index is None:
            logging.warning("FAISS index not available for search")
            return []
        
        try:
            # Создание эмбеддинга для запроса
            query_embedding = self._create_pattern_embeddings([query_pattern])
            
            if query_embedding is None:
                return []
            
            # Нормализация
            faiss.normalize_L2(query_embedding)
            
            # Поиск
            if len(self.metadata) == 0:
                logging.warning("No patterns indexed for search")
                return []
                
            top_k = max(1, top_k)  # Убедимся что top_k >= 1
            actual_k = min(top_k, len(self.metadata))
            
            logging.info(f"Searching with k={actual_k}, total patterns={len(self.metadata)}")
            
            scores, indices = self.index.search(query_embedding, k=actual_k)
            
            results = []
            # scores и indices - это кортежи с одним элементом внутри
            scores_list = scores[0] if len(scores) > 0 else []
            indices_list = indices[0] if len(indices) > 0 else []
            
            for score, idx in zip(scores_list, indices_list):
                if idx < len(self.metadata):
                    # Фильтруем по порогу похожести
                    if float(score) >= SIMILARITY_THRESHOLD:
                        pattern = self.metadata[idx]
                        results.append((pattern, float(score)))
            
            # Если ничего не найдено по порогу, возвращаем лучшие результаты
            if not results and scores_list:
                logging.warning(f"No patterns found above threshold {SIMILARITY_THRESHOLD}, returning best matches")
                for score, idx in zip(scores_list, indices_list):
                    if idx < len(self.metadata):
                        pattern = self.metadata[idx]
                        results.append((pattern, float(score)))
                        # Возвращаем только топ-3 если нет подходящих по порогу
                        if len(results) >= 3:
                            break
            
            return results
            
        except Exception as e:
            logging.error(f"Pattern search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по датасету"""
        stats = {
            'indexed_patterns': len(self.metadata) if self.metadata else 0,
            'dataset_path': str(self.dataset_path),
            'index_available': FAISS_AVAILABLE and self.index is not None,
            'embedding_model': self.config.embedding_model if self.embedding_model else 'fallback'
        }
        
        if self.metadata:
            # Распределение по типам
            type_counts = {}
            for pattern in self.metadata:
                ptype = pattern.get('pattern_type', 'unknown')
                type_counts[ptype] = type_counts.get(ptype, 0) + 1
            
            stats['type_distribution'] = type_counts
            
            # Средние значения
            points_counts = [len(p.get('points', {})) for p in self.metadata]
            lines_counts = [len(p.get('lines', {})) for p in self.metadata]
            
            stats['avg_points'] = np.mean(points_counts) if points_counts else 0
            stats['avg_lines'] = np.mean(lines_counts) if lines_counts else 0
        
        return stats
    
    def normalize_skirt_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Нормализация лекала юбки к стандартной системе координат
        
        Args:
            pattern: Исходный паттерн юбки
            
        Returns:
            Нормализованный паттерн с зонами
        """
        try:
            if not pattern or pattern.get('pattern_type') != 'skirt':
                logging.warning("Pattern is not a skirt type")
                return pattern
            
            # Копируем паттерн для модификации
            normalized = json.loads(json.dumps(pattern))
            
            # 1. Определяем ключевые точки
            points = normalized.get('points', {})
            lines = normalized.get('lines', {})
            
            # Находим waistline точки (содержат 'waist' или 'top')
            waist_points = {}
            for name, point in points.items():
                name_lower = name.lower()
                if any(key in name_lower for key in ['waist', 'top', 'upper']):
                    waist_points[name] = point
            
            # Находим hemline точки (содержат 'hem', 'bottom', 'lower')
            hem_points = {}
            for name, point in points.items():
                name_lower = name.lower()
                if any(key in name_lower for key in ['hem', 'bottom', 'lower']):
                    hem_points[name] = point
            
            # Находим center_line точки (содержат 'center', 'middle', 'front')
            center_points = {}
            for name, point in points.items():
                name_lower = name.lower()
                if any(key in name_lower for key in ['center', 'middle', 'front']):
                    center_points[name] = point
            
            # Находим side_seam точки (содержат 'side', 'left', 'right')
            side_points = {}
            for name, point in points.items():
                name_lower = name.lower()
                if any(key in name_lower for key in ['side', 'left', 'right']):
                    side_points[name] = point
            
            # 2. Определяем начало координат (верх середины переда)
            origin_x, origin_y = 0, 0
            
            if waist_points:
                # Ищем центральную точку waistline
                if 'waist_center' in waist_points:
                    origin_x, origin_y = waist_points['waist_center']['x'], waist_points['waist_center']['y']
                elif 'center_front' in waist_points:
                    origin_x, origin_y = waist_points['center_front']['x'], waist_points['center_front']['y']
                elif 'front_waist' in waist_points:
                    origin_x, origin_y = waist_points['front_waist']['x'], waist_points['front_waist']['y']
                else:
                    # Берем среднюю точку между крайними waist точками
                    waist_x_coords = [p['x'] for p in waist_points.values()]
                    waist_y_coords = [p['y'] for p in waist_points.values()]
                    origin_x = np.mean(waist_x_coords)
                    origin_y = np.mean(waist_y_coords)
            else:
                # Если нет waist точек, используем (0,0)
                origin_x, origin_y = 0, 0
            
            # 3. Смещаем все точки к началу координат
            for point_name, point_data in normalized.get('points', {}).items():
                point_data['x'] = point_data['x'] - origin_x
                point_data['y'] = point_data['y'] - origin_y
            
            # 4. Масштабируем в миллиметры (предполагаем что вход в см)
            scale_factor = 10.0  # см -> мм
            for point_name, point_data in normalized.get('points', {}).items():
                point_data['x'] = point_data['x'] * scale_factor
                point_data['y'] = point_data['y'] * scale_factor
            
            # 5. Обновляем линии с новыми координатами
            for line_name, line_data in normalized.get('lines', {}).items():
                if 'start' in line_data:
                    start_name = line_data['start']
                    if isinstance(start_name, dict) and 'x' in start_name:
                        # Прямые координаты в линии
                        line_data['start']['x'] = (line_data['start']['x'] - origin_x) * scale_factor
                        line_data['start']['y'] = (line_data['start']['y'] - origin_y) * scale_factor
                    elif start_name in normalized.get('points', {}):
                        # Ссылка на точку
                        point = normalized['points'][start_name]
                        line_data['start'] = {'x': point['x'], 'y': point['y']}
                
                if 'end' in line_data:
                    end_name = line_data['end']
                    if isinstance(end_name, dict) and 'x' in end_name:
                        # Прямые координаты в линии
                        line_data['end']['x'] = (line_data['end']['x'] - origin_x) * scale_factor
                        line_data['end']['y'] = (line_data['end']['y'] - origin_y) * scale_factor
                    elif end_name in normalized.get('points', {}):
                        # Ссылка на точку
                        point = normalized['points'][end_name]
                        line_data['end'] = {'x': point['x'], 'y': point['y']}
            
            # 6. Обновляем кривые с новыми координатами
            for curve_name, curve_data in normalized.get('curves', {}).items():
                for point_key in ['start', 'control1', 'control2', 'end']:
                    if point_key in curve_data:
                        point_ref = curve_data[point_key]
                        if isinstance(point_ref, dict) and 'x' in point_ref:
                            # Прямые координаты
                            curve_data[point_key]['x'] = (point_ref['x'] - origin_x) * scale_factor
                            curve_data[point_key]['y'] = (point_ref['y'] - origin_y) * scale_factor
                        elif isinstance(point_ref, str) and point_ref in normalized.get('points', {}):
                            # Ссылка на точку
                            point = normalized['points'][point_ref]
                            curve_data[point_key] = {'x': point['x'], 'y': point['y']}
            
            # 7. Определяем и сохраняем зоны
            zones = {}
            
            # Waistline зона
            if waist_points:
                waist_coords = [(p['x'], p['y']) for p in waist_points.values()]
                waist_x_coords = [coord[0] for coord in waist_coords]
                waist_y_coords = [coord[1] for coord in waist_coords]
                
                zones['waistline'] = {
                    'points': list(waist_points.keys()),
                    'bounds': {
                        'min_x': min(waist_x_coords),
                        'max_x': max(waist_x_coords),
                        'min_y': min(waist_y_coords),
                        'max_y': max(waist_y_coords)
                    },
                    'center_x': np.mean(waist_x_coords),
                    'center_y': np.mean(waist_y_coords),
                    'width': max(waist_x_coords) - min(waist_x_coords)
                }
            
            # Hemline зона
            if hem_points:
                hem_coords = [(p['x'], p['y']) for p in hem_points.values()]
                hem_x_coords = [coord[0] for coord in hem_coords]
                hem_y_coords = [coord[1] for coord in hem_coords]
                
                zones['hemline'] = {
                    'points': list(hem_points.keys()),
                    'bounds': {
                        'min_x': min(hem_x_coords),
                        'max_x': max(hem_x_coords),
                        'min_y': min(hem_y_coords),
                        'max_y': max(hem_y_coords)
                    },
                    'center_x': np.mean(hem_x_coords),
                    'center_y': np.mean(hem_y_coords),
                    'width': max(hem_x_coords) - min(hem_x_coords)
                }
            
            # Center_line зона
            if center_points:
                center_coords = [(p['x'], p['y']) for p in center_points.values()]
                center_x_coords = [coord[0] for coord in center_coords]
                center_y_coords = [coord[1] for coord in center_coords]
                
                zones['center_line'] = {
                    'points': list(center_points.keys()),
                    'bounds': {
                        'min_x': min(center_x_coords),
                        'max_x': max(center_x_coords),
                        'min_y': min(center_y_coords),
                        'max_y': max(center_y_coords)
                    },
                    'length': max(center_y_coords) - min(center_y_coords)
                }
            
            # Side_seam зона (левая и правая)
            if side_points:
                left_side = {}
                right_side = {}
                
                for name, point in side_points.items():
                    name_lower = name.lower()
                    if 'left' in name_lower:
                        left_side[name] = point
                    elif 'right' in name_lower:
                        right_side[name] = point
                    else:
                        # Определяем по координате X
                        if point['x'] < 0:
                            left_side[name] = point
                        else:
                            right_side[name] = point
                
                zones['side_seam'] = {
                    'left_side': {
                        'points': list(left_side.keys()),
                        'bounds': {
                            'min_x': min([p['x'] for p in left_side.values()]) if left_side else 0,
                            'max_x': max([p['x'] for p in left_side.values()]) if left_side else 0,
                            'min_y': min([p['y'] for p in left_side.values()]) if left_side else 0,
                            'max_y': max([p['y'] for p in left_side.values()]) if left_side else 0
                        }
                    },
                    'right_side': {
                        'points': list(right_side.keys()),
                        'bounds': {
                            'min_x': min([p['x'] for p in right_side.values()]) if right_side else 0,
                            'max_x': max([p['x'] for p in right_side.values()]) if right_side else 0,
                            'min_y': min([p['y'] for p in right_side.values()]) if right_side else 0,
                            'max_y': max([p['y'] for p in right_side.values()]) if right_side else 0
                        }
                    }
                }
            
            # 8. Добавляем метаданные нормализации
            normalized['normalization'] = {
                'origin': {'x': 0, 'y': 0},  # Всегда (0,0) после нормализации
                'scale_factor': scale_factor,
                'units': 'mm',
                'coordinate_system': {
                    'x_axis': 'width (horizontal)',
                    'y_axis': 'down (vertical)',
                    'origin': 'top center front'
                },
                'zones': zones
            }
            
            # 9. Обновляем метод конструирования
            normalized['construction_method'] = f"{normalized.get('construction_method', 'unknown')}_normalized"
            
            logging.info(f"Skirt pattern normalized: {len(points)} points, {len(zones)} zones")
            
            return normalized
            
        except Exception as e:
            logging.error(f"Pattern normalization failed: {e}")
            return pattern
    
    def extract_construction_rules(self, pattern: Dict[str, Any]) -> Dict[str, float]:
        """
        Извлекает правила кроя из паттерна юбки
        
        Args:
            pattern: Унифицированный паттерн (предпочтительно нормализованный)
            
        Returns:
            Dict с правилами кроя:
            - waist_width: ширина талии
            - hip_width: ширина бедер  
            - hem_width: ширина подола
            - side_seam_curve: кривизна бокового шва
            - front_back_difference: разница между передней и задней частью
        """
        try:
            rules = {}
            
            # Получаем зоны из нормализованного паттерна
            zones = pattern.get('normalization', {}).get('zones', {})
            
            # 1. Вычисляем waist_width
            waistline = zones.get('waistline', {})
            if waistline and 'width' in waistline:
                rules['waist_width'] = float(waistline['width'])
            else:
                # Если нет зоны, вычисляем по точкам с "waist" в названии
                waist_points = []
                for point_name, point_data in pattern.get('points', {}).items():
                    if 'waist' in point_name.lower():
                        waist_points.append(point_data.get('x', 0))
                if waist_points:
                    rules['waist_width'] = float(max(waist_points) - min(waist_points))
                else:
                    rules['waist_width'] = 0.0
            
            # 2. Вычисляем hip_width
            # Ищем точки с "hip" в названии или вычисляем на уровне бедер
            hip_points = []
            for point_name, point_data in pattern.get('points', {}).items():
                if 'hip' in point_name.lower():
                    hip_points.append(point_data.get('x', 0))
            
            if hip_points:
                rules['hip_width'] = float(max(hip_points) - min(hip_points))
            else:
                # Приблизительно: ищем точки на уровне 1/3 от талии до подола
                hemline = zones.get('hemline', {})
                if hemline and 'center_y' in hemline and waistline and 'center_y' in waistline:
                    hip_level = waistline['center_y'] + (hemline['center_y'] - waistline['center_y']) * 0.33
                    
                    hip_x_points = []
                    for point_data in pattern.get('points', {}).values():
                        if abs(point_data.get('y', 0) - hip_level) < 20:  # допуск 20мм
                            hip_x_points.append(point_data.get('x', 0))
                    
                    if hip_x_points:
                        rules['hip_width'] = float(max(hip_x_points) - min(hip_x_points))
                    else:
                        rules['hip_width'] = rules.get('waist_width', 0.0) * 1.2  # типичная пропорция
                else:
                    rules['hip_width'] = rules.get('waist_width', 0.0) * 1.2
            
            # 3. Вычисляем hem_width
            hemline = zones.get('hemline', {})
            if hemline and 'width' in hemline:
                rules['hem_width'] = float(hemline['width'])
            else:
                # Если нет зоны, вычисляем по точкам с "hem" в названии
                hem_points = []
                for point_name, point_data in pattern.get('points', {}).items():
                    if 'hem' in point_name.lower() or 'bottom' in point_name.lower():
                        hem_points.append(point_data.get('x', 0))
                if hem_points:
                    rules['hem_width'] = float(max(hem_points) - min(hem_points))
                else:
                    # Ищем самые нижние точки
                    all_y = [p.get('y', 0) for p in pattern.get('points', {}).values()]
                    if all_y:
                        bottom_y = max(all_y)
                        bottom_x = [p.get('x', 0) for p in pattern.get('points', {}).values() 
                                  if abs(p.get('y', 0) - bottom_y) < 20]
                        if bottom_x:
                            rules['hem_width'] = float(max(bottom_x) - min(bottom_x))
                        else:
                            rules['hem_width'] = rules.get('waist_width', 0.0) * 1.5
                    else:
                        rules['hem_width'] = 0.0
            
            # 4. Вычисляем side_seam_curve
            side_seam = zones.get('side_seam', {})
            if side_seam:
                # Анализируем кривизну бокового шва
                left_side = side_seam.get('left_side', {})
                right_side = side_seam.get('right_side', {})
                
                # Вычисляем отклонение от прямой линии
                curve_values = []
                
                for side_name, side_data in [('left', left_side), ('right', right_side)]:
                    if side_data and 'bounds' in side_data:
                        bounds = side_data['bounds']
                        min_y = bounds.get('min_y', 0)
                        max_y = bounds.get('max_y', 0)
                        
                        if max_y - min_y > 0:
                            # Ищем точки бокового шва
                            side_points = []
                            for point_name, point_data in pattern.get('points', {}).items():
                                if 'side' in point_name.lower() and side_name in point_name.lower():
                                    side_points.append(point_data)
                            
                            if len(side_points) >= 3:
                                # Вычисляем кривизну через отклонение от прямой
                                y_coords = [p['y'] for p in side_points]
                                x_coords = [p['x'] for p in side_points]
                                
                                # Линейная интерполяция
                                y_range = max(y_coords) - min(y_coords)
                                if y_range > 0:
                                    expected_x = []
                                    for i, y in enumerate(y_coords):
                                        t = (y - min(y_coords)) / y_range
                                        expected = x_coords[0] + t * (x_coords[-1] - x_coords[0])
                                        expected_x.append(expected)
                                    
                                    # Среднее отклонение
                                    deviations = [abs(actual - expected) 
                                               for actual, expected in zip(x_coords, expected_x)]
                                    curve_values.append(sum(deviations) / len(deviations))
                
                if curve_values:
                    rules['side_seam_curve'] = float(sum(curve_values) / len(curve_values))
                else:
                    rules['side_seam_curve'] = 0.0
            else:
                rules['side_seam_curve'] = 0.0
            
            # 5. Вычисляем front_back_difference
            # Разница между передней и задней частями юбки
            center_points = []
            for point_name, point_data in pattern.get('points', {}).items():
                if 'center' in point_name.lower() or 'centre' in point_name.lower():
                    center_points.append(point_data)
            
            if center_points:
                # Ищем передние и задние центральные точки
                front_center = None
                back_center = None
                
                for point in center_points:
                    if 'front' in str(point).lower():
                        front_center = point
                    elif 'back' in str(point).lower():
                        back_center = point
                
                if front_center and back_center:
                    rules['front_back_difference'] = abs(float(back_center.get('y', 0) - front_center.get('y', 0)))
                else:
                    # Если нет четкого разделения, используем Y-разброс
                    y_coords = [p.get('y', 0) for p in center_points]
                    rules['front_back_difference'] = float(max(y_coords) - min(y_coords))
            else:
                # Приблизительно: 1/3 от общей высоты
                all_y = [p.get('y', 0) for p in pattern.get('points', {}).values()]
                if all_y:
                    rules['front_back_difference'] = float(max(all_y) - min(all_y)) * 0.33
                else:
                    rules['front_back_difference'] = 0.0
            
            # 6. Вычисляем дополнительные полезные коэффициенты
            if rules.get('waist_width', 0) > 0:
                rules['hip_to_waist_ratio'] = rules.get('hip_width', 0) / rules['waist_width']
                rules['hem_to_waist_ratio'] = rules.get('hem_width', 0) / rules['waist_width']
                # ПРАВИЛЬНАЯ ФОРМУЛА: flare_ratio = bottom_width / waist_width
                rules['flare_ratio'] = rules.get('hem_width', 0) / rules['waist_width']
            else:
                rules['hip_to_waist_ratio'] = 1.0
                rules['hem_to_waist_ratio'] = 1.0
                rules['flare_ratio'] = 0.0
            
            # 7. Авто-извлечение силуэта на основе flare_ratio
            flare_ratio = rules.get('flare_ratio', 0)
            if flare_ratio < 1.1:
                rules['silhouette_type'] = 'straight'
            elif flare_ratio <= 1.4:
                rules['silhouette_type'] = 'a_line'
            else:
                rules['silhouette_type'] = 'flared'
            
            logging.info(f"Construction rules extracted: {len(rules)} parameters")
            return rules
            
        except Exception as e:
            logging.error(f"Failed to extract construction rules: {e}")
            return {
                'waist_width': 0.0,
                'hip_width': 0.0,
                'hem_width': 0.0,
                'side_seam_curve': 0.0,
                'front_back_difference': 0.0,
                'hip_to_waist_ratio': 1.0,
                'hem_to_waist_ratio': 1.0,
                'flare_ratio': 0.0,
                'silhouette_type': 'unknown'
            }
    
    def apply_dataset_curves(self, pattern: Dict[str, Any], style: str = "flare") -> Dict[str, Any]:
        """
        Применяет кривые из датасета к паттерну
        
        Args:
            pattern: Исходный паттерн
            style: Стиль для применения кривых
            
        Returns:
            Паттерн с примененными кривыми
        """
        # Получаем кривые из датасета
        dataset_curves = pattern.get('curves', {})
        
        if not dataset_curves:
            # Если кривых нет, генерируем для стиля flare
            if style == "flare":
                pattern = self._generate_flare_curves(pattern)
            return pattern
        
        # Применяем существующие кривые из датасета
        enhanced_pattern = pattern.copy()
        enhanced_pattern['curves_applied'] = True
        enhanced_pattern['curve_style'] = style
        
        # Обновляем метаданные
        if 'metadata' not in enhanced_pattern:
            enhanced_pattern['metadata'] = {}
        
        enhanced_pattern['metadata']['dataset_curves'] = len(dataset_curves)
        enhanced_pattern['metadata']['curve_types'] = [
            curve.get('curve_type', 'unknown') for curve in dataset_curves.values()
        ]
        
        return enhanced_pattern
    
    def _generate_flare_curves(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует кривые для стиля flare если их нет в датасете
        
        Args:
            pattern: Исходный паттерн
            
        Returns:
            Паттерн с сгенерированными кривыми
        """
        enhanced_pattern = pattern.copy()
        curves = {}
        
        points = pattern.get('points', {})
        lines = pattern.get('lines', {})
        
        # Ищем боковые швы для создания кривых
        side_seam_lines = [
            (name, line) for name, line in lines.items()
            if 'side' in name.lower() or 'seam' in name.lower()
        ]
        
        for line_name, line_data in side_seam_lines:
            start_name = line_data.get('start')
            end_name = line_data.get('end')
            
            if start_name in points and end_name in points:
                start_point = points[start_name]
                end_point = points[end_name]
                
                # Создаем контрольные точки для кривой Безье
                dx = end_point['x'] - start_point['x']
                dy = end_point['y'] - start_point['y']
                
                # Смещение для расклешения (5-10 см)
                curve_offset = 80.0  # 8 см
                
                # Контрольные точки
                control1 = {
                    'x': start_point['x'] + dx * 0.3 + curve_offset,
                    'y': start_point['y'] + dy * 0.3
                }
                
                control2 = {
                    'x': start_point['x'] + dx * 0.7 + curve_offset,
                    'y': start_point['y'] + dy * 0.7
                }
                
                curves[f"{line_name}_curve"] = {
                    'start': start_name,
                    'control1': control1,
                    'control2': control2,
                    'end': end_name,
                    'curve_type': 'bezier',
                    'curve_strength': 1.0,
                    'generated': True
                }
        
        enhanced_pattern['curves'] = curves
        enhanced_pattern['curves_applied'] = True
        enhanced_pattern['curve_style'] = 'flare'
        
        # Обновляем метаданные
        if 'metadata' not in enhanced_pattern:
            enhanced_pattern['metadata'] = {}
        
        enhanced_pattern['metadata']['generated_curves'] = len(curves)
        enhanced_pattern['metadata']['curve_generation_method'] = 'flare_auto'
        
        return enhanced_pattern
