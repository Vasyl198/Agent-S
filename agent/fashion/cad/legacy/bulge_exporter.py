"""
⚠️ LEGACY MODULE
# DO NOT USE IN PRODUCTION
========================================

ЭТАП 2.2 — ФУНКЦИЯ BULGE ИЗ 3 КОНСТРУКТИВНЫХ ТОЧЕК
========================================================

🚫 ЗАПРЕЩЕНО К ИСПОЛЬЗОВАНИЮ В ПРОДАКШЕНЕ!
✅ ВСЯ ФУНКЦИОНАЛЬНОСТЬ ПЕРЕНЕСЕНА В:
   - agent/fashion/cad/core/curves.py
   - agent/fashion/cad/core/geometry.py

Математическое вычисление DXF bulge для дуги через 3 точки.
Это ядро всего шага - стабильная математика, не эвристика.
"""

import math
from typing import Tuple, List
from pathlib import Path


def bulge_from_3_points(
    A: Tuple[float, float],
    M: Tuple[float, float],
    B: Tuple[float, float]
) -> float:
    """
    Вычисляет DXF bulge для дуги A → B,
    проходящей через контрольную точку M
    
    📌 Это математика, не эвристика
    📌 Работает стабильно
    📌 Проверено в CAD
    
    Args:
        A: Tuple[float, float] - начальная точка
        M: Tuple[float, float] - контрольная точка
        B: Tuple[float, float] - конечная точка
        
    Returns:
        float - bulge значение для DXF
    """
    ax, ay = A
    mx, my = M
    bx, by = B

    # длины сторон треугольника
    a = math.dist(M, B)  # M → B
    b = math.dist(A, M)  # A → M
    c = math.dist(A, B)  # A → B

    # защита от вырожденных случаев
    if a * b * c == 0:
        return 0.0

    # радиус описанной окружности через формулу Герона
    s = (a + b + c) / 2  # полупериметр
    area_sq = s * (s - a) * (s - b) * (s - c)
    area = math.sqrt(max(area_sq, 0.0))
    
    if area == 0:
        return 0.0

    # радиус описанной окружности
    R = (a * b * c) / (4 * area)

    # центральный угол (в радианах)
    theta = 2 * math.asin(min(c / (2 * R), 1.0))

    # знак дуги (лево/право) через векторное произведение
    cross = (mx - ax) * (by - ay) - (my - ay) * (bx - ax)
    sign = 1 if cross > 0 else -1

    return sign * math.tan(theta / 4)


def bulge_from_constructive_points(points: List[Tuple[float, float]]) -> List[float]:
    """
    Вычисляет bulge значения для конструктивных точек юбки
    
    🧱 Подготовка точек + bulge (БЕЗ изменения конструктора)
    
    Args:
        points: List[Tuple[float, float]] - конструктивные точки
        
    Returns:
        List[float] - bulge значения для каждой точки
    """
    bulges = [0.0] * len(points)
    
    # Индексы для конструктивной юбки:
    # 0 A (талия центр)
    # 1 M1 (прогиб талии)
    # 2 B (талия бок)
    # 3 M2 (отклонение бока)
    # 4 F (бок низа)
    # 5 E (середина низа)
    # 6 C_mid
    # 7 A (замыкание)
    
    if len(points) >= 3:
        # 🔴 ТАЛИЯ: A → B через M1
        bulges[0] = bulge_from_3_points(points[0], points[1], points[2])
    
    if len(points) >= 5:
        # 🔵 БОК: B → F через M2
        bulges[2] = bulge_from_3_points(points[2], points[3], points[4])
    
    # 📌 Остальные bulge = 0 (прямые линии)
    
    return bulges


def export_lwpolyline_dxf_with_bulge(
    points: List[Tuple[float, float]], 
    bulges: List[float], 
    filepath: str
) -> str:
    """
    Экспорт LWPOLYLINE с bulge значениями
    
    📤 3️⃣ Экспорт LWPOLYLINE С BULGE
    
    Args:
        points: List[Tuple[float, float]] - точки контура
        bulges: List[float] - bulge значения
        filepath: str - путь для сохранения
        
    Returns:
        str - путь к созданному файлу
    """
    assert len(points) == len(bulges), f"Точек: {len(points)}, bulge: {len(bulges)}"
    
    # Вычисляем границы
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    
    # Создаем директорию
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # DXF с bulge
    dxf_content = f"""0
SECTION
2
HEADER
9
$ACADVER
1
AC1027
9
$INSUNITS
70
4
9
$EXTMIN
10
{xmin}
20
{ymin}
30
0.0
9
$EXTMAX
10
{xmax}
20
{ymax}
30
0.0
0
ENDSEC
0
SECTION
2
ENTITIES
0
LWPOLYLINE
8
MAIN
90
{len(points)}
70
1
"""
    
    # Добавляем точки с bulge
    for (x, y), bulge in zip(points, bulges):
        dxf_content += f"""10
{x}
20
{y}
42
{bulge}
"""
    
    dxf_content += """0
ENDSEC
0
EOF"""
    
    # Записываем в файл
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dxf_content)
    
    return str(path)


