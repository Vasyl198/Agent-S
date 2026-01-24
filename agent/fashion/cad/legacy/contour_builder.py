import math
from typing import Dict, List, Tuple, Set, Optional
from .canonical import CanonicalCAD, Point, Segment

def extract_segments(cad: CanonicalCAD) -> List[Segment]:
    """
    ШАГ 1: Нормализация геометрии
    
    Приводит все элементы к сегментам (линиям между двумя точками)
    
    Args:
        cad: CanonicalCAD объект
        
    Returns:
        List[Segment]: Список сегментов
    """
    segments = []
    
    # Lines → прямые сегменты
    for p1, p2 in cad.lines:
        segments.append((p1, p2))
    
    # Polylines → сегменты между соседними точками
    for poly in cad.polylines:
        for i in range(len(poly) - 1):
            segments.append((poly[i], poly[i + 1]))
    
    # Splines → аппроксимация отрезками между контрольными точками
    for spline in cad.splines:
        for i in range(len(spline) - 1):
            segments.append((spline[i], spline[i + 1]))
    
    return segments

def create_bezier_curve(p1: Point, p2: Point, curve_offset: float = 50.0) -> List[Point]:
    """
    Создание кривой Безье между двумя точками
    
    Args:
        p1, p2: Начальная и конечная точки
        curve_offset: Смещение для кривизны (в мм)
        
    Returns:
        List[Point]: Точки кривой Безье
    """
    # Вычисляем контрольные точки для кубической кривой Безье
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    
    # Длина линии
    length = math.hypot(dx, dy)
    
    # Нормаль к линии (перпендикуляр)
    if length > 0:
        nx = -dy / length
        ny = dx / length
    else:
        nx, ny = 0, 0
    
    # Контрольные точки на 1/3 и 2/3 линии со смещением
    cp1 = (
        p1[0] + dx * 0.3 + nx * curve_offset,
        p1[1] + dy * 0.3 + ny * curve_offset
    )
    
    cp2 = (
        p1[0] + dx * 0.7 + nx * curve_offset,
        p1[1] + dy * 0.7 + ny * curve_offset
    )
    
    # Генерируем точки кривой Безье
    curve_points = []
    num_points = 20  # Количество точек на кривой
    
    for i in range(num_points + 1):
        t = i / num_points
        point = cubic_bezier_point(p1, cp1, cp2, p2, t)
        curve_points.append(point)
    
    return curve_points

