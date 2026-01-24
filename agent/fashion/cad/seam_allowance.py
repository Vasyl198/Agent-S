import math
from typing import Dict, List, Tuple, Any
from .canonical import CanonicalCAD, Point

def offset_line(p1: Point, p2: Point, offset: float) -> Tuple[Point, Point]:
    """
    Смещение линии на заданное расстояние
    
    Args:
        p1: Начальная точка линии
        p2: Конечная точка линии
        offset: Смещение (положительное - влево, отрицательное - вправо)
        
    Returns:
        Tuple[Point, Point]: Смещенные точки
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)

    if length == 0:
        return p1, p2

    # Нормаль (перпендикуляр влево)
    nx = -dy / length
    ny = dx / length

    return (
        (p1[0] + nx * offset, p1[1] + ny * offset),
        (p2[0] + nx * offset, p2[1] + ny * offset)
    )

def offset_polyline(points: List[Point], offset: float) -> List[Point]:
    """
    Смещение полилинии на заданное расстояние
    
    Args:
        points: Точки полилинии
        offset: Смещение
        
    Returns:
        List[Point]: Смещенные точки
    """
    if len(points) < 2:
        return points.copy()
    
    offset_points = []
    
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        o1, o2 = offset_line(p1, p2, offset)
        
        if i == 0:
            offset_points.append(o1)
        offset_points.append(o2)
    
    return offset_points

def build_seam_allowance(cad: CanonicalCAD, constraints: Dict[str, Any], points_dict: Dict[str, Dict]) -> CanonicalCAD:
    """
    Построение контура припусков на швы
    
    Args:
        cad: Основной CAD контур
        constraints: Constraints с информацией о припусках
        points_dict: Словарь точек паттерна
        
    Returns:
        CanonicalCAD: CAD с контуром припусков
    """
    seam_cad = CanonicalCAD()
    seam_cad.metadata["type"] = "seam_allowance"
    seam_cad.metadata["base_pattern_type"] = cad.metadata.get("pattern_type", "unknown")
    
    # Вспомогательная функция для получения координат точки
    def get_point(point_name: str) -> Point:
        point = points_dict.get(point_name, {})
        return (point.get("x", 0.0), point.get("y", 0.0))
    
    # Обрабатываем линии из constraints
    lines_constraints = constraints.get("lines", {})
    
    for line_name, line_data in lines_constraints.items():
        line_points = line_data.get("points", [])
        seam_allowance = line_data.get("seam_allowance", 10)  # Дефолт 10 мм
        line_type = line_data.get("type", "unknown")
        
        if len(line_points) < 2:
            continue
        
        # Получаем реальные координаты точек
        real_points = [get_point(p_name) for p_name in line_points]
        
        # Строим припуск для этой линии
        if len(real_points) == 2:
            # Простая линия
            p1, p2 = real_points
            o1, o2 = offset_line(p1, p2, seam_allowance)
            seam_cad.add_line(o1, o2)
            
        elif len(real_points) > 2:
            # Полилиния
            offset_points = offset_polyline(real_points, seam_allowance)
            seam_cad.add_polyline(offset_points)
        
        # Добавляем аннотацию с припуском
        if len(real_points) >= 2:
            mid_x = sum(p[0] for p in real_points[:2]) / 2
            mid_y = sum(p[1] for p in real_points[:2]) / 2
            
            seam_cad.add_annotation(
                f"{line_name}: {seam_allowance}mm",
                (mid_x, mid_y + 5),
                "seam_allowance"
            )
    
    # Добавляем информацию о припусках в метаданные
    seam_allowance_info = {}
    for line_name, line_data in lines_constraints.items():
        seam_allowance_info[line_name] = {
            "allowance": line_data.get("seam_allowance", 10),
            "type": line_data.get("type", "unknown")
        }
    
    seam_cad.metadata["seam_allowances"] = seam_allowance_info
    
    return seam_cad

def build_seam_allowance_from_pattern(pattern: Dict[str, Any]) -> CanonicalCAD:
    """
    Построение припусков напрямую из паттерна
    
    Args:
        pattern: Паттерн от PatternMaker
        
    Returns:
        CanonicalCAD: CAD с контуром припусков
    """
    from .from_pattern import pattern_to_cad
    
    # Конвертируем паттерн в CAD
    cad = pattern_to_cad(pattern)
    
    # Строим припуски
    constraints = pattern.get("constraints", {})
    points = pattern.get("points", {})
    
    seam_cad = build_seam_allowance(cad, constraints, points)
    
    return seam_cad

def validate_seam_allowance(seam_cad: CanonicalCAD) -> List[str]:
    """
    Валидация контура припусков
    
    Args:
        seam_cad: CAD с припусками
        
    Returns:
        List[str]: Список проблем
    """
    issues = []
    
    # Проверяем наличие элементов
    if not seam_cad.lines and not seam_cad.polylines:
        issues.append("No seam allowance elements found")
    
    # Проверяем метаданные
    if not seam_cad.metadata.get("seam_allowances"):
        issues.append("No seam allowance information in metadata")
    
    # Проверяем тип
    if seam_cad.metadata.get("type") != "seam_allowance":
        issues.append("Invalid CAD type for seam allowance")
    
    # Проверяем границы
    bounds = seam_cad.get_bounds()
    if bounds[0] == bounds[1]:
        issues.append("Invalid bounds (all points at same location)")
    
    return issues

def get_seam_allowance_statistics(seam_cad: CanonicalCAD) -> Dict[str, Any]:
    """
    Получение статистики по припускам
    
    Args:
        seam_cad: CAD с припусками
        
    Returns:
        Dict[str, Any]: Статистика припусков
    """
    stats = seam_cad.get_statistics()
    
    # Добавляем информацию о припусках
    seam_allowances = seam_cad.metadata.get("seam_allowances", {})
    
    allowance_stats = {}
    for line_name, allowance_info in seam_allowances.items():
        allowance = allowance_info.get("allowance", 0)
        line_type = allowance_info.get("type", "unknown")
        
        if line_type not in allowance_stats:
            allowance_stats[line_type] = {
                "count": 0,
                "total_allowance": 0,
                "min_allowance": float('inf'),
                "max_allowance": 0
            }
        
        allowance_stats[line_type]["count"] += 1
        allowance_stats[line_type]["total_allowance"] += allowance
        allowance_stats[line_type]["min_allowance"] = min(allowance_stats[line_type]["min_allowance"], allowance)
        allowance_stats[line_type]["max_allowance"] = max(allowance_stats[line_type]["max_allowance"], allowance)
    
    # Вычисляем средние значения
    for line_type in allowance_stats:
        if allowance_stats[line_type]["count"] > 0:
            allowance_stats[line_type]["avg_allowance"] = (
                allowance_stats[line_type]["total_allowance"] / allowance_stats[line_type]["count"]
            )
        else:
            allowance_stats[line_type]["avg_allowance"] = 0
    
    stats["seam_allowance_stats"] = allowance_stats
    
    return stats

def merge_contours(main_cad: CanonicalCAD, seam_cad: CanonicalCAD) -> CanonicalCAD:
    """
    Объединение основного контура и припусков в один CAD
    
    Args:
        main_cad: Основной контур
        seam_cad: Контур припусков
        
    Returns:
        CanonicalCAD: Объединенный CAD
    """
    merged = CanonicalCAD()
    
    # Копируем основной контур
    merged.lines.extend(main_cad.lines)
    merged.polylines.extend(main_cad.polylines)
    merged.splines.extend(main_cad.splines)
    merged.axes.extend(main_cad.axes)
    merged.annotations.extend(main_cad.annotations)
    
    # Добавляем припуски
    merged.lines.extend(seam_cad.lines)
    merged.polylines.extend(seam_cad.polylines)
    merged.annotations.extend(seam_cad.annotations)
    
    # Объединяем метаданные
    merged.metadata = main_cad.metadata.copy()
    merged.metadata.update(seam_cad.metadata)
    merged.metadata["type"] = "merged_pattern_with_seam_allowance"
    
    return merged
