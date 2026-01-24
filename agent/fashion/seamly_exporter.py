"""
Seamly Exporter Module

Модуль для экспорта параметрических лекал в формат Seamly (.val)
"""

from typing import Dict, Any, List, Tuple
import json
from pathlib import Path


class SeamlyExporter:
    """Экспортер параметрических лекал в формат Seamly"""
    
    def __init__(self):
        """Инициализация экспортера"""
        # Стандартные формулы для расчетов
        self.formulas = {
            'armhole_depth': 'chest * 0.15 + 2',
            'neckline_width': 'chest * 0.2',
            'shoulder_slope': '2',
            'back_length': 'height * 0.42',
            'front_length': 'height * 0.43',
            'sleeve_cap_height': 'armhole_length / 3',
            'sleeve_width': 'chest * 0.4',
            'sleeve_length': 'height * 0.35'
        }
        
        # Базовые переменные
        self.base_variables = {
            'height': {'value': 170, 'description': 'Рост'},
            'chest': {'value': 100, 'description': 'Обхват груди'},
            'waist': {'value': 80, 'description': 'Обхват талии'},
            'hips': {'value': 105, 'description': 'Обхват бедер'},
            'armhole_length': {'value': 45, 'description': 'Длина проймы'}
        }
    
    def export_pattern_to_seamly(self, 
                               pattern_data: Dict[str, Any], 
                               measurements: Dict[str, float],
                               output_file: str) -> bool:
        """
        Экспорт паттерна в формат Seamly .val
        
        Args:
            pattern_data: Данные паттерна (линии, точки)
            measurements: Мерки тела
            output_file: Имя выходного файла
            
        Returns:
            Успешность экспорта
        """
        try:
            # Создаем структуру Seamly
            seamly_data = {
                "version": "1.0",
                "name": "Parametric Pattern",
                "description": "Параметрическая выкройка",
                "variables": {},
                "calculations": {},
                "pieces": {}
            }
            
            # 1. Добавляем переменные (мерки)
            seamly_data["variables"] = self._create_variables(measurements)
            
            # 2. Добавляем расчеты (формулы)
            seamly_data["calculations"] = self._create_calculations()
            
            # 3. Добавляем детали (перед, спинка, рукав)
            seamly_data["pieces"] = self._create_pieces(pattern_data, measurements)
            
            # Сохраняем в .val файл
            return self._save_val_file(seamly_data, output_file)
            
        except Exception as e:
            print(f"Error exporting to Seamly: {e}")
            return False
    
    def _create_variables(self, measurements: Dict[str, float]) -> Dict[str, Any]:
        """
        Создание переменных для Seamly
        
        Args:
            measurements: Мерки тела
            
        Returns:
            Словарь переменных Seamly
        """
        variables = {}
        
        # Основные мерки
        for name, value in measurements.items():
            variables[name] = {
                "type": "measurement",
                "value": value,
                "description": self._get_measurement_description(name),
                "unit": "cm"
            }
        
        # Дополнительные переменные
        variables['ease_chest'] = {
            "type": "constant",
            "value": 4,
            "description": "Прибавка на груди"
        }
        
        variables['ease_waist'] = {
            "type": "constant", 
            "value": 2,
            "description": "Прибавка на талии"
        }
        
        variables['seam_allowance'] = {
            "type": "constant",
            "value": 1.5,
            "description": "Припуск на шов"
        }
        
        return variables
    
    def _create_calculations(self) -> Dict[str, Any]:
        """
        Создание расчетов (формул) для Seamly
        
        Returns:
            Словарь расчетов Seamly
        """
        calculations = {}
        
        # Основные расчеты
        calculations['chest_with_ease'] = {
            "formula": "chest + ease_chest",
            "description": "Грудь с прибавкой"
        }
        
        calculations['waist_with_ease'] = {
            "formula": "waist + ease_waist", 
            "description": "Талия с прибавкой"
        }
        
        calculations['armhole_depth'] = {
            "formula": "chest * 0.15 + 2",
            "description": "Глубина проймы"
        }
        
        calculations['neckline_width'] = {
            "formula": "chest * 0.2",
            "description": "Ширина горловины"
        }
        
        calculations['back_length'] = {
            "formula": "height * 0.42",
            "description": "Длина спинки"
        }
        
        calculations['front_length'] = {
            "formula": "height * 0.43",
            "description": "Длина переда"
        }
        
        calculations['shoulder_width'] = {
            "formula": "chest_with_ease / 4 + 2",
            "description": "Ширина плеча"
        }
        
        # Расчеты для рукава
        calculations['sleeve_cap_height'] = {
            "formula": "armhole_length / 3",
            "description": "Высота оката рукава"
        }
        
        calculations['sleeve_width'] = {
            "formula": "chest * 0.4",
            "description": "Ширина рукава"
        }
        
        calculations['sleeve_length'] = {
            "formula": "height * 0.35",
            "description": "Длина рукава"
        }
        
        # Расчеты для построения
        calculations['half_back_width'] = {
            "formula": "chest_with_ease / 2",
            "description": "Половина ширины спинки"
        }
        
        calculations['half_front_width'] = {
            "formula": "chest_with_ease / 2",
            "description": "Половина ширины переда"
        }
        
        calculations['neck_depth_back'] = {
            "formula": "chest * 0.04",
            "description": "Глубина горловины спинки"
        }
        
        calculations['neck_depth_front'] = {
            "formula": "chest * 0.1",
            "description": "Глубина горловины переда"
        }
        
        return calculations
    
    def _create_pieces(self, pattern_data: Dict[str, Any], measurements: Dict[str, float]) -> Dict[str, Any]:
        """
        Создание деталей для Seamly
        
        Args:
            pattern_data: Данные паттерна
            measurements: Мерки тела
            
        Returns:
            Словарь деталей Seamly
        """
        pieces = {}
        
        # Деталь 1: Спинка
        pieces['back'] = {
            "name": "Спинка",
            "description": "Зняя часть изделия",
            "points": self._create_back_points(),
            "lines": self._create_back_lines(),
            "constraints": self._create_back_constraints()
        }
        
        # Деталь 2: Перед
        pieces['front'] = {
            "name": "Перед",
            "description": "Передняя часть изделия", 
            "points": self._create_front_points(),
            "lines": self._create_front_lines(),
            "constraints": self._create_front_constraints()
        }
        
        # Деталь 3: Рукав
        pieces['sleeve'] = {
            "name": "Рукав",
            "description": "Втачной рукав",
            "points": self._create_sleeve_points(),
            "lines": self._create_sleeve_lines(),
            "constraints": self._create_sleeve_constraints()
        }
        
        return pieces
    
    def _create_back_points(self) -> List[Dict[str, Any]]:
        """Создание точек для спинки"""
        return [
            {
                "name": "A",
                "x": "0",
                "y": "0", 
                "description": "Верх середины спинки"
            },
            {
                "name": "B",
                "x": "-half_back_width",
                "y": "0",
                "description": "Левый верх спинки"
            },
            {
                "name": "C", 
                "x": "half_back_width",
                "y": "0",
                "description": "Правый верх спинки"
            },
            {
                "name": "D",
                "x": "-half_back_width",
                "y": "back_length * 0.3",
                "description": "Левая точка груди"
            },
            {
                "name": "E",
                "x": "half_back_width", 
                "y": "back_length * 0.3",
                "description": "Правая точка груди"
            },
            {
                "name": "F",
                "x": "0",
                "y": "back_length",
                "description": "Низ середины спинки"
            },
            {
                "name": "G",
                "x": "-half_back_width",
                "y": "back_length",
                "description": "Левый низ спинки"
            },
            {
                "name": "H",
                "x": "half_back_width",
                "y": "back_length", 
                "description": "Правый низ спинки"
            }
        ]
    
    def _create_back_lines(self) -> List[Dict[str, Any]]:
        """Создание линий для спинки"""
        return [
            {
                "name": "top_line",
                "start": "B",
                "end": "C",
                "type": "straight"
            },
            {
                "name": "left_chest_line",
                "start": "B", 
                "end": "D",
                "type": "straight"
            },
            {
                "name": "right_chest_line",
                "start": "C",
                "end": "E",
                "type": "straight"
            },
            {
                "name": "center_back_line",
                "start": "A",
                "end": "F",
                "type": "straight"
            },
            {
                "name": "left_side_line",
                "start": "D",
                "end": "G",
                "type": "straight"
            },
            {
                "name": "right_side_line", 
                "start": "E",
                "end": "H",
                "type": "straight"
            },
            {
                "name": "bottom_line",
                "start": "G",
                "end": "H",
                "type": "straight"
            }
        ]
    
    def _create_back_constraints(self) -> List[Dict[str, Any]]:
        """Создание ограничений для спинки"""
        return [
            {
                "type": "horizontal",
                "points": ["B", "C"],
                "description": "Верхняя линия горизонтальна"
            },
            {
                "type": "vertical", 
                "points": ["A", "F"],
                "description": "Центровая линия вертикальна"
            },
            {
                "type": "parallel",
                "lines": ["top_line", "bottom_line"],
                "description": "Верх и низ параллельны"
            }
        ]
    
    def _create_front_points(self) -> List[Dict[str, Any]]:
        """Создание точек для переда"""
        return [
            {
                "name": "I",
                "x": "half_back_width",
                "y": "0",
                "description": "Левый верх переда"
            },
            {
                "name": "J",
                "x": "half_back_width * 2",
                "y": "0", 
                "description": "Правый верх переда"
            },
            {
                "name": "K",
                "x": "half_back_width",
                "y": "front_length * 0.3",
                "description": "Левая точка груди"
            },
            {
                "name": "L",
                "x": "half_back_width * 2",
                "y": "front_length * 0.3",
                "description": "Правая точка груди"
            },
            {
                "name": "M",
                "x": "half_back_width * 1.5",
                "y": "front_length",
                "description": "Низ середины переда"
            },
            {
                "name": "N",
                "x": "half_back_width * 0.8",
                "y": "front_length",
                "description": "Левый низ переда"
            },
            {
                "name": "O",
                "x": "half_back_width * 2.2",
                "y": "front_length",
                "description": "Правый низ переда"
            }
        ]
    
    def _create_front_lines(self) -> List[Dict[str, Any]]:
        """Создание линий для переда"""
        return [
            {
                "name": "front_top_line",
                "start": "I",
                "end": "J",
                "type": "straight"
            },
            {
                "name": "front_left_chest",
                "start": "I",
                "end": "K", 
                "type": "straight"
            },
            {
                "name": "front_right_chest",
                "start": "J",
                "end": "L",
                "type": "straight"
            },
            {
                "name": "front_center_line",
                "start": "M",
                "end": "I",
                "type": "straight"
            },
            {
                "name": "front_left_side",
                "start": "K",
                "end": "N",
                "type": "straight"
            },
            {
                "name": "front_right_side",
                "start": "L", 
                "end": "O",
                "type": "straight"
            },
            {
                "name": "front_bottom_line",
                "start": "N",
                "end": "O",
                "type": "straight"
            }
        ]
    
    def _create_front_constraints(self) -> List[Dict[str, Any]]:
        """Создание ограничений для переда"""
        return [
            {
                "type": "horizontal",
                "points": ["I", "J"],
                "description": "Верхняя линия переда горизонтальна"
            },
            {
                "type": "parallel",
                "lines": ["front_top_line", "front_bottom_line"],
                "description": "Верх и низ переда параллельны"
            }
        ]
    
    def _create_sleeve_points(self) -> List[Dict[str, Any]]:
        """Создание точек для рукава"""
        return [
            {
                "name": "P",
                "x": "0",
                "y": "0",
                "description": "Верх оката рукава"
            },
            {
                "name": "Q",
                "x": "sleeve_width * 0.3",
                "y": "sleeve_cap_height * 0.3",
                "description": "Передняя точка оката"
            },
            {
                "name": "R",
                "x": "sleeve_width * 0.4",
                "y": "sleeve_cap_height * 0.7",
                "description": "Боковая точка оката"
            },
            {
                "name": "S",
                "x": "sleeve_width * 0.7",
                "y": "sleeve_cap_height * 0.7",
                "description": "Задняя точка оката"
            },
            {
                "name": "T",
                "x": "sleeve_width",
                "y": "0",
                "description": "Нижняя точка оката"
            },
            {
                "name": "U",
                "x": "sleeve_width * 0.2",
                "y": "sleeve_length",
                "description": "Передний низ рукава"
            },
            {
                "name": "V",
                "x": "sleeve_width * 0.8",
                "y": "sleeve_length",
                "description": "Задний низ рукава"
            }
        ]
    
    def _create_sleeve_lines(self) -> List[Dict[str, Any]]:
        """Создание линий для рукава"""
        return [
            {
                "name": "sleeve_cap_1",
                "start": "P",
                "end": "Q",
                "type": "curve"
            },
            {
                "name": "sleeve_cap_2", 
                "start": "Q",
                "end": "R",
                "type": "curve"
            },
            {
                "name": "sleeve_cap_3",
                "start": "R",
                "end": "S",
                "type": "curve"
            },
            {
                "name": "sleeve_cap_4",
                "start": "S",
                "end": "T",
                "type": "curve"
            },
            {
                "name": "front_seam",
                "start": "Q",
                "end": "U",
                "type": "straight"
            },
            {
                "name": "back_seam",
                "start": "S",
                "end": "V",
                "type": "straight"
            },
            {
                "name": "sleeve_bottom",
                "start": "U",
                "end": "V",
                "type": "straight"
            }
        ]
    
    def _create_sleeve_constraints(self) -> List[Dict[str, Any]]:
        """Создание ограничений для рукава"""
        return [
            {
                "type": "tangent",
                "curves": ["sleeve_cap_1", "sleeve_cap_2"],
                "description": "Плавный переход оката"
            },
            {
                "type": "symmetric",
                "lines": ["front_seam", "back_seam"],
                "description": "Боковые швы симметричны"
            }
        ]
    
    def _get_measurement_description(self, name: str) -> str:
        """Получение описания мерки"""
        descriptions = {
            'height': 'Рост',
            'chest': 'Обхват груди',
            'waist': 'Обхват талии', 
            'hips': 'Обхват бедер',
            'armhole_length': 'Длина проймы'
        }
        return descriptions.get(name, name)
    
    def _save_val_file(self, data: Dict[str, Any], output_file: str) -> bool:
        """
        Сохранение данных в .val файл
        
        Args:
            data: Данные для сохранения
            output_file: Имя файла
            
        Returns:
            Успешность сохранения
        """
        try:
            # Добавляем расширение .val если нет
            if not output_file.endswith('.val'):
                output_file += '.val'
            
            # Создаем директорию если нужно
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем в JSON формате с правильной структурой
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Seamly pattern saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving .val file: {e}")
            return False


# Удобная функция для быстрого экспорта
def export_to_seamly(pattern_data: Dict[str, Any], 
                    measurements: Dict[str, float],
                    output_file: str) -> bool:
    """
    Удобная функция для экспорта в Seamly
    
    Args:
        pattern_data: Данные паттерна
        measurements: Мерки тела
        output_file: Имя выходного файла
        
    Returns:
        Успешность экспорта
    """
    exporter = SeamlyExporter()
    return exporter.export_pattern_to_seamly(pattern_data, measurements, output_file)
