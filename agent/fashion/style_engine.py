"""
Fashion Style Engine Module

Модуль для применения стилей к лекалам
"""

from typing import Dict, Any, List, Tuple
import math


class StyleEngine:
    """Движок стилизации лекал"""
    
    def __init__(self):
        """Инициализация движка стилизации"""
        # Определения стилей
        self.styles = {
            'classic': {
                'name': 'Классический',
                'description': 'Стандартный крой без изменений',
                'chest_adjustment': 0,
                'waist_adjustment': 0,
                'armhole_adjustment': 0,
                'shoulder_adjustment': 0,
                'length_adjustment': 0
            },
            'slim': {
                'name': 'Слим',
                'description': 'Облегающий крой',
                'chest_adjustment': -5.0,  # -4–6 см по груди
                'waist_adjustment': -3.0,   # Уменьшение талии
                'armhole_adjustment': -2.0, # Уменьшение проймы
                'shoulder_adjustment': -1.5, # Уменьшение плеча
                'length_adjustment': -1.0   # Небольшое укорочение
            },
            'oversize': {
                'name': 'Оверсайз',
                'description': 'Свободный крой',
                'chest_adjustment': 8.0,   # +6–12 см по груди
                'waist_adjustment': 6.0,    # Увеличение талии
                'armhole_adjustment': 3.0,  # Увеличение проймы
                'shoulder_adjustment': 2.0, # Увеличение плеча
                'length_adjustment': 2.0    # Удлинение
            }
        }
        
        # Параметры для разных типов одежды
        self.garment_modifiers = {
            'shirt': {
                'chest_multiplier': 1.0,
                'waist_multiplier': 0.8,
                'armhole_multiplier': 1.0,
                'shoulder_multiplier': 1.0
            },
            'dress': {
                'chest_multiplier': 1.0,
                'waist_multiplier': 0.7,
                'armhole_multiplier': 1.0,
                'shoulder_multiplier': 1.0
            },
            'jacket': {
                'chest_multiplier': 1.1,  # Дополнительное пространство
                'waist_multiplier': 0.9,
                'armhole_multiplier': 1.2,
                'shoulder_multiplier': 1.1
            }
        }
    
    def apply_style(self, pattern: Dict[str, Any], style_name: str, 
                   garment_type: str = 'shirt') -> Dict[str, Any]:
        """
        Применение стиля к лекалам
        
        Args:
            pattern: Исходные лекала
            style_name: Название стиля (slim, classic, oversize)
            garment_type: Тип одежды
            
        Returns:
            Скорректированные лекала
        """
        try:
            # Проверяем наличие стиля
            if style_name not in self.styles:
                raise ValueError(f"Неизвестный стиль: {style_name}")
            
            # Получаем параметры стиля
            style_params = self.styles[style_name]
            garment_mods = self.garment_modifiers.get(garment_type, self.garment_modifiers['shirt'])
            
            # Создаем копию лекал
            styled_pattern = {
                'name': pattern.get('name', 'Unknown'),
                'description': f"{pattern.get('description', '')} - {style_params['name']}",
                'original_pattern': pattern.copy(),
                'style_applied': style_name,
                'style_params': style_params.copy(),
                'pieces': {}
            }
            
            # Применяем стиль к каждой детали
            original_pieces = pattern.get('pieces', {})
            for piece_name, piece_data in original_pieces.items():
                styled_piece = self._apply_style_to_piece(
                    piece_data, style_params, garment_mods
                )
                styled_pattern['pieces'][piece_name] = styled_piece
            
            # Добавляем информацию о стиле
            styled_pattern['style_info'] = {
                'applied_style': style_name,
                'garment_type': garment_type,
                'adjustments': style_params,
                'fit_analysis': self._analyze_style_fit(style_params, garment_type)
            }
            
            return styled_pattern
            
        except Exception as e:
            raise ValueError(f"Ошибка при применении стиля: {str(e)}")
    
    def _apply_style_to_piece(self, piece: Dict[str, Any], 
                            style_params: Dict[str, Any],
                            garment_mods: Dict[str, float]) -> Dict[str, Any]:
        """Применение стиля к отдельной детали"""
        styled_piece = {
            'name': piece.get('name', 'Unknown'),
            'description': piece.get('description', ''),
            'original_piece': piece.copy(),
            'points': {},
            'lines': {}
        }
        
        # Получаем исходные точки и линии
        original_points = piece.get('points', {})
        original_lines = piece.get('lines', {})
        
        # Применяем корректировки к точкам
        styled_points = self._adjust_points(original_points, style_params, garment_mods)
        styled_piece['points'] = styled_points
        
        # Копируем линии (они ссылаются на скорректированные точки)
        styled_piece['lines'] = original_lines.copy()
        
        # Добавляем информацию о корректировках
        styled_piece['adjustments_applied'] = {
            'chest_adjustment': style_params['chest_adjustment'] * garment_mods['chest_multiplier'],
            'waist_adjustment': style_params['waist_adjustment'] * garment_mods['waist_multiplier'],
            'armhole_adjustment': style_params['armhole_adjustment'] * garment_mods['armhole_multiplier'],
            'shoulder_adjustment': style_params['shoulder_adjustment'] * garment_mods['shoulder_multiplier']
        }
        
        return styled_piece
    
    def _adjust_points(self, points: Dict[str, Any], 
                      style_params: Dict[str, Any],
                      garment_mods: Dict[str, float]) -> Dict[str, Any]:
        """Корректировка точек согласно стилю"""
        adjusted_points = {}
        
        for point_name, point_data in points.items():
            # Копируем исходную точку
            adjusted_point = point_data.copy()
            
            # Получаем координаты
            x = float(point_data.get('x', 0))
            y = float(point_data.get('y', 0))
            
            # Определяем тип точки для корректировки
            point_type = self._classify_point(point_name, x, y)
            
            # Применяем корректировки в зависимости от типа точки
            if point_type == 'chest':
                x += style_params['chest_adjustment'] * garment_mods['chest_multiplier']
            elif point_type == 'waist':
                x += style_params['waist_adjustment'] * garment_mods['waist_multiplier']
            elif point_type == 'shoulder':
                x += style_params['shoulder_adjustment'] * garment_mods['shoulder_multiplier']
            elif point_type == 'armhole':
                # Для проймы корректируем и x, и y
                x += style_params['armhole_adjustment'] * garment_mods['armhole_multiplier']
                y += style_params['armhole_adjustment'] * garment_mods['armhole_multiplier'] * 0.5
            elif point_type == 'length':
                y += style_params['length_adjustment']
            
            # Обновляем координаты
            adjusted_point['x'] = x
            adjusted_point['y'] = y
            adjusted_point['original_x'] = point_data.get('x', 0)
            adjusted_point['original_y'] = point_data.get('y', 0)
            
            adjusted_points[point_name] = adjusted_point
        
        return adjusted_points
    
    def _classify_point(self, point_name: str, x: float, y: float) -> str:
        """Классификация точки для определения типа корректировки"""
        # Анализируем название точки
        name_lower = point_name.lower()
        
        if 'chest' in name_lower or 'bust' in name_lower:
            return 'chest'
        elif 'waist' in name_lower:
            return 'waist'
        elif 'shoulder' in name_lower or 'shldr' in name_lower:
            return 'shoulder'
        elif 'armhole' in name_lower or 'arm' in name_lower:
            return 'armhole'
        elif 'neck' in name_lower or 'collar' in name_lower:
            return 'neck'
        elif 'hem' in name_lower or 'bottom' in name_lower:
            return 'length'
        
        # Анализируем положение точки
        if y < 10:  # Верхняя часть
            if abs(x) > 15:
                return 'shoulder'
            else:
                return 'neck'
        elif 10 <= y <= 40:  # Средняя часть
            if abs(x) > 20:
                return 'chest'
            else:
                return 'waist'
        elif y > 40:  # Нижняя часть
            return 'length'
        
        return 'general'
    
    def _analyze_style_fit(self, style_params: Dict[str, Any], 
                          garment_type: str) -> Dict[str, Any]:
        """Анализ посадки стиля"""
        analysis = {
            'fit_type': 'unknown',
            'comfort_level': 'medium',
            'recommendations': [],
            'potential_issues': []
        }
        
        # Определяем тип посадки
        if style_params['chest_adjustment'] < -3:
            analysis['fit_type'] = 'tight'
            analysis['comfort_level'] = 'low'
            analysis['recommendations'].append('Использовать эластичные ткани')
            analysis['potential_issues'].append('Может быть тесно в движении')
        elif style_params['chest_adjustment'] > 5:
            analysis['fit_type'] = 'loose'
            analysis['comfort_level'] = 'high'
            analysis['recommendations'].append('Подходит для свободного силуэта')
        else:
            analysis['fit_type'] = 'regular'
            analysis['comfort_level'] = 'medium'
            analysis['recommendations'].append('Универсальный вариант')
        
        # Анализируем совместимость с типом одежды
        if garment_type == 'jacket' and style_params['chest_adjustment'] < -2:
            analysis['potential_issues'].append('Пиджак должен иметь больше свободы')
        elif garment_type == 'shirt' and style_params['chest_adjustment'] > 8:
            analysis['potential_issues'].append('Слишком свободно для рубашки')
        
        return analysis
    
    def get_available_styles(self) -> Dict[str, Dict[str, Any]]:
        """Получение доступных стилей"""
        return self.styles.copy()
    
    def preview_style_changes(self, pattern: Dict[str, Any], 
                             style_name: str,
                             garment_type: str = 'shirt') -> Dict[str, Any]:
        """Предпросмотр изменений стиля без применения"""
        if style_name not in self.styles:
            return {'error': f'Неизвестный стиль: {style_name}'}
        
        style_params = self.styles[style_name]
        garment_mods = self.garment_modifiers.get(garment_type, self.garment_modifiers['shirt'])
        
        preview = {
            'style_name': style_name,
            'style_description': style_params['description'],
            'adjustments': {},
            'affected_points': [],
            'estimated_fit': self._analyze_style_fit(style_params, garment_type)
        }
        
        # Рассчитываем корректировки
        preview['adjustments'] = {
            'chest': style_params['chest_adjustment'] * garment_mods['chest_multiplier'],
            'waist': style_params['waist_adjustment'] * garment_mods['waist_multiplier'],
            'armhole': style_params['armhole_adjustment'] * garment_mods['armhole_multiplier'],
            'shoulder': style_params['shoulder_adjustment'] * garment_mods['shoulder_multiplier'],
            'length': style_params['length_adjustment']
        }
        
        # Определяем затронутые точки
        pieces = pattern.get('pieces', {})
        for piece_name, piece_data in pieces.items():
            points = piece_data.get('points', {})
            for point_name, point_data in points.items():
                point_type = self._classify_point(
                    point_name, 
                    float(point_data.get('x', 0)), 
                    float(point_data.get('y', 0))
                )
                if point_type != 'general':
                    preview['affected_points'].append({
                        'piece': piece_name,
                        'point': point_name,
                        'type': point_type,
                        'current_coords': (point_data.get('x', 0), point_data.get('y', 0))
                    })
        
        return preview
    
    def combine_styles(self, base_style: str, modifier_style: str, 
                      modifier_strength: float = 0.5) -> Dict[str, Any]:
        """
        Комбинирование стилей
        
        Args:
            base_style: Базовый стиль
            modifier_style: Модифицирующий стиль
            modifier_strength: Сила модификатора (0-1)
            
        Returns:
            Комбинированный стиль
        """
        if base_style not in self.styles or modifier_style not in self.styles:
            raise ValueError("Один из стилей не найден")
        
        base = self.styles[base_style]
        modifier = self.styles[modifier_style]
        
        combined = {
            'name': f"{base['name']} + {modifier['name']}",
            'description': f"Комбинация {base['name']} с элементами {modifier['name']}",
            'base_style': base_style,
            'modifier_style': modifier_style,
            'modifier_strength': modifier_strength
        }
        
        # Комбинируем параметры
        for param in ['chest_adjustment', 'waist_adjustment', 'armhole_adjustment', 
                     'shoulder_adjustment', 'length_adjustment']:
            base_value = base.get(param, 0)
            modifier_value = modifier.get(param, 0)
            combined[param] = base_value + (modifier_value - base_value) * modifier_strength
        
        return combined


# Удобные функции для быстрого использования
def apply_style(pattern: Dict[str, Any], style_name: str, 
               garment_type: str = 'shirt') -> Dict[str, Any]:
    """
    Удобная функция для применения стиля
    
    Args:
        pattern: Лекала
        style_name: Название стиля
        garment_type: Тип одежды
        
    Returns:
        Стилизованные лекала
    """
    style_engine = StyleEngine()
    return style_engine.apply_style(pattern, style_name, garment_type)


def get_style_preview(pattern: Dict[str, Any], style_name: str,
                    garment_type: str = 'shirt') -> Dict[str, Any]:
    """
    Удобная функция для предпросмотра стиля
    
    Args:
        pattern: Лекала
        style_name: Название стиля
        garment_type: Тип одежды
        
    Returns:
        Предпросмотр изменений
    """
    style_engine = StyleEngine()
    return style_engine.preview_style_changes(pattern, style_name, garment_type)