def cubic_bezier_point(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    """
    Вычисление точки на кубической кривой Безье
    
    Args:
        p0, p1, p2, p3: Контрольные точки
        t: Параметр (0..1)
        
    Returns:
        Point: Точка на кривой
    """
    u = 1 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t
    
    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
    
    return (x, y)

def apply_flare_curves(segments: List[Segment], style: str = "flare") -> List[Segment]:
    """
    Применение кривых для стиля "flare" (расклешение)
    
    Args:
        segments: Список сегментов
        style: Стиль паттерна
        
    Returns:
        List[Segment]: Сегменты с кривыми
    """
    if style != "flare":
        return segments
    
    curved_segments = []
    
    for i, (p1, p2) in enumerate(segments):
        # Определяем тип линии по индексу
        is_side_seam = i % 4 == 1 or i % 4 == 3  # Боковые швы
        
        if is_side_seam:
            # Заменяем прямую на кривую Безье
            curve_offset = 80.0  # 8 см для расклешения
            curve_points = create_bezier_curve(p1, p2, curve_offset)
            
            # Преобразуем кривую в сегменты
            for j in range(len(curve_points) - 1):
                curved_segments.append((curve_points[j], curve_points[j + 1]))
        else:
            # Оставляем талию и низ прямыми
            curved_segments.append((p1, p2))
    
    return curved_segments

def extract_segments_with_curves(cad: CanonicalCAD, style: str = "standard") -> List[Segment]:
    """
    ШАГ 1: Нормализация геометрии с поддержкой кривых
    
    Args:
        cad: CanonicalCAD объект
        style: Стиль паттерна (standard, flare, etc.)
        
    Returns:
        List[Segment]: Список сегментов с кривыми
    """
    segments = []
    
    # Lines → прямые сегменты
    for p1, p2 in cad.lines:
        segments.append((p1, p2))
    
    # Polylines → сегменты между соседними точками
    for poly in cad.polylines:
        for i in range(len(poly) - 1):
            segments.append((poly[i], poly[i + 1]))
    
    # Splines → аппроксимация отрезками между контрольными точками
    for spline in cad.splines:
        for i in range(len(spline) - 1):
            segments.append((spline[i], spline[i + 1]))
    
    # Применяем кривые для стиля flare
    segments = apply_flare_curves(segments, style)
    
    return segments

def is_close(p1: Point, p2: Point, tol: float = 0.5) -> bool:
    """
    Проверка близости двух точек
    
    Args:
        p1, p2: Точки для сравнения
        tol: Допуск близости
        
    Returns:
        bool: True если точки близки
    """
    return abs(p1[0] - p2[0]) < tol and abs(p1[1] - p2[1]) < tol

def normalize_point(point: Point, tolerance: float = 0.1) -> Point:
    """
    Нормализация точки для устранения погрешностей
    
    Args:
        point: Исходная точка
        tolerance: Точность округления
        
    Returns:
        Point: Нормализованная точка
    """
    return (
        round(point[0] / tolerance) * tolerance,
        round(point[1] / tolerance) * tolerance
    )

def build_connectivity(segments: List[Segment], tolerance: float = 0.5) -> Dict[Point, List[Point]]:
    """
    ШАГ 2: Построение графа связности
    
    Args:
        segments: Список сегментов
        tolerance: Допуск для соединения точек
        
    Returns:
        Dict[Point, List[Point]]: Граф связности
    """
    graph = {}
    
    # Нормализуем точки для объединения близких
    normalized_segments = []
    for p1, p2 in segments:
        norm_p1 = normalize_point(p1, tolerance)
        norm_p2 = normalize_point(p2, tolerance)
        normalized_segments.append((norm_p1, norm_p2))
    
    # Строим граф связности
    for p1, p2 in normalized_segments:
        graph.setdefault(p1, []).append(p2)
        graph.setdefault(p2, []).append(p1)
    
    return graph

def find_start_point(graph: Dict[Point, List[Point]]) -> Point:
    """
    Поиск начальной точки для обхода контура
    
    Ищем точку с минимальными координатами (левая нижняя)
    
    Args:
        graph: Граф связности
        
    Returns:
        Point: Начальная точка
    """
    points = list(graph.keys())
    if not points:
        return (0.0, 0.0)
    
    # Левая нижняя точка
    start = min(points, key=lambda p: (p[1], p[0]))
    return start

def walk_contour(graph: Dict[Point, List[Point]], start: Point, tolerance: float = 0.5) -> List[Point]:
    """
    ШАГ 3: Обход контура с улучшенным алгоритмом
    
    Args:
        graph: Граф связности
        start: Начальная точка
        tolerance: Допуск для замыкания
        
    Returns:
        List[Point]: Контур (замкнутый путь)
    """
    contour = [start]
    current = start
    prev = None
    visited_segments = set()
    
    while True:
        neighbors = graph.get(current, [])
        next_point = None
        
        # Ищем следующую точку (не предыдущую и не посещенную)
        for n in neighbors:
            # Пропускаем предыдущую точку
            if prev is not None and is_close(n, prev, tolerance):
                continue
            
            # Проверяем не посещали ли этот сегмент
            segment = tuple(sorted([current, n]))
            if segment in visited_segments:
                continue
            
            next_point = n
            break
        
        if next_point is None:
            # Пробуем любую соседнюю точку
            for n in neighbors:
                if prev is None or not is_close(n, prev, tolerance):
                    next_point = n
                    break
            
            if next_point is None:
                break
        
        # Отмечаем сегмент как посещенный
        segment = tuple(sorted([current, next_point]))
        visited_segments.add(segment)
        
        prev, current = current, next_point
        
        # Проверяем на замыкание контура
        if is_close(current, start, tolerance):
            contour.append(start)
            break
        
        contour.append(current)
        
        # Защита от бесконечного цикла
        if len(contour) > 1000:
            break
    
    return contour

def build_closed_contour(cad: CanonicalCAD, tolerance: float = 0.5, style: str = "standard") -> List[Point]:
    """
    ШАГ 4: Основная функция сборки замкнутого контура с поддержкой кривых
    
    Args:
        cad: CanonicalCAD объект
        tolerance: Допуск для соединения точек
        style: Стиль паттерна (standard, flare, etc.)
        
    Returns:
        List[Point]: Замкнутый контур
    """
    # Шаг 1: Нормализация геометрии с кривыми
    segments = extract_segments_with_curves(cad, style)
    
    if not segments:
        return []
    
    # Шаг 2: Построение графа связности
    graph = build_connectivity(segments, tolerance)
    
    # Шаг 3: Поиск начальной точки
    start = find_start_point(graph)
    
    # Шаг 4: Обход контура
    contour = walk_contour(graph, start, tolerance)
    
    return contour

def build_closed_contour_with_curves(cad: CanonicalCAD, style: str = "flare", tolerance: float = 0.5) -> Tuple[List[Point], Dict]:
    """
    Построение замкнутого контура с кривыми и статистикой
    
    Args:
        cad: CanonicalCAD объект
        style: Стиль паттерна
        tolerance: Допуск для соединения точек
        
    Returns:
        Tuple[List[Point], Dict]: Контур и статистика кривых
    """
    # Строим контур с кривыми
    contour = build_closed_contour(cad, tolerance, style)
    
    # Статистика кривых
    stats = {
        "style": style,
        "curves_applied": style == "flare",
        "curve_segments": 0,
        "straight_segments": 0,
        "total_segments": len(contour) - 1 if contour else 0
    }
    
    if style == "flare" and contour:
        # Считаем количество кривых сегментов
        segments = extract_segments_with_curves(cad, style)
        original_segments = extract_segments(cad)
        
        stats["curve_segments"] = len(segments) - len(original_segments)
        stats["straight_segments"] = len(original_segments)
    
    return contour, stats

def build_all_contours(cad: CanonicalCAD, tolerance: float = 0.5) -> List[List[Point]]:
    """
⚠️ LEGACY MODULE
# DO NOT USE IN PRODUCTION
========================================

🚫 ЗАПРЕЩЕНО К ИСПОЛЬЗОВАНИЮ В ПРОДАКШЕНЕ!
✅ ВСЯ ФУНКЦИОНАЛЬНОСТЬ ПЕРЕНЕСЕНА В:
   - agent/fashion/cad/core/contour.py
   - agent/fashion/cad/core/validation.py

Оригинальный файл с логикой построения контуров.
""" 
    """
    Построение всех контуров (для сложных паттернов)
    
    Args:
        cad: CanonicalCAD объект
        tolerance: Допуск для соединения точек
        
    Returns:
        List[List[Point]]: Список всех контуров
    """
    segments = extract_segments(cad)
    
    if not segments:
        return []
    
    graph = build_connectivity(segments, tolerance)
    contours = []
    visited_points = set()
    
    # Строим контуры для всех несвязанных компонент
    for point in graph.keys():
        if point not in visited_points:
            contour = walk_contour(graph, point, tolerance)
            
            if contour and len(contour) > 2:
                contours.append(contour)
                
                # Отмечаем посещенные точки
                for p in contour:
                    visited_points.add(p)
    
    return contours

def validate_contour(contour: List[Point], check_intersections: bool = False) -> List[str]:
    """
    Валидация контура
    
    Args:
        contour: Контур для проверки
        check_intersections: Проверять самопересечения (можно отключить)
        
    Returns:
        List[str]: Список проблем
    """
    issues = []
    
    if len(contour) < 3:
        issues.append("Contour has less than 3 points")
        return issues
    
    # Проверка замыкания
    if not is_close(contour[0], contour[-1], 0.1):
        issues.append("Contour is not closed")
    
    # Проверка на дубликаты точек
    unique_points = set()
    for i, point in enumerate(contour[:-1]):  # Исключаем последнюю (дублирует первую)
        norm_point = normalize_point(point, 0.1)
        if norm_point in unique_points:
            issues.append(f"Duplicate point at index {i}: {point}")
        unique_points.add(norm_point)
    
    # Проверка на самопересечения (можно отключить)
    if check_intersections:
        for i in range(len(contour) - 1):
            p1, p2 = contour[i], contour[i + 1]
            for j in range(i + 2, len(contour) - 1):
                p3, p4 = contour[j], contour[j + 1]
                if segments_intersect(p1, p2, p3, p4):
                    issues.append(f"Self-intersection at segments {i} and {j}")
    
    return issues

def segments_intersect(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    """
    Проверка пересечения двух отрезков
    
    Args:
        p1, p2: Концы первого отрезка
        p3, p4: Концы второго отрезка
        
    Returns:
        bool: True если отрезки пересекаются
    """
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    
    # Исключаем соседние отрезки
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False
    
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def get_contour_statistics(contour: List[Point]) -> Dict:
    """
    Получение статистики контура
    
    Args:
        contour: Контур
        
    Returns:
        Dict: Статистика контура
    """
    if not contour:
        return {}
    
    # Периметр
    perimeter = 0.0
    for i in range(len(contour) - 1):
        p1, p2 = contour[i], contour[i + 1]
        perimeter += math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    
    # Границы
    xs = [p[0] for p in contour]
    ys = [p[1] for p in contour]
    
    bounds = {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys)
    }
    
    # Площадь (метод Гаусса)
    area = 0.0
    for i in range(len(contour) - 1):
        x1, y1 = contour[i]
        x2, y2 = contour[i + 1]
        area += (x1 * y2 - x2 * y1)
    area = abs(area) / 2.0
    
    return {
        "points_count": len(contour),
        "perimeter": perimeter,
        "area": area,
        "bounds": bounds,
        "is_closed": is_close(contour[0], contour[-1], 0.1) if len(contour) > 2 else False
    }

def test_contour_closed(contour: List[Point]) -> bool:
    """
    Тест замкнутости контура
    
    Args:
        contour: Контур для проверки
        
    Returns:
        bool: True если контур корректно замкнут
    """
    # Базовые проверки
    assert len(contour) > 4, f"Contour has only {len(contour)} points"
    assert contour[0] == contour[-1], "Contour is not closed"
    
    # Дополнительная валидация
    issues = validate_contour(contour)
    assert not issues, f"Contour validation failed: {issues}"
    
    return True
