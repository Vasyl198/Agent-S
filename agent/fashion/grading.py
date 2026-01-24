"""
Fashion Grading Module

Модуль для градации лекал на разные размеры
"""

from typing import Dict, Any, List, Tuple
import math
import xml.etree.ElementTree as ET


class PatternGrader:
    """Класс для градации лекал"""
    
    def __init__(self):
        """Инициализация градатора"""
        # Стандартные приращения для градации
        self.size_increments = {
            "XS": -4,
            "S": -2, 
            "M": 0,
            "L": +2,
            "XL": +4,
            "XXL": +6
        }
        
        # Коэффициенты для разных типов линий
        self.grading_rules = {
            "width": 1.0,          # Полная ширина
            "chest_depth": 0.5,     # Глубина проймы
            "shoulder": 0.3,        # Плечо
            "sleeve_width": 0.8,    # Ширина рукава
            "sleeve_length": 0.4,    # Длина рукава
            "neckline": 0.2          # Горловина
        }
    
    def grade_pattern(self, base_pattern: Dict[str, Any], size_steps: Dict[str, int]) -> Dict[str, Any]:
        """
        Градация базового лекала на разные размеры
        
        Args:
            base_pattern: Базовое лекало (размер M)
            size_steps: Шаги градации для каждого размера
            
        Returns:
            Словарь с отградированными лекалами
        """
        graded_patterns = {}
        
        # Получаем базовые линии из паттерна
        base_lines = base_pattern.get('lines', {})
        base_points = base_pattern.get('points', {})
        
        for size_name, increment in size_steps.items():
            # Создаем копию базового паттерна
            graded_pattern = {
                "lines": {},
                "points": {},
                "curves": {}
            }
            
            # Градируем линии
            for line_name, line_data in base_lines.items():
                graded_line = self._grade_line(line_data, increment, line_name)
                graded_pattern["lines"][line_name] = graded_line
            
            # Градируем точки
            for point_name, point_data in base_points.items():
                graded_point = self._grade_point(point_data, increment, point_name)
                graded_pattern["points"][point_name] = graded_point
            
            # Сохраняем отградированный паттерн
            graded_patterns[f"SHIRT_{size_name}"] = graded_pattern
        
        return graded_patterns
    
    def _grade_line(self, line_data: Dict[str, Any], increment: int, line_name: str) -> Dict[str, Any]:
        """
        Градация отдельной линии
        
        Args:
            line_data: Данные линии
            increment: Приращение размера
            line_name: Имя линии
            
        Returns:
            Отградированная линия
        """
        graded_line = line_data.copy()
        
        # Определяем тип линии по названию
        line_type = self._classify_line(line_name)
        
        # Получаем коэффициент градации
        grading_factor = self.grading_rules.get(line_type, 1.0)
        
        # Градируем начальную и конечную точки
        if 'start' in graded_line:
            graded_line['start'] = self._grade_point(graded_line['start'], increment, line_name + '_start')
        
        if 'end' in graded_line:
            graded_line['end'] = self._grade_point(graded_line['end'], increment, line_name + '_end')
        
        return graded_line
    
    def _grade_point(self, point_data: Dict[str, Any], increment: int, point_name: str) -> Dict[str, Any]:
        """
        Градация отдельной точки
        
        Args:
            point_data: Данные точки
            increment: Приращение размера
            point_name: Имя точки
            
        Returns:
            Отградированная точка
        """
        graded_point = point_data.copy()
        
        # Определяем тип точки по названию
        point_type = self._classify_point(point_name)
        
        # Получаем коэффициент градации
        grading_factor = self.grading_rules.get(point_type, 1.0)
        
        # Применяем градацию
        actual_increment = increment * grading_factor * 0.5  # 0.5 см за размер
        
        # Градируем координаты
        if 'x' in graded_point:
            graded_point['x'] += actual_increment
        
        if 'y' in graded_point:
            # Для Y координаты используем меньший коэффициент
            y_factor = 0.3 if 'depth' in point_type else 0.2
            graded_point['y'] += actual_increment * y_factor
        
        return graded_point
    
    def _classify_line(self, line_name: str) -> str:
        """
        Классификация линии по названию
        
        Args:
            line_name: Имя линии
            
        Returns:
            Тип линии
        """
        line_name_lower = line_name.lower()
        
        if any(keyword in line_name_lower for keyword in ['chest', 'bust', 'width']):
            return 'width'
        elif any(keyword in line_name_lower for keyword in ['armhole', 'depth']):
            return 'chest_depth'
        elif any(keyword in line_name_lower for keyword in ['shoulder']):
            return 'shoulder'
        elif any(keyword in line_name_lower for keyword in ['sleeve', 'cap']):
            return 'sleeve_width'
        elif any(keyword in line_name_lower for keyword in ['neck', 'collar']):
            return 'neckline'
        else:
            return 'width'  # По умолчанию
    
    def _classify_point(self, point_name: str) -> str:
        """
        Классификация точки по названию
        
        Args:
            point_name: Имя точки
            
        Returns:
            Тип точки
        """
        point_name_lower = point_name.lower()
        
        if any(keyword in point_name_lower for keyword in ['chest', 'bust']):
            return 'width'
        elif any(keyword in point_name_lower for keyword in ['armhole', 'depth']):
            return 'chest_depth'
        elif any(keyword in point_name_lower for keyword in ['shoulder']):
            return 'shoulder'
        elif any(keyword in point_name_lower for keyword in ['sleeve', 'cap']):
            return 'sleeve_width'
        elif any(keyword in point_name_lower for keyword in ['neck', 'collar']):
            return 'neckline'
        else:
            return 'width'  # По умолчанию
    
    def export_graded_patterns_svg(self, graded_patterns: Dict[str, Any], output_file: str) -> bool:
        """
        Экспорт всех отградированных размеров в один SVG файл
        
        Args:
            graded_patterns: Отградированные паттерны
            output_file: Имя выходного файла
            
        Returns:
            Успешность экспорта
        """
        try:
            # Создаем SVG документ
            svg = ET.Element("svg")
            svg.set("xmlns", "http://www.w3.org/2000/svg")
            svg.set("width", "1200")
            svg.set("height", "800")
            svg.set("viewBox", "0 0 1200 800")
            
            # Определяем цвета для разных размеров
            size_colors = {
                "XS": "#FF6B6B",  # Красный
                "S": "#4ECDC4",   # Бирюзовый
                "M": "#45B7D1",   # Синий
                "L": "#96CEB4",   # Зеленый
                "XL": "#FFEAA7",   # Желтый
                "XXL": "#DDA0DD"  # Фиолетовый
            }
            
            # Позиции для размещения размеров
            positions = {
                "XS": (100, 100),
                "S": (300, 100),
                "M": (500, 100),
                "L": (700, 100),
                "XL": (900, 100),
                "XXL": (100, 400)
            }
            
            # Добавляем каждый размер в отдельную группу
            for size_key, pattern_data in graded_patterns.items():
                # Извлекаем имя размера
                size_name = size_key.replace("SHIRT_", "")
                
                # Создаем группу для размера
                group = ET.SubElement(svg, "g")
                group.set("id", f"SHIRT_{size_name}")
                
                # Применяем смещение
                offset_x, offset_y = positions.get(size_name, (0, 0))
                
                # Добавляем линии
                lines = pattern_data.get('lines', {})
                for line_name, line_data in lines.items():
                    line = ET.SubElement(group, "line")
                    
                    start = line_data.get('start', {})
                    end = line_data.get('end', {})
                    
                    line.set("x1", str(start.get('x', 0) + offset_x))
                    line.set("y1", str(start.get('y', 0) + offset_y))
                    line.set("x2", str(end.get('x', 0) + offset_x))
                    line.set("y2", str(end.get('y', 0) + offset_y))
                    line.set("stroke", size_colors.get(size_name, "black"))
                    line.set("stroke-width", "1")
                    line.set("id", f"{size_name}_{line_name}")
                
                # Добавляем точки
                points = pattern_data.get('points', {})
                for point_name, point_data in points.items():
                    circle = ET.SubElement(group, "circle")
                    circle.set("cx", str(point_data.get('x', 0) + offset_x))
                    circle.set("cy", str(point_data.get('y', 0) + offset_y))
                    circle.set("r", "2")
                    circle.set("fill", size_colors.get(size_name, "black"))
                    circle.set("id", f"{size_name}_{point_name}")
                
                # Добавляем текстовую подпись
                text = ET.SubElement(group, "text")
                text.set("x", str(offset_x))
                text.set("y", str(offset_y - 20))
                text.set("font-family", "Arial, sans-serif")
                text.set("font-size", "16")
                text.set("font-weight", "bold")
                text.set("fill", size_colors.get(size_name, "black"))
                text.text = f"SIZE {size_name}"
            
            # Добавляем метаданные
            metadata = ET.SubElement(svg, "metadata")
            import json
            metadata.text = json.dumps({
                "format": "svg",
                "type": "graded_patterns",
                "sizes": list(graded_patterns.keys()),
                "grading_method": "proportional"
            })
            
            # Сохраняем файл
            tree = ET.ElementTree(svg)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            
            return True
            
        except Exception as e:
            print(f"Error exporting graded patterns: {e}")
            return False
    
    def grade_sleeve_pattern(self, base_sleeve: Dict[str, Any], size_steps: Dict[str, int]) -> Dict[str, Any]:
        """
        Градация рукава с сохранением пропорций
        
        Args:
            base_sleeve: Базовый рукав
            size_steps: Шаги градации
            
        Returns:
            Отградированные рукава
        """
        graded_sleeves = {}
        
        for size_name, increment in size_steps.items():
            graded_sleeve = base_sleeve.copy()
            
            # Градируем линии рукава с учетом пропорций
            lines = base_sleeve.get('lines', [])
            graded_lines = []
            
            for line in lines:
                graded_line = line.copy()
                line_name = line.get('name', '')
                
                # Определяем тип линии рукава
                if 'cap' in line_name.lower():
                    # Окат рукава - максимальная градация
                    factor = 1.0
                elif 'seam' in line_name.lower():
                    # Боковой шов - средняя градация
                    factor = 0.7
                elif 'bottom' in line_name.lower():
                    # Низ рукава - минимальная градация
                    factor = 0.5
                else:
                    factor = 0.8
                
                # Применяем градацию
                actual_increment = increment * factor * 0.5
                
                if 'start' in graded_line:
                    graded_line['start'] = self._apply_increment_to_point(
                        graded_line['start'], actual_increment
                    )
                
                if 'end' in graded_line:
                    graded_line['end'] = self._apply_increment_to_point(
                        graded_line['end'], actual_increment
                    )
                
                graded_lines.append(graded_line)
            
            graded_sleeve['lines'] = graded_lines
            
            # Обновляем информацию о рукаве
            if 'info' in graded_sleeve:
                info = graded_sleeve['info'].copy()
                info['sleeve_width'] += actual_increment * 2
                info['sleeve_length'] += actual_increment * 0.5
                info['cap_height'] += actual_increment * 0.3
                graded_sleeve['info'] = info
            
            graded_sleeves[f"SLEEVE_{size_name}"] = graded_sleeve
        
        return graded_sleeves
    
    def _apply_increment_to_point(self, point: Dict[str, Any], increment: float) -> Dict[str, Any]:
        """Применение приращения к точке"""
        graded_point = point.copy()
        
        if 'x' in graded_point:
            graded_point['x'] += increment
        
        if 'y' in graded_point:
            graded_point['y'] += increment * 0.3  # Меньшее приращение по Y
        
        return graded_point


# Удобная функция для быстрой градации
def grade_pattern(base_pattern: Dict[str, Any], size_steps: Dict[str, int]) -> Dict[str, Any]:
    """
    Удобная функция для градации паттерна
    
    Args:
        base_pattern: Базовый паттерн
        size_steps: Шаги градации
        
    Returns:
        Отградированные паттерны
    """
    grader = PatternGrader()
    return grader.grade_pattern(base_pattern, size_steps)


def export_graded_svg(graded_patterns: Dict[str, Any], output_file: str) -> bool:
    """
    Удобная функция для экспорта градации в SVG
    
    Args:
        graded_patterns: Отградированные паттерны
        output_file: Имя выходного файла
        
    Returns:
        Успешность экспорта
    """
    grader = PatternGrader()
    return grader.export_graded_patterns_svg(graded_patterns, output_file)
