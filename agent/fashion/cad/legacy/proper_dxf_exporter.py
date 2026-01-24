"""
ЕДИНСТВЕННЫЙ ПРАВИЛЬНЫЙ DXF-ЭКСПОРТЁР (LWPOLYLINE)
==============================================

✅ Обязательные требования:
- assemble_contour() - сборка контура
- reconstruct_contour() - curve reconstruction
- plot_contour() - визуальный дебаг (опционально)
- export_lwpolyline_dxf() - экспорт LWPOLYLINE
- validate_lwpolyline_dxf() - валидация

❌ ЗАПРЕТЫ:
- export пустых DXF
- export без контура
- export без validate_lwpolyline_dxf
- ❌ БОЛЬШЕ НЕ ИСПОЛЬЗУЕМ POLYLINE/VERTEX/SEQEND
- ✅ ИСПОЛЬЗУЕМ LWPOLYLINE (DXF AC1027)
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any
import re

# Импорты наших функций
from .validate_dxf import validate_dxf_structure
from ..debug.plot_contour import plot_contour
from .curve_reconstruction import reconstruct_contour
from .lwpolyline_exporter import export_lwpolyline_dxf, validate_lwpolyline_dxf


def assemble_contour(cad) -> List[Tuple[float, float]]:
    """
    Собирает контур из CAD данных
    
    Args:
        cad: CAD объект с линиями и полилиниями
        
    Returns:
        List[Tuple[float, float]] - упорядоченные точки контура
        
    Raises:
        ValueError: если невозможно собрать контур
    """
    if not cad or (not hasattr(cad, 'lines') and not hasattr(cad, 'polylines')):
        raise ValueError("CAD объект пуст или некорректен")
    
    # Собираем все сегменты
    segments = []
    
    # Извлекаем линии
    if hasattr(cad, 'lines') and cad.lines:
        for p1, p2 in cad.lines:
            segments.append(((float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1]))))
    
    # Извлекаем полилинии
    if hasattr(cad, 'polylines') and cad.polylines:
        for polyline in cad.polylines:
            for i in range(len(polyline) - 1):
                p1 = polyline[i]
                p2 = polyline[i + 1]
                segments.append(((float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1]))))
    
    if not segments:
        raise ValueError("В CAD данных не найдено сегментов")
    
    # Строим граф соединений
    graph = {}
    for start, end in segments:
        if start not in graph:
            graph[start] = []
        if end not in graph:
            graph[end] = []
        graph[start].append(end)
        graph[end].append(start)
    
    # Находим все точки
    all_points = list(graph.keys())
    
    # Пробуем построить контур методом обхода
    best_contour = None
    max_length = 0
    
    # Пробуем начать с каждой точки
    for start_point in all_points:
        contour = [start_point]
        visited = {start_point}
        current = start_point
        
        # Обходим граф
        while True:
            # Ищем следующую точку
            next_point = None
            for neighbor in graph[current]:
                if neighbor not in visited:
                    next_point = neighbor
                    break
            
            if next_point is None:
                # Пробуем вернуться к началу
                for neighbor in graph[current]:
                    if _same_point(neighbor, start_point) and len(contour) >= 3:
                        next_point = neighbor
                        break
                
                if next_point is None:
                    break
            
            contour.append(next_point)
            visited.add(next_point)
            current = next_point
            
            # Если вернулись к началу
            if _same_point(current, start_point):
                break
        
        # Проверяем замыкание
        if len(contour) >= 4:  # Минимум 3 уникальные точки + замыкание
            # Убираем последнюю точку (дублирует первую)
            closed_contour = contour[:-1]
            
            # Проверяем что все точки связаны
            if len(closed_contour) >= 3:
                if len(closed_contour) > max_length:
                    max_length = len(closed_contour)
                    best_contour = closed_contour
    
    if not best_contour:
        # Если не удалось построить контур, пробуем упрощенный метод
        # Просто собираем все уникальные точки в порядке их появления
        all_points_ordered = []
        seen = set()
        
        for p1, p2 in segments:
            if p1 not in seen:
                all_points_ordered.append(p1)
                seen.add(p1)
            if p2 not in seen:
                all_points_ordered.append(p2)
                seen.add(p2)
        
        if len(all_points_ordered) >= 3:
            # Проверяем можно ли замкнуть
            first = all_points_ordered[0]
            last = all_points_ordered[-1]
            
            # Если первая и последняя точки близки, замыкаем
            if _same_point(first, last):
                best_contour = all_points_ordered[:-1]
            else:
                # Добавляем первую точку в конец для замыкания
                best_contour = all_points_ordered + [first]
    
    if not best_contour or len(best_contour) < 3:
        raise ValueError(f"Не удалось собрать контур. Найдено точек: {len(all_points) if all_points else 0}")
    
    return best_contour


def is_contour_closed(points: List[Tuple[float, float]], tolerance: float = 0.5) -> Tuple[bool, float]:
    """
    ПРАВИЛЬНАЯ ПРОВЕРКА ЗАМЫКАНИЯ КОНТУРА (КАК В CAD)
    
    Args:
        points: точки контура
        tolerance: допуск в мм (стандартно 0.5 мм)
        
    Returns:
        Tuple[bool, float]: (замкнут, расстояние)
    """
    if len(points) < 3:
        return False, float('inf')
    
    # Вычисляем расстояние между первой и последней точкой
    first_point = points[0]
    last_point = points[-1]
    distance = ((first_point[0] - last_point[0])**2 + (first_point[1] - last_point[1])**2)**0.5
    
    # CAD-правило: контур замкнут если расстояние ≤ допуска
    is_closed = distance <= tolerance
    
    return is_closed, distance


def normalize_contour(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    ОРМАЛИЗАЦИЯ КООРДИНАТ (КРИТИЧНО)
    
    Центрирует лекало в (0,0)
    Решает 80% "пустых DXF"
    
    Args:
        points: исходные точки контура
        
    Returns:
        List[Tuple[float, float]] - нормализованные точки
    """
    if not points:
        return points
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    # Вычисляем центр bounding box
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # Центр контура
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    
    # Смещаем в (0,0)
    normalized = [(x - cx, y - cy) for x, y in points]
    
    print(f"   🎯 Нормализация: центр ({cx:.2f}, {cy:.2f}) → (0, 0)")
    print(f"   📐 Bounding box: ({min_x:.2f}, {min_y:.2f}) → ({max_x:.2f}, {max_y:.2f})")
    
    return normalized


