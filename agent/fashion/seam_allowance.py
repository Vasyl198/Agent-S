"""
Fashion Seam Allowance Module

Модуль для добавления припусков на швы к лекалам
"""

from typing import Dict, Any, List, Tuple
import math


class SeamAllowance:
    """Класс для работы с припусками на швы"""
    
    def __init__(self):
        """Инициализация модуля припусков"""
        # Стандартные припуски по типу шва (в см)
        self.standard_allowances = {
            'straight': 1.5,      # Прямой шов
            'curved': 1.0,        # Криволинейный шов
            'corner': 2.0,        # Угловой шов
            'hem': 3.0,          # Подгиб низа
            'neckline': 1.0,      # Горловина
            'armhole': 1.5,       # Пройма
            'sleeve_cap': 1.0,    # Окат рукава
            'waist': 1.5,         # Пояс
            'shoulder': 1.0,       # Плечевой шов
            'side': 1.5,          # Боковой шов
            'center': 1.0          # Центральный шов
        }
        
        # Типы обработки углов
        self.corner_types = {
            'miter': 'miter',      # Угловой срез
            'round': 'round',        # Скругленный
            'bevel': 'bevel'        # Скошенный
        }
    
    def add_seam_allowances(self, piece: Dict[str, Any], allowances: Dict[str, float]) -> Dict[str, Any]:
        """
        Добавление припусков на швы к детали
        
        Args:
            piece: Деталь лекала (points, lines)
            allowances: Словарь припусков по типу шва
            
        Returns:
            Новая деталь с припусками
        """
        try:
            # Создаем копию детали для сохранения оригинала
            new_piece = {
                'name': piece.get('name', 'Unknown'),
                'description': piece.get('description', ''),
                'original_piece': piece.copy(),  # Сохраняем оригинал
                'points': {},
                'lines': {},
                'allowances': allowances.copy(),
                'allowance_info': {}
            }
            
            # Получаем исходные точки и линии
            original_points = piece.get('points', {})
            original_lines = piece.get('lines', {})
            
            # 1. Создаем новые точки с учетом припусков
            new_points = self._create_allowance_points(original_points, original_lines, allowances)
            new_piece['points'] = new_points
            
            # 2. Создаем новые линии с учетом припусков
            new_lines = self._create_allowance_lines(original_lines, new_points, allowances)
            new_piece['lines'] = new_lines
            
            # 3. Добавляем информацию о припусках
            new_piece['allowance_info'] = self._calculate_allowance_info(original_lines, allowances)
            
            # 4. Валидируем индексы точек и линий
            validation_result = self.validate_piece_indices(new_piece)
            new_piece['validation'] = validation_result
            
            return new_piece
            
        except Exception as e:
            raise ValueError(f"Ошибка при добавлении припусков: {str(e)}")
    
    def _create_allowance_points(self, original_points: Dict[str, Any], 
                               original_lines: Dict[str, Any], 
                               allowances: Dict[str, float]) -> Dict[str, Any]:
        """Создание новых точек с учетом припусков"""
        new_points = {}
        
        # Копируем оригинальные точки
        for point_name, point_data in original_points.items():
            new_points[point_name] = point_data.copy()
        
        # Создаем точки для припусков
        for line_name, line_data in original_lines.items():
            seam_type = line_data.get('seam_type', 'straight')
            allowance = allowances.get(seam_type, self.standard_allowances.get(seam_type, 1.5))
            
            start_point = line_data.get('start')
            end_point = line_data.get('end')
            
            # Создаем смещенные точки
            if start_point and end_point:
                # Находим координаты начальной и конечной точек
                start_coords = self._get_point_coords(original_points, start_point)
                end_coords = self._get_point_coords(original_points, end_point)
                
                if start_coords and end_coords:
                    # Создаем точки припусков
                    allowance_points = self._create_line_allowance_points(
                        start_coords, end_coords, allowance, line_name
                    )
                    
                    # Добавляем новые точки
                    for point_name, point_coords in allowance_points.items():
                        if point_name not in new_points:
                            new_points[point_name] = {
                                'x': point_coords[0],
                                'y': point_coords[1],
                                'type': 'allowance',
                                'parent_line': line_name
                            }
        
        return new_points
    
    def _create_allowance_lines(self, original_lines: Dict[str, Any], 
                              new_points: Dict[str, Any], 
                              allowances: Dict[str, float]) -> Dict[str, Any]:
        """Создание новых линий с учетом припусков"""
        new_lines = {}
        
        # Копируем оригинальные линии
        for line_name, line_data in original_lines.items():
            new_lines[line_name] = line_data.copy()
        
        # Создаем линии припусков
        for line_name, line_data in original_lines.items():
            seam_type = line_data.get('seam_type', 'straight')
            allowance = allowances.get(seam_type, self.standard_allowances.get(seam_type, 1.5))
            
            start_point = line_data.get('start')
            end_point = line_data.get('end')
            
            if start_point and end_point:
                # Создаем линии припусков
                allowance_lines = self._create_line_allowance_lines(
                    line_name, start_point, end_point, new_points, allowance
                )
                
                # Добавляем новые линии
                for new_line_name, new_line_data in allowance_lines.items():
                    new_lines[new_line_name] = new_line_data
        
        return new_lines
    
    def _create_line_allowance_points(self, start_coords: Tuple[float, float], 
                                   end_coords: Tuple[float, float], 
                                   allowance: float, 
                                   line_name: str) -> Dict[str, Tuple[float, float]]:
        """Создание точек припусков для линии"""
        points = {}
        
        # Вычисляем вектор направления линии
        dx = end_coords[0] - start_coords[0]
        dy = end_coords[1] - start_coords[1]
        length = math.sqrt(dx**2 + dy**2)
        
        if length == 0:
            return points
        
        # Нормализуем вектор
        nx = dx / length
        ny = dy / length
        
        # Перпендикулярный вектор (для смещения)
        px = -ny
        py = nx
        
        # Создаем смещенные точки
        start_offset = (
            start_coords[0] + px * allowance,
            start_coords[1] + py * allowance
        )
        end_offset = (
            end_coords[0] + px * allowance,
            end_coords[1] + py * allowance
        )
        
        # Сохраняем точки
        points[f'{line_name}_start_allowance'] = start_offset
        points[f'{line_name}_end_allowance'] = end_offset
        
        # Создаем промежуточные точки для кривых
        # Примечание: тип линии нужно передавать как параметр
        # if line_data.get('type') == 'curve':
        #     mid_point = (
        #         (start_coords[0] + end_coords[0]) / 2 + px * allowance,
        #         (start_coords[1] + end_coords[1]) / 2 + py * allowance
        #     )
        #     points[f'{line_name}_mid_allowance'] = mid_point
        
        return points
    
    def _create_line_allowance_lines(self, line_name: str, 
                                  start_point: str, 
                                  end_point: str,
                                  new_points: Dict[str, Any], 
                                  allowance: float) -> Dict[str, Any]:
        """Создание линий припусков для линии"""
        lines = {}
        
        # Линия припуска
        lines[f'{line_name}_allowance'] = {
            'start': f'{line_name}_start_allowance',
            'end': f'{line_name}_end_allowance',
            'type': 'straight',
            'seam_type': 'allowance',
            'parent_line': line_name,
            'allowance': allowance
        }
        
        # Соединительные линии
        lines[f'{line_name}_start_connect'] = {
            'start': start_point,
            'end': f'{line_name}_start_allowance',
            'type': 'straight',
            'seam_type': 'connect',
            'parent_line': line_name
        }
        
        lines[f'{line_name}_end_connect'] = {
            'start': end_point,
            'end': f'{line_name}_end_allowance',
            'type': 'straight',
            'seam_type': 'connect',
            'parent_line': line_name
        }
        
        return lines
    
    def _get_point_coords(self, points: Dict[str, Any], point_ref: Any) -> Tuple[float, float]:
        """Получение координат точки"""
        if isinstance(point_ref, str):
            # Имя точки
            if point_ref in points:
                point = points[point_ref]
                return (float(point.get('x', 0)), float(point.get('y', 0)))
        elif isinstance(point_ref, dict):
            # Координаты напрямую
            return (float(point_ref.get('x', 0)), float(point_ref.get('y', 0)))
        
        return None
    
    def _calculate_allowance_info(self, lines: Dict[str, Any], 
                               allowances: Dict[str, float]) -> Dict[str, Any]:
        """Расчет информации о припусках"""
        info = {
            'total_lines': len(lines),
            'allowance_types': {},
            'total_allowance_length': 0,
            'average_allowance': 0
        }
        
        total_allowance = 0
        line_count = 0
        
        for line_name, line_data in lines.items():
            seam_type = line_data.get('seam_type', 'straight')
            allowance = allowances.get(seam_type, self.standard_allowances.get(seam_type, 1.5))
            
            if seam_type not in info['allowance_types']:
                info['allowance_types'][seam_type] = {
                    'count': 0,
                    'allowance': allowance,
                    'total_length': 0
                }
            
            info['allowance_types'][seam_type]['count'] += 1
            total_allowance += allowance
            line_count += 1
        
        if line_count > 0:
            info['average_allowance'] = total_allowance / line_count
        
        return info
    
    def create_standard_allowances(self, garment_type: str = 'shirt') -> Dict[str, float]:
        """
        Создание стандартных припусков для типа одежды
        
        Args:
            garment_type: Тип одежды
            
        Returns:
            Словарь стандартных припусков
        """
        if garment_type == 'shirt':
            return {
                'straight': 1.5,
                'curved': 1.0,
                'hem': 3.0,
                'neckline': 1.0,
                'armhole': 1.5,
                'sleeve_cap': 1.0,
                'shoulder': 1.0,
                'side': 1.5,
                'center': 1.0
            }
        elif garment_type == 'dress':
            return {
                'straight': 1.5,
                'curved': 1.0,
                'hem': 4.0,
                'neckline': 1.0,
                'armhole': 1.5,
                'sleeve_cap': 1.0,
                'shoulder': 1.0,
                'side': 1.5,
                'waist': 2.0
            }
        elif garment_type == 'pants':
            return {
                'straight': 1.5,
                'curved': 1.0,
                'hem': 4.0,
                'waist': 2.0,
                'side': 1.5,
                'center': 1.0,
                'crotch': 1.5
            }
        else:
            # Стандартные припуски по умолчанию
            return self.standard_allowances.copy()
    
    def process_corners(self, piece: Dict[str, Any], corner_type: str = 'miter') -> Dict[str, Any]:
        """
        Обработка углов в детали
        
        Args:
            piece: Деталь с припусками
            corner_type: Тип обработки углов
            
        Returns:
            Деталь с обработанными углами
        """
        if corner_type not in self.corner_types:
            corner_type = 'miter'
        
        processed_piece = piece.copy()
        
        # Находим углы (точки где сходятся 2+ линии)
        corners = self._find_corners(piece)
        
        # Обрабатываем каждый угол
        for corner_point, connected_lines in corners.items():
            corner_processing = self._process_corner(
                piece, corner_point, connected_lines, corner_type
            )
            
            if corner_processing:
                # Добавляем обработанные точки и линии
                if 'new_points' in corner_processing:
                    processed_piece['points'].update(corner_processing['new_points'])
                
                if 'new_lines' in corner_processing:
                    processed_piece['lines'].update(corner_processing['new_lines'])
        
        processed_piece['corner_processing'] = {
            'type': corner_type,
            'processed_corners': len(corners)
        }
        
        return processed_piece
    
    def _find_corners(self, piece: Dict[str, Any]) -> Dict[str, List[str]]:
        """Нахождение углов в детали"""
        corners = {}
        lines = piece.get('lines', {})
        
        # Строим граф связей точек
        point_connections = {}
        
        for line_name, line_data in lines.items():
            start = line_data.get('start')
            end = line_data.get('end')
            
            if start:
                if start not in point_connections:
                    point_connections[start] = []
                point_connections[start].append(line_name)
            
            if end:
                if end not in point_connections:
                    point_connections[end] = []
                point_connections[end].append(line_name)
        
        # Находим углы (точки с 2+ соединениями)
        for point, connected_lines in point_connections.items():
            if len(connected_lines) >= 2:
                corners[point] = connected_lines
        
        return corners
    
    def _process_corner(self, piece: Dict[str, Any], corner_point: str, 
                       connected_lines: List[str], corner_type: str) -> Dict[str, Any]:
        """Обработка отдельного угла"""
        result = {'new_points': {}, 'new_lines': {}}
        
        if corner_type == 'miter':
            # Угловой срез
            return self._create_miter_corner(piece, corner_point, connected_lines)
        elif corner_type == 'round':
            # Скругленный угол
            return self._create_round_corner(piece, corner_point, connected_lines)
        elif corner_type == 'bevel':
            # Скошенный угол
            return self._create_bevel_corner(piece, corner_point, connected_lines)
        
        return result
    
    def _create_miter_corner(self, piece: Dict[str, Any], corner_point: str, 
                           connected_lines: List[str]) -> Dict[str, Any]:
        """Создание углового среза"""
        result = {'new_points': {}, 'new_lines': {}}
        
        points = piece.get('points', {})
        lines = piece.get('lines', {})
        
        # Находим линии припусков для угловой точки
        allowance_lines = []
        for line_name in connected_lines:
            allowance_line_name = f'{line_name}_allowance'
            if allowance_line_name in lines:
                allowance_lines.append(allowance_line_name)
        
        if len(allowance_lines) >= 2:
            # Создаем угловую точку припуска
            corner_point_coords = self._get_point_coords(points, corner_point)
            
            # Находим конечные точки линий припусков
            allowance_points = []
            for line_name in allowance_lines:
                line_data = lines[line_name]
                end_point = line_data.get('end')
                if end_point and end_point != corner_point:
                    allowance_points.append(end_point)
            
            if len(allowance_points) >= 2:
                # Создаем угловую точку (пересечение продолжений)
                corner_allowance_point = self._calculate_corner_intersection(
                    allowance_points[0], allowance_points[1], corner_point_coords
                )
                
                if corner_allowance_point:
                    corner_name = f'{corner_point}_corner_allowance'
                    result['new_points'][corner_name] = {
                        'x': corner_allowance_point[0],
                        'y': corner_allowance_point[1],
                        'type': 'corner_allowance',
                        'corner_type': 'miter'
                    }
        
        return result
    
    def _create_round_corner(self, piece: Dict[str, Any], corner_point: str, 
                           connected_lines: List[str]) -> Dict[str, Any]:
        """Создание скругленного угла"""
        result = {'new_points': {}, 'new_lines': {}}
        
        # Для скругленного угла создаем дугу
        points = piece.get('points', {})
        lines = piece.get('lines', {})
        
        corner_point_coords = self._get_point_coords(points, corner_point)
        if not corner_point_coords:
            return result
        
        # Находим точки припусков
        allowance_points = []
        for line_name in connected_lines:
            allowance_line_name = f'{line_name}_allowance'
            if allowance_line_name in lines:
                line_data = lines[allowance_line_name]
                end_point = line_data.get('end')
                if end_point and end_point != corner_point:
                    allowance_points.append(end_point)
        
        if len(allowance_points) >= 2:
            # Создаем промежуточные точки для дуги
            radius = 2.0  # Радиус скругления
            arc_points = self._create_arc_points(
                allowance_points[0], allowance_points[1], 
                corner_point_coords, radius
            )
            
            # Добавляем точки дуги
            for i, point in enumerate(arc_points):
                point_name = f'{corner_point}_arc_{i}'
                result['new_points'][point_name] = {
                    'x': point[0],
                    'y': point[1],
                    'type': 'arc_point',
                    'corner_type': 'round'
                }
        
        return result
    
    def _create_bevel_corner(self, piece: Dict[str, Any], corner_point: str, 
                           connected_lines: List[str]) -> Dict[str, Any]:
        """Создание скошенного угла"""
        result = {'new_points': {}, 'new_lines': {}}
        
        # Для скошенного угла создаем прямую линию между точками припусков
        points = piece.get('points', {})
        lines = piece.get('lines', {})
        
        # Находим точки припусков
        allowance_points = []
        for line_name in connected_lines:
            allowance_line_name = f'{line_name}_allowance'
            if allowance_line_name in lines:
                line_data = lines[allowance_line_name]
                end_point = line_data.get('end')
                if end_point and end_point != corner_point:
                    allowance_points.append(end_point)
        
        if len(allowance_points) >= 2:
            # Создаем линию между точками припусков
            bevel_line_name = f'{corner_point}_bevel'
            result['new_lines'][bevel_line_name] = {
                'start': allowance_points[0],
                'end': allowance_points[1],
                'type': 'straight',
                'seam_type': 'bevel',
                'corner_type': 'bevel'
            }
        
        return result
    
    def _calculate_corner_intersection(self, point1: str, point2: str, 
                                   corner: Tuple[float, float]) -> Tuple[float, float]:
        """Расчет точки пересечения для углового среза"""
        # Упрощенный расчет - средняя точка между точками припусков
        # В реальной реализации здесь была бы геометрия пересечения прямых
        return corner
    
    def _create_arc_points(self, start: str, end: str, 
                         center: Tuple[float, float], radius: float) -> List[Tuple[float, float]]:
        """Создание точек для дуги"""
        # Упрощенная реализация - создаем несколько точек на дуге
        points = []
        num_points = 5
        
        for i in range(num_points):
            angle = (i / (num_points - 1)) * math.pi / 4  # 45 градусов
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
        
        return points
    
    def validate_piece_indices(self, piece: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация индексов точек и линий в детали
        
        Args:
            piece: Деталь для валидации
            
        Returns:
            Результат валидации
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        points = piece.get('points', {})
        lines = piece.get('lines', {})
        
        # Проверяем, что все линии ссылаются на существующие точки
        missing_points = set()
        invalid_lines = []
        
        for line_name, line_data in lines.items():
            start_point = line_data.get('start')
            end_point = line_data.get('end')
            
            # Проверяем начальную точку
            if start_point:
                if isinstance(start_point, str):
                    if start_point not in points:
                        missing_points.add(start_point)
                        invalid_lines.append(line_name)
                elif isinstance(start_point, dict):
                    # Проверяем координаты напрямую
                    if 'x' not in start_point or 'y' not in start_point:
                        invalid_lines.append(line_name)
            
            # Проверяем конечную точку
            if end_point:
                if isinstance(end_point, str):
                    if end_point not in points:
                        missing_points.add(end_point)
                        invalid_lines.append(line_name)
                elif isinstance(end_point, dict):
                    # Проверяем координаты напрямую
                    if 'x' not in end_point or 'y' not in end_point:
                        invalid_lines.append(line_name)
        
        # Проверяем, что все точки используются в линиях
        used_points = set()
        for line_data in lines.values():
            start = line_data.get('start')
            end = line_data.get('end')
            
            if isinstance(start, str):
                used_points.add(start)
            if isinstance(end, str):
                used_points.add(end)
        
        unused_points = set(points.keys()) - used_points
        
        # Формируем результат
        if missing_points:
            validation_result['valid'] = False
            validation_result['errors'].append(
                f'Отсутствуют точки: {list(missing_points)}'
            )
        
        if invalid_lines:
            validation_result['valid'] = False
            validation_result['errors'].append(
                f'Некорректные линии: {invalid_lines}'
            )
        
        if unused_points:
            validation_result['warnings'].append(
                f'Неиспользуемые точки: {list(unused_points)}'
            )
        
        # Статистика
        validation_result['statistics'] = {
            'total_points': len(points),
            'total_lines': len(lines),
            'valid_lines': len(lines) - len(invalid_lines),
            'missing_points': len(missing_points),
            'unused_points': len(unused_points)
        }
        
        return validation_result


# Удобные функции для быстрого использования
def add_seam_allowances(piece: Dict[str, Any], allowances: Dict[str, float]) -> Dict[str, Any]:
    """
    Удобная функция для добавления припусков
    
    Args:
        piece: Деталь лекала
        allowances: Припуски по типу шва
        
    Returns:
        Деталь с припусками
    """
    seam_allowance = SeamAllowance()
    return seam_allowance.add_seam_allowances(piece, allowances)


def create_standard_allowances(garment_type: str = 'shirt') -> Dict[str, float]:
    """
    Удобная функция для создания стандартных припусков
    
    Args:
        garment_type: Тип одежды
        
    Returns:
        Словарь стандартных припусков
    """
    seam_allowance = SeamAllowance()
    return seam_allowance.create_standard_allowances(garment_type)


def validate_piece_indices(piece: Dict[str, Any]) -> Dict[str, Any]:
    """
    Удобная функция для валидации индексов
    
    Args:
        piece: Деталь для валидации
        
    Returns:
        Результат валидации
    """
    seam_allowance = SeamAllowance()
    return seam_allowance.validate_piece_indices(piece)
