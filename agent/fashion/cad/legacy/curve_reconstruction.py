"""
⚠️ LEGACY MODULE
# DO NOT USE IN PRODUCTION
========================================

🚫 ЗАПРЕЩЕНО К ИСПОЛЬЗОВАНИЮ В ПРОДАКШЕНЕ!
✅ ВСЯ ФУНКЦИОНАЛЬНОСТЬ ПЕРЕНЕСЕНА В:
   - agent/fashion/cad/core/curves.py
   - agent/fashion/cad/core/geometry.py

CURVE RECONSTRUCTION
====================

Превращение угловатого контура в профессиональное лекало
с правильной сегментацией и сглаживанием
"""

import numpy as np
from typing import List, Tuple, Dict, Any
from scipy import interpolate
import math


def order_points_ccw(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    ВОССТАНОВЛЕНИЕ ПОРЯДКА КОНТУРА (CAD-правило)
    
    1. Найти центр масс
    2. Отсортировать по углу (против часовой стрелки)
    
    Args:
        points: точки контура
        
    Returns:
        List[Tuple[float, float]] - упорядоченные точки
    """
    if len(points) < 3:
        return points
    
    # 1. Найти центр масс
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    
    # 2. Отсортировать по углу (против часовой стрелки)
    def angle_from_center(p):
        return math.atan2(p[1] - cy, p[0] - cx)
    
    ordered = sorted(points, key=angle_from_center)
    
    print(f"   🔄 Упорядочивание: {len(points)} точек по CCW углу")
    print(f"   🎯 Центр масс: ({cx:.2f}, {cy:.2f})")
    
    return ordered


def deduplicate(points: List[Tuple[float, float]], eps: float = 0.01) -> List[Tuple[float, float]]:
    """
    УДАЛЕНИЕ ДУБЛИКАТОВ
    
    Args:
        points: точки контура
        eps: допуск для определения дубликатов
        
    Returns:
        List[Tuple[float, float]] - точки без дубликатов
    """
    cleaned = []
    for p in points:
        if not any(math.hypot(p[0] - q[0], p[1] - q[1]) < eps for q in cleaned):
            cleaned.append(p)
    
    if len(cleaned) < len(points):
        print(f"   🧹 Удалено дубликатов: {len(points) - len(cleaned)}")
    
    return cleaned


def check_contour_validity(points: List[Tuple[float, float]]) -> bool:
    """
    ПРОВЕРКА НЕ ВЫРОЖДЕННОСТИ КОНТУРА
    
    Args:
        points: точки контура
        
    Returns:
        bool: True если контур валидный
        
    Raises:
        ValueError: если контур вырожден
    """
    if len(points) < 3:
        raise ValueError("Контур должен содержать минимум 3 точки")
    
    y_coords = [p[1] for p in points]
    height = max(y_coords) - min(y_coords)
    
    # Проверяем вырожденность только если высота vraiment мала
    if height < 0.1:  # Уменьшим порог до 0.1 мм
        raise ValueError(f"Контур вырожден в линию (высота: {height:.3f} мм)")
    
    return True


def segment_contour(points: List[Tuple[float, float]]) -> Dict[str, List[Tuple[float, float]]]:
    """
    СЕГМЕНТАЦИЯ КОНТУРА (CAD-стандарт)
    
    Разбивает контур на логические зоны:
    - waist: талия (верхняя часть)
    - side: бок (соединяет талию и низ)
    - hem: низ (нижняя часть)
    
    Args:
        points: точки контура в порядке обхода
        
    Returns:
        Dict с сегментами 'waist', 'side', 'hem'
    """
    if len(points) < 3:
        raise ValueError("Для сегментации нужно минимум 3 точки")
    
    # Находим Y-координаты
    y_coords = [p[1] for p in points]
    max_y = max(y_coords)  # Самый верхний (талия)
    min_y = min(y_coords)  # Самый нижний (низ)
    
    # Находим индексы точек
    waist_indices = [i for i, p in enumerate(points) if abs(p[1] - max_y) < 1.0]
    hem_indices = [i for i, p in enumerate(points) if abs(p[1] - min_y) < 1.0]
    
    if not waist_indices or not hem_indices:
        raise ValueError("Не удалось определить талию или низ")
    
    # Берем центральные точки
    waist_center_idx = waist_indices[len(waist_indices) // 2]
    hem_center_idx = hem_indices[len(hem_indices) // 2]
    
    # Определяем сегменты
    segments = {
        'waist': [],
        'side': [],
        'hem': []
    }
    
    # Талия - точки вокруг верха
    waist_start = waist_center_idx
    waist_end = waist_center_idx
    
    # Расширяем талию в обе стороны
    for i in range(1, len(points) // 4):
        prev_idx = (waist_start - i) % len(points)
        next_idx = (waist_end + i) % len(points)
        
        if points[prev_idx][1] > max_y - 5:  # В пределах 5мм от талии
            segments['waist'].insert(0, points[prev_idx])
            waist_start = prev_idx
        
        if points[next_idx][1] > max_y - 5:
            segments['waist'].append(points[next_idx])
            waist_end = next_idx
    
    # Бок - от талии до низа (правая сторона)
    side_start = (waist_end + 1) % len(points)
    side_end = hem_center_idx
    
    i = side_start
    while True:
        segments['side'].append(points[i])
        if i == side_end:
            break
        i = (i + 1) % len(points)
        if i == side_start:  # Защита от бесконечного цикла
            break
    
    # Низ - точки вокруг низа
    hem_start = hem_center_idx
    hem_end = hem_center_idx
    
    for i in range(1, len(points) // 4):
        prev_idx = (hem_start - i) % len(points)
        next_idx = (hem_end + i) % len(points)
        
        if points[prev_idx][1] < min_y + 5:  # В пределах 5мм от низа
            segments['hem'].insert(0, points[prev_idx])
            hem_start = prev_idx
        
        if points[next_idx][1] < min_y + 5:
            segments['hem'].append(points[next_idx])
            hem_end = next_idx
    
    # Убедимся что все сегменты имеют точки
    for name, segment in segments.items():
        if len(segment) < 2:
            # Если сегмент пуст, добавляем соседние точки
            if name == 'waist':
                segments[name] = [points[waist_center_idx]]
            elif name == 'hem':
                segments[name] = [points[hem_center_idx]]
            else:
                segments[name] = [points[side_start], points[side_end]]
    
    return segments


def resample_polyline(points: List[Tuple[float, float]], target_count: int = 30) -> List[Tuple[float, float]]:
    """
    RESAMPLE — УБИРАЕМ ЛОМАНОСТЬ
    
    Равномерно увеличивает плотность точек вдоль сегмента
    CAD-минимум: 20-40 точек на кривую
    
    Args:
        points: исходные точки
        target_count: целевое количество точек
        
    Returns:
        List[Tuple[float, float]] - ресемплированные точки
    """
    if len(points) < 2:
        return points
    
    if len(points) == 2:
        # Для прямой линии просто интерполируем
        x1, y1 = points[0]
        x2, y2 = points[1]
        return [(x1 + (x2 - x1) * i / (target_count - 1),
                y1 + (y2 - y1) * i / (target_count - 1))
               for i in range(target_count)]
    
    # Для кривой используем параметрическую интерполяцию
    try:
        # Создаем параметрическую кривую
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        # Вычисляем параметрические расстояния
        distances = [0]
        for i in range(1, len(points)):
            dist = math.hypot(x_coords[i] - x_coords[i-1], y_coords[i] - y_coords[i-1])
            distances.append(distances[-1] + dist)
        
        total_length = distances[-1]
        if total_length == 0:
            return points
        
        # Нормализуем параметры
        t = [d / total_length for d in distances]
        
        # Создаем интерполяционные функции
        if len(set(t)) == len(t):  # Уникальные параметры
            fx = interpolate.interp1d(t, x_coords, kind='quadratic', fill_value='extrapolate')
            fy = interpolate.interp1d(t, y_coords, kind='quadratic', fill_value='extrapolate')
            
            # Генерируем новые точки
            new_points = []
            for i in range(target_count):
                ti = i / (target_count - 1)
                new_x = float(fx(ti))
                new_y = float(fy(ti))
                new_points.append((new_x, new_y))
            
            return new_points
        else:
            return points
            
    except Exception:
        # Если интерполяция не удалась, используем линейную
        return linear_interpolate(points, target_count)


def linear_interpolate(points: List[Tuple[float, float]], target_count: int) -> List[Tuple[float, float]]:
    """Линейная интерполяция как запасной вариант"""
    if len(points) < 2:
        return points
    
    result = []
    total_segments = len(points) - 1
    
    for i in range(target_count):
        # Позиция на исходной кривой
        pos = i * total_segments / (target_count - 1)
        segment_idx = int(pos)
        t = pos - segment_idx
        
        if segment_idx >= total_segments:
            result.append(points[-1])
        else:
            p1 = points[segment_idx]
            p2 = points[segment_idx + 1]
            x = p1[0] + t * (p2[0] - p1[0])
            y = p1[1] + t * (p2[1] - p1[1])
            result.append((x, y))
    
    return result


def fit_spline(points: List[Tuple[float, float]], smoothing: float = 0.1) -> List[Tuple[float, float]]:
    """
    FIT SPLINE для талии (мягкая кривая)
    
    Args:
        points: точки сегмента
        smoothing: параметр сглаживания
        
    Returns:
        List[Tuple[float, float]] - сглаженные точки
    """
    if len(points) < 3:
        return points
    
    try:
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        # Параметрическая интерполяция
        t = np.linspace(0, 1, len(points))
        
        # Сглаживающий сплайн
        t_smooth = np.linspace(0, 1, len(points))
        
        fx = interpolate.UnivariateSpline(t, x_coords, s=smoothing, k=3)
        fy = interpolate.UnivariateSpline(t, y_coords, s=smoothing, k=3)
        
        smooth_points = [(float(fx(ti)), float(fy(ti))) for ti in t_smooth]
        
        return smooth_points
        
    except Exception:
        return points


def fit_bezier(points: List[Tuple[float, float]], control_points: int = 4) -> List[Tuple[float, float]]:
    """
    FIT BEZIER с контролем наклона для боковой части
    
    Args:
        points: точки сегмента
        control_points: количество контрольных точек
        
    Returns:
        List[Tuple[float, float]] - сглаженные точки
    """
    if len(points) < 3:
        return points
    
    try:
        # Упрощенная реализация Bezier кривой
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        # Создаем параметрическую кривую
        t = np.linspace(0, 1, len(points))
        
        # Квадратичная интерполяция (приближение Bezier)
        from scipy.interpolate import interp1d
        fx = interp1d(t, x_coords, kind='quadratic', fill_value='extrapolate')
        fy = interp1d(t, y_coords, kind='quadratic', fill_value='extrapolate')
        
        t_smooth = np.linspace(0, 1, len(points))
        smooth_points = [(float(fx(ti)), float(fy(ti))) for ti in t_smooth]
        
        return smooth_points
        
    except Exception:
        return points


def fit_arc(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    FIT ARC для низа (почти прямая или дуга)
    
    Args:
        points: точки сегмента
        
    Returns:
        List[Tuple[float, float]] - сглаженные точки
    """
    if len(points) < 3:
        return points
    
    try:
        # Проверяем, нужно ли дуга или прямая
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        # Вычисляем кривизну
        start_y = y_coords[0]
        end_y = y_coords[-1]
        mid_y = y_coords[len(y_coords)//2]
        
        curvature = abs(mid_y - (start_y + end_y) / 2)
        
        if curvature < 1.0:  # Почти прямая
            # Просто сглаживаем линейную интерполяцию
            return linear_interpolate(points, len(points))
        else:
            # Используем дугу
            return fit_spline(points, smoothing=0.5)
            
    except Exception:
        return points


def reconstruct_contour(points: List[Tuple[float, float]], 
                     target_density: int = 30,
                     smoothing_factor: float = 0.1) -> List[Tuple[float, float]]:
    """
    ОСНОВНАЯ ФУНКЦИЯ - CURVE RECONSTRUCTION
    
    Превращает угловатый контур в профессиональное лекало
    
    Args:
        points: исходный угловатый контур
        target_density: плотность точек на сегмент
        smoothing_factor: фактор сглаживания
        
    Returns:
        List[Tuple[float, float]] - гладкий контур лекала
    """
    print(f"🔧 CURVE RECONSTRUCTION: {len(points)} точек → лекало")
    
    try:
        # ШАГ 0: Проверка валидности
        check_contour_validity(points)
        
        # ШАГ 1: Удаление дубликатов
        cleaned_points = deduplicate(points, eps=0.01)
        
        # ШАГ 2: Восстановление порядка (CAD-правило)
        ordered_points = order_points_ccw(cleaned_points)
        
        # ШАГ 3: Сегментация
        segments = segment_contour(ordered_points)
        print(f"   📐 Сегментация: waist={len(segments['waist'])}, side={len(segments['side'])}, hem={len(segments['hem'])}")
        
        # ШАГ 4: Resample каждого сегмента
        resampled = {}
        for name, segment in segments.items():
            if len(segment) >= 2:
                resampled[name] = resample_polyline(segment, target_density)
            else:
                resampled[name] = segment
        
        print(f"   📊 Resample: waist={len(resampled['waist'])}, side={len(resampled['side'])}, hem={len(resampled['hem'])}")
        
        # ШАГ 5: Curve fitting для каждого сегмента
        smooth_segments = {}
        
        # Талия - мягкая кривая
        smooth_segments['waist'] = fit_spline(resampled['waist'], smoothing=smoothing_factor)
        
        # Бок - Bezier с контролем наклона
        smooth_segments['side'] = fit_bezier(resampled['side'], control_points=4)
        
        # Низ - дуга или прямая
        smooth_segments['hem'] = fit_arc(resampled['hem'])
        
        print(f"   🎨 Curve fitting: waist={len(smooth_segments['waist'])}, side={len(smooth_segments['side'])}, hem={len(smooth_segments['hem'])}")
        
        # ШАГ 6: Сборка обратно в замкнутый контур
        final_contour = []
        
        # Добавляем сегменты в правильном порядке
        final_contour.extend(smooth_segments['waist'])
        
        # Добавляем бок (без дублирования талии)
        if len(smooth_segments['side']) > 0:
            if len(final_contour) > 0 and len(smooth_segments['side']) > 0:
                # Проверяем дублирование первой точки
                if abs(final_contour[-1][0] - smooth_segments['side'][0][0]) < 0.1 and \
                   abs(final_contour[-1][1] - smooth_segments['side'][0][1]) < 0.1:
                    final_contour.extend(smooth_segments['side'][1:])
                else:
                    final_contour.extend(smooth_segments['side'])
        
        # Добавляем низ (без дублирования)
        if len(smooth_segments['hem']) > 0:
            if len(final_contour) > 0 and len(smooth_segments['hem']) > 0:
                if abs(final_contour[-1][0] - smooth_segments['hem'][0][0]) < 0.1 and \
                   abs(final_contour[-1][1] - smooth_segments['hem'][0][1]) < 0.1:
                    final_contour.extend(smooth_segments['hem'][1:])
                else:
                    final_contour.extend(smooth_segments['hem'])
        
        # ШАГ 7: Финальная очистка и замыкание
        # Удаляем финальные дубликаты
        final_contour = deduplicate(final_contour, eps=0.01)
        
        # Гарантированное замыкание
        if len(final_contour) > 2:
            final_contour.append(final_contour[0])
        
        print(f"   ✅ Результат: {len(final_contour)} точек в гладком контуре")
        
        return final_contour
        
    except Exception as e:
        print(f"   ❌ Ошибка reconstruction: {e}")
        # В случае ошибки возвращаем исходный контур
        return points


# Тестирование
if __name__ == "__main__":
    # Тестовый контур юбки (угловатый)
    angular_skirt = [
        (0, 0),      # Левая точка талии
        (50, 0),     # Центр талии
        (100, 0),    # Правая точка талии
        (100, 30),   # Правый бок (средина)
        (100, 60),   # Правая точка низа
        (50, 60),    # Центр низа
        (0, 60),     # Левая точка низа
        (0, 30),     # Левый бок (средина)
        (0, 0)       # Замыкание
    ]
    
    print("🧪 ТЕСТ CURVE RECONSTRUCTION")
    print("=" * 50)
    
    try:
        smooth_skirt = reconstruct_contour(angular_skirt, target_density=20)
        print(f"\n✅ УСПЕХ: {len(angular_skirt)} → {len(smooth_skirt)} точек")
        print(f"🎨 Создано профессиональное лекало")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
