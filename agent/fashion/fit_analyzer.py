"""
Fashion Fit Analyzer Module

Модуль для анализа посадки лекал и проверки корректности конструкции
"""

from typing import Dict, Any, List, Tuple
import math
import logging

# Опциональная интеграция с датасетом
try:
    from .dataset_integration import DatasetIntegration, DatasetConfig
    from ..config import CONFIG
    DATASET_AVAILABLE = True
except ImportError:
    DATASET_AVAILABLE = False


class FitAnalyzer:
    """Анализатор посадки лекал"""
    
    def __init__(self, use_dataset: bool = True):
        """
        Инициализация анализатора
        
        Args:
            use_dataset: Использовать датасет для валидации (если доступен)
        """
        # Стандартные допуски и соотношения
        self.tolerances = {
            'armhole_sleeve_ratio': {'min': 0.28, 'max': 0.35, 'optimal': 0.33},
            'front_back_balance': {'min': 0.95, 'max': 1.05, 'optimal': 1.0},
            'shoulder_slope_ratio': {'min': 0.15, 'max': 0.25, 'optimal': 0.2},
            'pattern_symmetry': {'tolerance': 0.5},  # см
            'seam_continuity': {'tolerance': 0.2}  # см
        }
        
        # Стандартные пропорции тела
        self.body_proportions = {
            'armhole_to_chest': 0.45,  # пройма = 45% от обхвата груди
            'shoulder_to_chest': 0.25,  # плечо = 25% от обхвата груди
            'front_to_back_length': 1.02  # перед длиннее спинки на 2%
        }
        
        # Инициализация датасета (если доступен и запрошен)
        self.dataset_integration = None
        if use_dataset and DATASET_AVAILABLE:
            try:
                fashion_config = CONFIG.get('fashion', {})
                dataset_config = DatasetConfig(
                    dataset_path=fashion_config.get('dataset_path', ''),
                    index_path=fashion_config.get('dataset_index_path', ''),
                    metadata_path=fashion_config.get('dataset_metadata_path', ''),
                    embedding_model=fashion_config.get('embedding_model', 'all-MiniLM-L6-v2'),
                    max_patterns=fashion_config.get('max_dataset_patterns', 1000)
                )
                self.dataset_integration = DatasetIntegration(dataset_config)
                logging.info("Dataset integration enabled for FitAnalyzer")
            except Exception as e:
                logging.warning(f"Failed to initialize dataset integration: {e}")
                self.dataset_integration = None
    
    def check_armhole_vs_sleeve(self, armhole_length: float, sleeve_cap_length: float) -> Dict[str, Any]:
        """
        Проверка соотношения проймы и оката рукава
        
        Args:
            armhole_length: Длина проймы
            sleeve_cap_length: Длина оката рукава
            
        Returns:
            Результат проверки с предупреждениями и рекомендациями
        """
        result = {
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'status': 'ok'
        }
        
        if armhole_length <= 0 or sleeve_cap_length <= 0:
            result['errors'].append('Длина проймы и оката должны быть положительными')
            result['status'] = 'error'
            return result
        
        # Расчет соотношения
        ratio = sleeve_cap_length / armhole_length
        optimal_ratio = self.tolerances['armhole_sleeve_ratio']['optimal']
        min_ratio = self.tolerances['armhole_sleeve_ratio']['min']
        max_ratio = self.tolerances['armhole_sleeve_ratio']['max']
        
        # Проверка соотношения
        if ratio < min_ratio:
            result['warnings'].append(f'Окат рукава слишком короткий ({ratio:.3f} < {min_ratio:.2f})')
            result['recommendations'].append(f'Увеличьте длину оката рукава до {armhole_length * optimal_ratio:.1f} см')
            result['status'] = 'warning'
        elif ratio > max_ratio:
            result['warnings'].append(f'Окат рукава слишком длинный ({ratio:.3f} > {max_ratio:.2f})')
            result['recommendations'].append(f'Уменьшите длину оката рукава до {armhole_length * optimal_ratio:.1f} см')
            result['status'] = 'warning'
        else:
            result['recommendations'].append(f'Соотношение оката к пройме оптимальное ({ratio:.3f})')
        
        # Дополнительная проверка абсолютных значений
        if armhole_length < 30:
            result['warnings'].append('Пройма слишком короткая для стандартной фигуры')
            result['recommendations'].append('Проверьте мерки обхвата груди')
            result['status'] = 'warning'
        
        if armhole_length > 60:
            result['warnings'].append('Пройма слишком длинная - возможна ошибка в мерках')
            result['recommendations'].append('Убедитесь в корректности мерок')
            result['status'] = 'warning'
        
        # Добавляем детальную информацию
        result['analysis'] = {
            'armhole_length': armhole_length,
            'sleeve_cap_length': sleeve_cap_length,
            'ratio': ratio,
            'optimal_ratio': optimal_ratio,
            'difference': sleeve_cap_length - (armhole_length * optimal_ratio),
            'fit_assessment': self._assess_sleeve_fit(ratio)
        }
        
        return result
    
    def check_balance(self, front_length: float, back_length: float) -> Dict[str, Any]:
        """
        Проверка баланса переда и спинки
        
        Args:
            front_length: Длина переда
            back_length: Длина спинки
            
        Returns:
            Результат проверки баланса
        """
        result = {
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'status': 'ok'
        }
        
        if front_length <= 0 or back_length <= 0:
            result['errors'].append('Длины переда и спинки должны быть положительными')
            result['status'] = 'error'
            return result
        
        # Расчет соотношения
        ratio = front_length / back_length
        optimal_ratio = self.tolerances['front_back_balance']['optimal']
        min_ratio = self.tolerances['front_back_balance']['min']
        max_ratio = self.tolerances['front_back_balance']['max']
        
        # Проверка баланса
        if ratio < min_ratio:
            result['warnings'].append(f'Перед значительно короче спинки ({ratio:.3f} < {min_ratio:.2f})')
            result['recommendations'].append(f'Увеличьте длину переда или уменьшите спинку для баланса')
            result['status'] = 'warning'
        elif ratio > max_ratio:
            result['warnings'].append(f'Перед значительно длиннее спинки ({ratio:.3f} > {max_ratio:.2f})')
            result['recommendations'].append(f'Уменьшите длину переда или увеличьте спинку для баланса')
            result['status'] = 'warning'
        else:
            result['recommendations'].append(f'Баланс переда и спинки оптимальный ({ratio:.3f})')
        
        # Проверка абсолютной разницы
        difference = abs(front_length - back_length)
        if difference > 3:
            result['warnings'].append(f'Слишком большая разница между передом и спинкой ({difference:.1f} см)')
            result['recommendations'].append('Разница не должна превышать 2-3 см')
            result['status'] = 'warning'
        
        # Добавляем детальную информацию
        result['analysis'] = {
            'front_length': front_length,
            'back_length': back_length,
            'ratio': ratio,
            'difference': difference,
            'optimal_ratio': optimal_ratio,
            'balance_assessment': self._assess_balance(ratio)
        }
        
        return result
    
    def check_shoulder_slope(self, height: float, chest: float) -> Dict[str, Any]:
        """
        Проверка наклона плеча
        
        Args:
            height: Рост
            chest: Обхват груди
            
        Returns:
            Результат проверки наклона плеча
        """
        result = {
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'status': 'ok'
        }
        
        if height <= 0 or chest <= 0:
            result['errors'].append('Рост и обхват груди должны быть положительными')
            result['status'] = 'error'
            return result
        
        # Расчет оптимального наклона плеча
        # Стандартная формула: наклон = (обхват груди / 20) - (рост / 10)
        optimal_slope = (chest / 20) - (height / 10)
        
        # Альтернативный расчет через пропорции
        proportion_based_slope = self.body_proportions['shoulder_to_chest'] * chest / 4
        
        # Усредненный оптимальный наклон
        avg_optimal_slope = (optimal_slope + proportion_based_slope) / 2
        
        # Стандартные допуски
        min_slope = self.tolerances['shoulder_slope_ratio']['min']
        max_slope = self.tolerances['shoulder_slope_ratio']['max']
        
        # Нормализация наклона
        if avg_optimal_slope < 0:
            avg_optimal_slope = min_slope
        elif avg_optimal_slope > max_slope:
            avg_optimal_slope = max_slope
        
        # Проверка текущего наклона (если бы он был задан)
        # Здесь мы предполагаем, что нужно рассчитать рекомендуемый наклон
        
        # Проверка пропорций тела
        chest_to_height_ratio = chest / height
        if chest_to_height_ratio < 0.5:
            result['warnings'].append('Соотношение обхвата к росту меньше стандартного')
            result['recommendations'].append('Проверьте корректность мерок')
        elif chest_to_height_ratio > 0.7:
            result['warnings'].append('Соотношение обхвата к росту больше стандартного')
            result['recommendations'].append('Возможно нужна корректировка для нестандартной фигуры')
        
        # Добавляем детальную информацию
        result['analysis'] = {
            'height': height,
            'chest': chest,
            'chest_to_height_ratio': chest_to_height_ratio,
            'recommended_slope': avg_optimal_slope,
            'optimal_range': [min_slope, max_slope],
            'proportion_based_slope': proportion_based_slope,
            'formula_based_slope': optimal_slope,
            'fit_assessment': self._assess_shoulder_slope(avg_optimal_slope)
        }
        
        result['recommendations'].append(f'Рекомендуемый наклон плеча: {avg_optimal_slope:.2f} см')
        
        return result
    
    def validate_pattern(self, pieces: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация полного паттерна
        
        Args:
            pieces: Словарь с деталями паттерна
            
        Returns:
            Результат валидации
        """
        result = {
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'status': 'ok',
            'piece_analysis': {}
        }
        
        if not pieces:
            result['errors'].append('Нет деталей для валидации')
            result['status'] = 'error'
            return result
        
        # Валидация каждой детали
        for piece_name, piece_data in pieces.items():
            piece_result = self._validate_piece(piece_name, piece_data)
            result['piece_analysis'][piece_name] = piece_result
            
            # Добавляем предупреждения и ошибки общего уровня
            result['warnings'].extend(piece_result.get('warnings', []))
            result['errors'].extend(piece_result.get('errors', []))
            result['recommendations'].extend(piece_result.get('recommendations', []))
            
            if piece_result.get('status') == 'error':
                result['status'] = 'error'
            elif piece_result.get('status') == 'warning' and result['status'] == 'ok':
                result['status'] = 'warning'
        
        # Междетальная валидация
        inter_piece_result = self._validate_inter_piece_relations(pieces)
        result['warnings'].extend(inter_piece_result.get('warnings', []))
        result['errors'].extend(inter_piece_result.get('errors', []))
        result['recommendations'].extend(inter_piece_result.get('recommendations', []))
        
        if inter_piece_result.get('status') == 'error':
            result['status'] = 'error'
        elif inter_piece_result.get('status') == 'warning' and result['status'] == 'ok':
            result['status'] = 'warning'
        
        # Общая статистика
        total_points = sum(len(piece.get('points', [])) for piece in pieces.values())
        total_lines = sum(len(piece.get('lines', [])) for piece in pieces.values())
        
        result['summary'] = {
            'total_pieces': len(pieces),
            'total_points': total_points,
            'total_lines': total_lines,
            'pieces_with_errors': sum(1 for p in result['piece_analysis'].values() if p.get('status') == 'error'),
            'pieces_with_warnings': sum(1 for p in result['piece_analysis'].values() if p.get('status') == 'warning')
        }
        
        # Общие рекомендации
        if result['status'] == 'ok':
            result['recommendations'].append('Паттерн корректен и готов к производству')
        elif result['status'] == 'warning':
            result['recommendations'].append('Паттерн требует корректировки перед использованием')
        else:
            result['recommendations'].append('Паттерн содержит критические ошибки и требует исправления')
        
        return result
    
    def _validate_piece(self, piece_name: str, piece_data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация отдельной детали"""
        result = {
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'status': 'ok'
        }
        
        # Проверка наличия обязательных элементов
        required_elements = ['points', 'lines']
        for element in required_elements:
            if element not in piece_data:
                result['errors'].append(f'Отсутствует элемент {element} в детали {piece_name}')
                result['status'] = 'error'
        
        if result['status'] == 'error':
            return result
        
        # Валидация точек
        points = piece_data.get('points', [])
        if not points:
            result['warnings'].append(f'В детали {piece_name} нет точек')
            result['status'] = 'warning'
        else:
            point_validation = self._validate_points(points)
            result['warnings'].extend(point_validation['warnings'])
            result['errors'].extend(point_validation['errors'])
            if point_validation['status'] == 'error':
                result['status'] = 'error'
        
        # Валидация линий
        lines = piece_data.get('lines', [])
        if not lines:
            result['warnings'].append(f'В детали {piece_name} нет линий')
            result['status'] = 'warning'
        else:
            line_validation = self._validate_lines(lines)
            result['warnings'].extend(line_validation['warnings'])
            result['errors'].extend(line_validation['errors'])
            if line_validation['status'] == 'error':
                result['status'] = 'error'
        
        # Проверка связности
        if points and lines:
            connectivity_result = self._validate_connectivity(points, lines)
            result['warnings'].extend(connectivity_result['warnings'])
            result['errors'].extend(connectivity_result['errors'])
            if connectivity_result['status'] == 'error':
                result['status'] = 'error'
        
        # Добавляем статистику детали
        result['statistics'] = {
            'points_count': len(points),
            'lines_count': len(lines),
            'connected_points': connectivity_result.get('connected_points', 0),
            'dangling_lines': connectivity_result.get('dangling_lines', 0)
        }
        
        return result
    
    def _validate_inter_piece_relations(self, pieces: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация отношений между деталями"""
        result = {
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'status': 'ok'
        }
        
        # Проверка наличия обязательных деталей
        required_pieces = ['back', 'front']
        missing_pieces = []
        
        for piece in required_pieces:
            if piece not in pieces:
                missing_pieces.append(piece)
        
        if missing_pieces:
            result['errors'].append(f'Отсутствуют обязательные детали: {missing_pieces}')
            result['status'] = 'error'
        
        # Проверка соответствия деталей
        if 'back' in pieces and 'front' in pieces:
            back_points = pieces['back'].get('points', [])
            front_points = pieces['front'].get('points', [])
            
            # Проверка симметрии (если требуется)
            symmetry_result = self._check_piece_symmetry(back_points, front_points)
            result['warnings'].extend(symmetry_result['warnings'])
            
            # Проверка стыковки деталей
            matching_result = self._check_piece_matching(pieces)
            result['warnings'].extend(matching_result['warnings'])
            result['errors'].extend(matching_result['errors'])
            
            if matching_result['status'] == 'error':
                result['status'] = 'error'
        
        return result
    
    def _validate_points(self, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация точек"""
        result = {
            'warnings': [],
            'errors': [],
            'status': 'ok'
        }
        
        for i, point in enumerate(points):
            # Проверка наличия координат
            if 'x' not in point or 'y' not in point:
                result['errors'].append(f'Точка {i}: отсутствуют координаты x или y')
                result['status'] = 'error'
                continue
            
            # Проверка типа координат
            try:
                x_val = float(point['x'])
                y_val = float(point['y'])
                
                # Проверка на NaN или бесконечность
                if math.isnan(x_val) or math.isnan(y_val):
                    result['errors'].append(f'Точка {i}: координаты содержат NaN')
                    result['status'] = 'error'
                elif math.isinf(x_val) or math.isinf(y_val):
                    result['errors'].append(f'Точка {i}: координаты содержат бесконечность')
                    result['status'] = 'error'
                
            except (ValueError, TypeError):
                result['errors'].append(f'Точка {i}: некорректный тип координат')
                result['status'] = 'error'
        
        return result
    
    def _validate_lines(self, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация линий"""
        result = {
            'warnings': [],
            'errors': [],
            'status': 'ok'
        }
        
        for i, line in enumerate(lines):
            # Проверка наличия точек
            if 'start' not in line or 'end' not in line:
                result['errors'].append(f'Линия {i}: отсутствуют начальная или конечная точка')
                result['status'] = 'error'
                continue
            
            # Проверка типа линии
            line_type = line.get('type', 'straight')
            if line_type not in ['straight', 'curve']:
                result['warnings'].append(f'Линия {i}: неизвестный тип "{line_type}"')
        
        return result
    
    def _validate_connectivity(self, points: List[Dict[str, Any]], lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация связности точек и линий"""
        result = {
            'warnings': [],
            'errors': [],
            'status': 'ok',
            'connected_points': 0,
            'dangling_lines': 0
        }
        
        # Создаем множества всех точек из линий
        line_points = set()
        for line in lines:
            if 'start' in line:
                if isinstance(line['start'], dict):
                    line_points.add(line['start'].get('name', f"start_{len(line_points)}"))
                else:
                    line_points.add(str(line['start']))
            
            if 'end' in line:
                if isinstance(line['end'], dict):
                    line_points.add(line['end'].get('name', f"end_{len(line_points)}"))
                else:
                    line_points.add(str(line['end']))
        
        # Проверяем, все ли точки используются
        point_names = set()
        for point in points:
            if isinstance(point, dict) and 'name' in point:
                point_names.add(point['name'])
            else:
                point_names.add(str(point))
        
        connected_points = point_names.intersection(line_points)
        unused_points = point_names - line_points
        missing_line_points = line_points - point_names
        
        if unused_points:
            result['warnings'].append(f'Неиспользуемые точки: {list(unused_points)}')
        
        if missing_line_points:
            result['warnings'].append(f'Линии ссылаются на несуществующие точки: {list(missing_line_points)}')
        
        result['connected_points'] = len(connected_points)
        result['dangling_lines'] = len(missing_line_points)
        
        if missing_line_points:
            result['status'] = 'warning'
        
        return result
    
    def _check_piece_symmetry(self, back_points: List[Dict[str, Any]], front_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Проверка симметрии деталей"""
        result = {
            'warnings': [],
            'errors': [],
            'status': 'ok'
        }
        
        # Упрощенная проверка - количество точек должно быть сопоставимым
        if abs(len(back_points) - len(front_points)) > 2:
            result['warnings'].append(f'Значительная разница в количестве точек: спинка {len(back_points)}, перед {len(front_points)}')
        
        return result
    
    def _check_piece_matching(self, pieces: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка стыковки деталей"""
        result = {
            'warnings': [],
            'errors': [],
            'status': 'ok'
        }
        
        # Здесь можно добавить логику проверки стыковки деталей
        # Например, проверка совпадения боковых швов
        
        return result
    
    def _assess_sleeve_fit(self, ratio: float) -> str:
        """Оценка посадки рукава"""
        if ratio < 0.28:
            return 'tight_fit'
        elif ratio > 0.35:
            return 'loose_fit'
        else:
            return 'optimal_fit'
    
    def _assess_balance(self, ratio: float) -> str:
        """Оценка баланса"""
        if ratio < 0.95:
            return 'front_short'
        elif ratio > 1.05:
            return 'front_long'
        else:
            return 'balanced'
    
    def validate_pattern_with_dataset(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация паттерна с использованием датасета
        
        Args:
            pattern: Паттерн для валидации
            
        Returns:
            Результат валидации с сравнением с датасетом
        """
        result = {
            'standard_validation': {},
            'dataset_validation': {},
            'overall_score': 0,
            'recommendations': [],
            'status': 'ok'
        }
        
        # 1. Стандартная валидация
        try:
            standard_result = self.validate_pattern(pattern)
            result['standard_validation'] = standard_result
        except Exception as e:
            logging.warning(f"Standard validation failed: {e}")
            result['standard_validation'] = {'status': 'error', 'errors': [str(e)]}
        
        # 2. Валидация с датасетом (если доступен)
        if self.dataset_integration:
            try:
                # Получаем тип одежды
                clothing_type = pattern.get('pattern_type', 'unknown')
                
                # Ищем похожие паттерны в датасете
                similar_patterns = self.dataset_integration.search_similar_patterns(pattern, top_k=3)
                
                if similar_patterns:
                    best_reference, similarity_score = similar_patterns[0]
                    
                    # Валидация против лучшего эталона
                    validation_result = self.dataset_integration.validate_generated_pattern(
                        pattern, best_reference
                    )
                    
                    result['dataset_validation'] = {
                        'reference_found': True,
                        'similarity_score': similarity_score,
                        'validation_score': validation_result.score,
                        'point_rmse': validation_result.point_rmse,
                        'symmetry_score': validation_result.symmetry_score,
                        'recommendations': validation_result.recommendations
                    }
                    
                    # Общая оценка (70% стандартная, 30% датасет)
                    standard_score = self._calculate_standard_score(standard_result)
                    dataset_score = validation_result.score
                    result['overall_score'] = (standard_score * 0.7 + dataset_score * 0.3)
                    
                    result['recommendations'].extend(validation_result.recommendations)
                else:
                    result['dataset_validation'] = {
                        'reference_found': False,
                        'message': 'No similar patterns found in dataset'
                    }
                    result['overall_score'] = self._calculate_standard_score(standard_result)
                    
            except Exception as e:
                logging.warning(f"Dataset validation failed: {e}")
                result['dataset_validation'] = {'status': 'error', 'error': str(e)}
                result['overall_score'] = self._calculate_standard_score(standard_result)
        else:
            result['dataset_validation'] = {
                'message': 'Dataset integration not available'
            }
            result['overall_score'] = self._calculate_standard_score(standard_result)
        
        # Определение статуса
        if result['overall_score'] < 50:
            result['status'] = 'error'
        elif result['overall_score'] < 70:
            result['status'] = 'warning'
        
        return result
    
    def _calculate_standard_score(self, validation_result: Dict[str, Any]) -> float:
        """Расчет оценки стандартной валидации"""
        if validation_result.get('status') == 'error':
            return 0.0
        elif validation_result.get('status') == 'warning':
            return 60.0
        else:
            return 85.0


# Удобные функции для быстрого использования
def check_armhole_vs_sleeve(armhole_length: float, sleeve_cap_length: float) -> Dict[str, Any]:
    """Удобная функция для проверки проймы и оката"""
    analyzer = FitAnalyzer()
    return analyzer.check_armhole_vs_sleeve(armhole_length, sleeve_cap_length)


def check_balance(front_length: float, back_length: float) -> Dict[str, Any]:
    """Удобная функция для проверки баланса"""
    analyzer = FitAnalyzer()
    return analyzer.check_balance(front_length, back_length)


def check_shoulder_slope(height: float, chest: float) -> Dict[str, Any]:
    """Удобная функция для проверки наклона плеча"""
    analyzer = FitAnalyzer()
    return analyzer.check_shoulder_slope(height, chest)


def validate_pattern(pieces: Dict[str, Any], use_dataset: bool = False) -> Dict[str, Any]:
    """Удобная функция для валидации паттерна"""
    analyzer = FitAnalyzer(use_dataset=use_dataset)
    
    if use_dataset and analyzer.dataset_integration:
        return analyzer.validate_pattern_with_dataset(pieces)
    else:
        return analyzer.validate_pattern(pieces)


def validate_pattern_with_dataset(pattern: Dict[str, Any]) -> Dict[str, Any]:
    """Удобная функция для валидации паттерна с датасетом"""
    analyzer = FitAnalyzer(use_dataset=True)
    return analyzer.validate_pattern_with_dataset(pattern)


def check_pattern_symmetry(pattern: Dict[str, Any]) -> Dict[str, Any]:
    """Проверка симметрии паттерна"""
    analyzer = FitAnalyzer()
    return analyzer.check_pattern_symmetry(pattern)