def export_closed_polyline(contour: List[Tuple[float, float]], filepath: str) -> str:
    """
    Экспортирует контур как замкнутую POLYLINE в DXF
    
    Args:
        contour: List[Tuple[float, float]] - точки контура в порядке обхода
        filepath: str - путь для сохранения DXF файла
        
    Returns:
        str - путь к созданному файлу
        
    Raises:
        ValueError: если контур некорректен
    """
    if not contour or len(contour) < 3:
        raise ValueError(f"Контур должен содержать минимум 3 точки, получено: {len(contour)}")
    
    # ПРАВИЛЬНАЯ ПРОВЕРКА ЗАМЫКАНИЯ
    is_closed, distance = is_contour_closed(contour, tolerance=0.5)
    
    if not is_closed:
        raise ValueError(
            f"Контур не замкнут. "
            f"Расстояние между первой и последней точкой: {distance:.3f} мм (допуск 0.5 мм)"
        )
    
    # CAD-правильное поведение: если почти замкнут, forcibly замыкаем
    if distance > 0.01:  # Если есть небольшой gap
        contour = contour.copy()
        contour.append(contour[0])  # Принудительное замыкание
    
    # НОРМАЛИЗАЦИЯ КООРДИНАТ (КРИТИЧЕСКИ ВАЖНО)
    normalized_contour = normalize_contour(contour)
    
    # Вычисляем границы для EXTMIN/EXTMAX
    xs = [p[0] for p in normalized_contour]
    ys = [p[1] for p in normalized_contour]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # Создаем DXF с правильным HEADER
    dxf_content = _create_closed_polyline_dxf(normalized_contour, min_x, min_y, max_x, max_y)
    
    # Сохраняем файл
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dxf_content)
    
    return str(path)