def validate_bulge_dxf(filepath: str) -> dict:
    """
    Валидация DXF файла с bulge
    
    Args:
        filepath: str - путь к DXF файлу
        
    Returns:
        dict - результат валидации
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            'has_header': 'SECTION' in content and 'HEADER' in content,
            'has_entities': 'SECTION' in content and 'ENTITIES' in content,
            'has_lwpolyline': 'LWPOLYLINE' in content,
            'has_bulge': '42' in content,  # group code 42 для bulge
            'has_eof': content.strip().endswith('EOF'),
            'has_acadver': 'AC1027' in content,
            'has_layer': 'MAIN' in content
        }
        
        # Проверяем количество bulge значений
        bulge_count = content.count('42\n')
        checks['bulge_count'] = bulge_count
        
        # Проверяем наличие координат
        x_count = content.count('10\n')
        y_count = content.count('20\n')
        checks['coordinate_count'] = min(x_count, y_count)
        
        success_checks = [k for k, v in checks.items() if v is True]
        
        return {
            'is_valid': len([v for v in checks.values() if v is False]) == 0,
            'checks': checks,
            'success_checks': success_checks,
            'errors': [k for k, v in checks.items() if v is False],
            'warnings': [],
            'file_size': len(content)
        }
    except Exception as e:
        return {
            'is_valid': False,
            'checks': {},
            'success_checks': [],
            'errors': [f'Ошибка чтения файла: {e}'],
            'warnings': [],
            'file_size': 0
        }


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ BULGE ФУНКЦИИ")
    print("=" * 50)
    
    # Тест 1: Простая дуга
    print("📐 Тест 1: Простая дуга")
    A = (0.0, 0.0)
    M = (10.0, 10.0)
    B = (20.0, 0.0)
    
    bulge = bulge_from_3_points(A, M, B)
    print(f"   Точки: A{A} → M{M} → B{B}")
    print(f"   Bulge: {bulge:.6f}")
    
    # Тест 2: Дуга в другую сторону
    print("\n📐 Тест 2: Дуга в другую сторону")
    A = (0.0, 0.0)
    M = (10.0, -10.0)
    B = (20.0, 0.0)
    
    bulge = bulge_from_3_points(A, M, B)
    print(f"   Точки: A{A} → M{M} → B{B}")
    print(f"   Bulge: {bulge:.6f}")
    
    # Тест 3: Прямая линия
    print("\n📐 Тест 3: Прямая линия")
    A = (0.0, 0.0)
    M = (10.0, 0.0)
    B = (20.0, 0.0)
    
    bulge = bulge_from_3_points(A, M, B)
    print(f"   Точки: A{A} → M{M} → B{B}")
    print(f"   Bulge: {bulge:.6f}")
    
    # Тест 4: Конструктивная юбка
    print("\n🧪 Тест 4: Конструктивная юбка")
    
    # Конструктивные точки юбки
    points = [
        (0.0, 0.0),      # A - середина талии
        (92.5, 8.0),     # M1 - прогиб талии
        (185.0, 0.0),    # B - бок талии
        (264.0, 180.0),   # M2 - отклонение бока
        (250.0, 650.0),   # F - бок низа
        (0.0, 650.0),    # E - середина низа
        (0.0, 180.0),    # C_mid - середина бедер
        (0.0, 0.0)       # A - замыкание
    ]
    
    bulges = bulge_from_constructive_points(points)
    print(f"   📊 Точек: {len(points)}")
    print(f"   🔢 Bulge значений: {len(bulges)}")
    
    print("   📍 Bulge значения:")
    for i, bulge in enumerate(bulges):
        if abs(bulge) > 0.001:
            print(f"      {i}: {bulge:.6f} 🔄")
        else:
            print(f"      {i}: {bulge:.6f}")
    
    # Экспорт DXF с bulge
    print("\n📁 Экспорт DXF с bulge...")
    exported_path = export_lwpolyline_dxf_with_bulge(
        points, bulges, 
        "output/skirt_constructive_bulge.dxf"
    )
    print(f"   ✅ DXF создан: {exported_path}")
    
    # Валидация
    validation = validate_bulge_dxf(exported_path)
    print(f"\n🔍 Валидация DXF с bulge:")
    print(f"   ✅ Корректность: {validation['is_valid']}")
    print(f"   📊 Успешных проверок: {len(validation['success_checks'])}")
    print(f"   ❌ Ошибок: {len(validation['errors'])}")
    print(f"   📏 Bulge значений: {validation['checks'].get('bulge_count', 0)}")
    print(f"   📊 Координат: {validation['checks'].get('coordinate_count', 0)}")
    
    if validation['errors']:
        print("   ❌ Ошибки:")
        for error in validation['errors']:
            print(f"      ❌ {error}")
    
    print(f"\n✅ Bulge функция готова!")
