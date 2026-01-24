from .canonical import CanonicalCAD, Point
from typing import Dict, List, Any

def pattern_to_cad(pattern: dict) -> CanonicalCAD:
    """
    Конвертация паттерна в каноническое CAD представление
    
    Args:
        pattern: Паттерн от PatternMaker с points, lines, curves, constraints
        
    Returns:
        CanonicalCAD: Каноническое CAD представление
    """
    cad = CanonicalCAD()
    
    # Извлекаем компоненты паттерна
    points = pattern.get("points", {})
    lines = pattern.get("lines", {})
    curves = pattern.get("curves", {})
    constraints = pattern.get("constraints", {})
    
    # Вспомогательная функция для получения координат точки
    def get_point(point_name: str) -> Point:
        point = points.get(point_name, {})
        return (point.get("x", 0.0), point.get("y", 0.0))
    
    # 1. Прямые линии
    for line_name, line_data in lines.items():
        start_point = line_data.get("start", {})
        end_point = line_data.get("end", {})
        
        # Если координаты заданы напрямую
        if isinstance(start_point, dict) and "x" in start_point:
            p1 = (start_point.get("x", 0.0), start_point.get("y", 0.0))
            p2 = (end_point.get("x", 0.0), end_point.get("y", 0.0))
        # Если координаты заданы через имена точек
        else:
            p1 = get_point(start_point)
            p2 = get_point(end_point)
        
        cad.add_line(p1, p2)
    
    # 2. Кривые → сплайны
    for curve_name, curve_data in curves.items():
        spline_points = []
        
        # Разные типы кривых
        if curve_data.get("type") == "bezier":
            # Кривая Безье с контрольными точками
            start = get_point(curve_data.get("start", ""))
            control1 = curve_data.get("control1", {})
            control2 = curve_data.get("control2", {})
            end = get_point(curve_data.get("end", ""))
            
            # Обрабатываем контрольные точки (могут быть как координатами, так и именами точек)
            if isinstance(control1, dict) and "x" in control1:
                c1 = (control1.get("x", 0.0), control1.get("y", 0.0))
            else:
                c1 = get_point(control1)
                
            if isinstance(control2, dict) and "x" in control2:
                c2 = (control2.get("x", 0.0), control2.get("y", 0.0))
            else:
                c2 = get_point(control2)
            
            spline_points = [start, c1, c2, end]
        
        elif curve_data.get("type") == "arc":
            # Дуга с центром и радиусом
            center = get_point(curve_data.get("center", ""))
            start_angle = curve_data.get("start_angle", 0)
            end_angle = curve_data.get("end_angle", 90)
            radius = curve_data.get("radius", 10)
            
            # Генерируем точки дуги
            import math
            num_points = 8
            for i in range(num_points + 1):
                angle = math.radians(start_angle + (end_angle - start_angle) * i / num_points)
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
                spline_points.append((x, y))
        
        else:
            # Общий случай - кривая Безье по умолчанию
            start = get_point(curve_data.get("start", ""))
            control1 = curve_data.get("control1", {})
            control2 = curve_data.get("control2", {})
            end = get_point(curve_data.get("end", ""))
            
            # Обрабатываем контрольные точки (могут быть как координатами, так и именами точек)
            if isinstance(control1, dict) and "x" in control1:
                c1 = (control1.get("x", 0.0), control1.get("y", 0.0))
            else:
                c1 = get_point(control1)
                
            if isinstance(control2, dict) and "x" in control2:
                c2 = (control2.get("x", 0.0), control2.get("y", 0.0))
            else:
                c2 = get_point(control2)
            
            spline_points = [start, c1, c2, end]
        
        if spline_points:
            cad.add_spline(spline_points)
    
    # 3. Оси симметрии из constraints
    axes = constraints.get("axes", {})
    for axis_name, axis_points in axes.items():
        if isinstance(axis_points, list) and len(axis_points) >= 2:
            p1 = get_point(axis_points[0])
            p2 = get_point(axis_points[1])
            cad.add_axis(p1, p2)
    
    # 4. Линии из constraints (WAIST_LINE, HEM_LINE, etc.)
    constraint_lines = constraints.get("lines", {})
    for line_name, line_points in constraint_lines.items():
        if isinstance(line_points, list) and len(line_points) >= 2:
            # Создаем полилинию из точек линии
            polyline_points = [get_point(p_name) for p_name in line_points]
            cad.add_polyline(polyline_points)
    
    # 5. Аннотации на основе метаданных
    metadata = constraints.get("metadata", {})
    if metadata.get("pattern_type"):
        bounds = cad.get_bounds()
        center_x = (bounds[0][0] + bounds[1][0]) / 2
        center_y = bounds[0][1] - 10  # Под паттерном
        
        cad.add_annotation(
            f"Pattern: {metadata['pattern_type']}",
            (center_x, center_y),
            "title"
        )
    
    # 6. Измерения для градации
    measurements = constraints.get("measurements", {})
    for measurement_name, measurement_data in measurements.items():
        if measurement_data.get("type") == "distance" and "points" in measurement_data:
            points_list = measurement_data["points"]
            if len(points_list) >= 2:
                p1 = get_point(points_list[0])
                p2 = get_point(points_list[1])
                
                # Добавляем аннотацию с размером
                import math
                distance = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2
                
                cad.add_annotation(
                    f"{measurement_name}: {distance:.1f}",
                    (mid_x, mid_y + 5),
                    "dimension"
                )
    
    # 7. Копируем метаданные
    cad.metadata = metadata.copy()
    cad.metadata.update({
        "source": pattern.get("source", "unknown"),
        "construction_method": pattern.get("construction_method", "unknown"),
        "dataset_adjusted": pattern.get("dataset_adjusted", False),
        "pattern_half": pattern.get("pattern_half", "unknown")
    })
    
    return cad

def validate_pattern_for_cad(pattern: dict) -> List[str]:
    """
    Валидация паттерна перед конвертацией в CAD
    
    Args:
        pattern: Паттерн для валидации
        
    Returns:
        List[str]: Список проблем
    """
    issues = []
    
    # Проверяем обязательные компоненты
    if "points" not in pattern:
        issues.append("Missing 'points' in pattern")
    
    if "lines" not in pattern and "curves" not in pattern:
        issues.append("Pattern must contain 'lines' or 'curves'")
    
    # Проверяем точки
    points = pattern.get("points", {})
    if not points:
        issues.append("No points defined in pattern")
    
    # Проверяем constraints
    constraints = pattern.get("constraints", {})
    if not constraints:
        issues.append("No constraints defined - CAD features will be limited")
    
    # Проверяем метаданные
    metadata = constraints.get("metadata", {})
    if not metadata.get("cad_ready", False):
        issues.append("Pattern not marked as CAD-ready")
    
    return issues