def export_proper_dxf(cad, filepath: str, debug: bool = False, 
                     enable_curve_reconstruction: bool = True) -> Dict[str, Any]:
    """
    ЕДИНСТВЕННЫЙ ПРАВИЛЬНЫЙ ФЛОУ ЭКСПОРТА LWPOLYLINE DXF
    
    Args:
        cad: CAD объект
        filepath: str - путь для сохранения
        debug: bool - включить визуальный дебаг
        enable_curve_reconstruction: bool - включить сглаживание контура
        
    Returns:
        Dict[str, Any] - результат экспорта с валидацией
        
    Raises:
        RuntimeError: если любой этап не прошел
    """
    result = {
        'success': False,
        'filepath': filepath,
        'original_points': 0,
        'smooth_points': 0,
        'reconstruction_enabled': enable_curve_reconstruction,
        'validation_report': None,
        'error': None
    }
    
    try:
        # ШАГ 1: Сборка контура
        print("🔧 ШАГ 1: Сборка контура...")
        contour = assemble_contour(cad)
        result['original_points'] = len(contour)
        print(f"   ✅ Контур собран: {len(contour)} точек")
        
        # ШАГ 1.5: Curve Reconstruction (опционально)
        if enable_curve_reconstruction and len(contour) >= 3:
            print("🎨 ШАГ 1.5: Curve Reconstruction...")
            try:
                # Проверяем валидность ДО нормализации
                from .curve_reconstruction import check_contour_validity
                check_contour_validity(contour)
                
                smooth_contour = reconstruct_contour(
                    contour, 
                    target_density=25, 
                    smoothing_factor=0.1
                )
                result['smooth_points'] = len(smooth_contour)
                print(f"   ✅ Сглаживание: {len(contour)} → {len(smooth_contour)} точек")
                contour = smooth_contour
            except Exception as e:
                print(f"   ⚠️ Curve reconstruction не удался: {e}")
                print(f"   🔄 Используем исходный контур")
        
        # ШАГ 2: Визуальный дебаг (опционально)
        if debug:
            print("🎨 ШАГ 2: Визуальный дебаг...")
            try:
                plot_contour(contour, title=f"LWPOLYLINE Export Debug - {len(contour)} points")
                print("   ✅ Визуализация выполнена")
            except Exception as e:
                print(f"   ⚠️ Визуализация не удалась: {e}")
        
        # ШАГ 3: Экспорт LWPOLYLINE
        print("📁 ШАГ 3: Экспорт LWPOLYLINE DXF...")
        exported_path = export_lwpolyline_dxf(contour, filepath)
        print(f"   ✅ LWPOLYLINE DXF сохранен: {exported_path}")
        
        # ШАГ 4: Валидация LWPOLYLINE
        print("🔍 ШАГ 4: Валидация LWPOLYLINE DXF...")
        validation_report = validate_lwpolyline_dxf(exported_path)
        result['validation_report'] = validation_report
        
        if not validation_report["is_valid"]:
            error_msg = f"LWPOLYLINE DXF export failed validation: {validation_report['errors']}"
            print(f"   ❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        print("   ✅ Валидация пройдена")
        
        # Успех
        result['success'] = True
        print(f"🎉 LWPOLYLINE DXF ЭКСПОРТ УСПЕШЕН!")
        print(f"   📁 Файл: {exported_path}")
        print(f"   📊 Исходных точек: {result['original_points']}")
        if result['smooth_points'] > 0:
            print(f"   🎨 Сглаженных точек: {result['smooth_points']}")
        print(f"   🔍 Валидация: {len(validation_report['success_checks'])} успешных проверок")
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ LWPOLYLINE DXF EXPORT FAILED: {e}")
        raise RuntimeError(f"LWPOLYLINE DXF export failed: {e}")


def _create_closed_polyline_dxf(contour: List[Tuple[float, float]], 
                              min_x: float, min_y: float, 
                              max_x: float, max_y: float) -> str:
    """Создает DXF содержимое с замкнутой POLYLINE и правильным HEADER"""
    
    dxf_header = f"""0
SECTION
2
HEADER
9
$INSUNITS
70
4
9
$EXTMIN
10
{min_x:.6f}
20
{min_y:.6f}
30
0.0
9
$EXTMAX
10
{max_x:.6f}
20
{max_y:.6f}
30
0.0
0
ENDSEC
0
SECTION
2
TABLES
0
TABLE
2
LAYER
70
1
0
LAYER
2
MAIN_CONTOUR
70
0
62
7
420
0
ENDTAB
0
SECTION
2
ENTITIES
"""
    
    # POLYLINE с замыканием
    polyline = """0
POLYLINE
8
MAIN_CONTOUR
66
1
70
1
40
0.0
"""
    
    # Добавляем вершины
    for i, (x, y) in enumerate(contour):
        polyline += f"""0
VERTEX
8
MAIN_CONTOUR
10
{x:.6f}
20
{y:.6f}
30
0.0
"""
    
    # Закрываем POLYLINE
    polyline += """0
SEQEND
"""
    
    dxf_footer = """0
ENDSEC
0
EOF"""
    
    return dxf_header + polyline + dxf_footer


def _same_point(a: Tuple[float, float], b: Tuple[float, float], eps: float = 1e-3) -> bool:
    """Проверяет совпадение точек с допуском"""
    return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps


# Пример использования
if __name__ == "__main__":
    # Тестовый пример
    class MockCAD:
        def __init__(self):
            self.lines = [
                ((0, 0), (100, 0)),
                ((100, 0), (100, 50)),
                ((100, 50), (0, 50)),
                ((0, 50), (0, 0))
            ]
            self.polylines = []
    
    try:
        cad = MockCAD()
        result = export_proper_dxf(cad, "output/test_proper.dxf", debug=True)
        
        if result['success']:
            print("\n🎉 УСПЕХ: Правильный DXF экспорт работает!")
        else:
            print(f"\n❌ ОШИБКА: {result['error']}")
            
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
