"""
LWPOLYLINE DXF EXPORTER - ЭТАЛОННЫЙ ЭКСПОРТЁР
==========================================

Полный переход на LWPOLYLINE с эталонным DXF форматом
LibreCAD гарантированно работает только с LWPOLYLINE
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any
import math


def export_lwpolyline_dxf(points: List[Tuple[float, float]], filepath: str) -> str:
    """
    ЭТАЛОННЫЙ ЭКСПОРТ LWPOLYLINE DXF
    
    Args:
        points: List[Tuple[float, float]] - точки контура
        filepath: str - путь для сохранения
        
    Returns:
        str - путь к созданному файлу
        
    Raises:
        AssertionError: если точки некорректны
    """
    assert len(points) >= 3, "Минимум 3 точки"
    
    # Проверка на NaN и дубликаты
    cleaned_points = []
    for x, y in points:
        assert not (math.isnan(x) or math.isnan(y)), f"NaN в точках: ({x}, {y})"
        
        # Удаляем дубликаты (последовательные)
        if not cleaned_points or (abs(x - cleaned_points[-1][0]) > 0.001 or 
                                 abs(y - cleaned_points[-1][1]) > 0.001):
            cleaned_points.append((x, y))
    
    assert len(cleaned_points) >= 3, f"После очистки осталось {len(cleaned_points)} точек"
    
    # Вычисляем границы
    xs = [p[0] for p in cleaned_points]
    ys = [p[1] for p in cleaned_points]
    
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    
    # Создаем директорию
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Эталонный DXF AC1027 (R2013)
    with open(path, "w", encoding="utf-8") as f:
        # HEADER
        f.write("0\nSECTION\n2\nHEADER\n")
        f.write("9\n$ACADVER\n1\nAC1027\n")
        f.write("9\n$INSUNITS\n70\n4\n")
        f.write(f"9\n$EXTMIN\n10\n{xmin}\n20\n{ymin}\n30\n0.0\n")
        f.write(f"9\n$EXTMAX\n10\n{xmax}\n20\n{ymax}\n30\n0.0\n")
        f.write("0\nENDSEC\n")
        
        # TABLES
        f.write("0\nSECTION\n2\nTABLES\n")
        
        # LTYPE - CONTINUOUS
        f.write(
            "0\nTABLE\n2\nLTYPE\n70\n1\n"
            "0\nLTYPE\n2\nCONTINUOUS\n70\n64\n3\nSolid line\n"
            "72\n65\n73\n0\n40\n0.0\n0\nENDTAB\n"
        )
        
        # LAYER - MAIN
        f.write(
            "0\nTABLE\n2\nLAYER\n70\n1\n"
            "0\nLAYER\n2\nMAIN\n70\n0\n62\n7\n6\nCONTINUOUS\n"
            "0\nENDTAB\n"
        )
        
        f.write("0\nENDSEC\n")
        
        # ENTITIES
        f.write("0\nSECTION\n2\nENTITIES\n")
        f.write("0\nLWPOLYLINE\n8\nMAIN\n")
        f.write(f"90\n{len(cleaned_points)}\n")  # Количество точек
        f.write("70\n1\n")  # Замкнутый
        
        # Координаты точек
        for x, y in cleaned_points:
            f.write(f"10\n{x}\n20\n{y}\n")
        
        f.write("0\nENDSEC\n0\nEOF\n")
    
    print(f"   ✅ LWPOLYLINE DXF создан: {path.name}")
    print(f"   📊 Точек: {len(cleaned_points)}")
    print(f"   📐 Границы: ({xmin:.1f}, {ymin:.1f}) → ({xmax:.1f}, {ymax:.1f})")
    print(f"   🎯 Формат: AC1027 (R2013)")
    
    return str(path)


def validate_lwpolyline_dxf(filepath: str) -> Dict[str, Any]:
    """
    РЕАЛЬНАЯ ВАЛИДАЦИЯ LWPOLYLINE DXF
    
    Args:
        filepath: путь к DXF файлу
        
    Returns:
        Dict[str, Any] - результат валидации
    """
    result = {
        'is_valid': False,
        'errors': [],
        'warnings': [],
        'info': {},
        'success_checks': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверка базовой структуры
        if '0\nSECTION' not in content:
            result['errors'].append('Отсутствует SECTION')
            return result
        
        # Проверка HEADER
        if '2\nHEADER' not in content:
            result['errors'].append('Отсутствует HEADER')
        else:
            result['success_checks'].append('HEADER найден')
        
        # Проверка ACADVER
        if '9\n$ACADVER' in content and '1\nAC1027' in content:
            result['success_checks'].append('ACADVER = AC1027')
            result['info']['acadver'] = 'AC1027'
        else:
            result['errors'].append('ACADVER != AC1027')
        
        # Проверка INSUNITS
        if '9\n$INSUNITS' in content and '70\n4' in content:
            result['success_checks'].append('INSUNITS = 4')
            result['info']['insunits'] = 4
        else:
            result['errors'].append('INSUNITS != 4')
        
        # Проверка EXTMIN/EXTMAX
        if '9\n$EXTMIN' in content and '9\n$EXTMAX' in content:
            result['success_checks'].append('EXTMIN/EXTMAX найдены')
            
            # Извлекаем границы
            import re
            extmin_match = re.search(r'9\n\$EXTMIN\n10\n([\d.-]+)\n20\n([\d.-]+)', content)
            extmax_match = re.search(r'9\n\$EXTMAX\n10\n([\d.-]+)\n20\n([\d.-]+)', content)
            
            if extmin_match and extmax_match:
                result['info']['extmin'] = (float(extmin_match.group(1)), float(extmin_match.group(2)))
                result['info']['extmax'] = (float(extmax_match.group(1)), float(extmax_match.group(2)))
        else:
            result['errors'].append('EXTMIN/EXTMAX отсутствуют')
        
        # Проверка TABLES
        if '2\nTABLES' in content:
            result['success_checks'].append('TABLES найдены')
            
            # Проверка LTYPE
            if '2\nCONTINUOUS' in content:
                result['success_checks'].append('LTYPE CONTINUOUS найден')
            else:
                result['errors'].append('LTYPE CONTINUOUS отсутствует')
            
            # Проверка LAYER
            if '2\nMAIN' in content:
                result['success_checks'].append('LAYER MAIN найден')
            else:
                result['errors'].append('LAYER MAIN отсутствует')
        else:
            result['errors'].append('TABLES отсутствуют')
        
        # Проверка ENTITIES
        if '2\nENTITIES' in content:
            result['success_checks'].append('ENTITIES найдены')
            
            # Проверка LWPOLYLINE
            lwpolyline_count = content.count('0\nLWPOLYLINE')
            if lwpolyline_count > 0:
                result['success_checks'].append(f'LWPOLYLINE найден: {lwpolyline_count}')
                result['info']['lwpolyline_count'] = lwpolyline_count
                
                # Проверка количества точек
                points_match = re.search(r'90\n(\d+)', content)
                if points_match:
                    points_count = int(points_match.group(1))
                    result['info']['points_count'] = points_count
                    
                    if points_count >= 3:
                        result['success_checks'].append(f'Точек: {points_count} (>=3)')
                    else:
                        result['errors'].append(f'Точек: {points_count} (<3)')
                
                # Проверка замыкания
                if '70\n1' in content:
                    result['success_checks'].append('LWPOLYLINE замкнут (70=1)')
                else:
                    result['errors'].append('LWPOLYLINE не замкнут (70!=1)')
                
                # Проверка координат
                coord_matches = re.findall(r'10\n([\d.-]+)\n20\n([\d.-]+)', content)
                result['info']['coordinates'] = [(float(x), float(y)) for x, y in coord_matches]
                
                # Проверка на NaN
                for x, y in result['info']['coordinates']:
                    if math.isnan(x) or math.isnan(y):
                        result['errors'].append(f'NaN в координатах: ({x}, {y})')
                        break
                else:
                    result['success_checks'].append('Нет NaN в координатах')
                
                # Проверка на дубликаты
                if len(coord_matches) == len(set(coord_matches)):
                    result['success_checks'].append('Нет дубликатов координат')
                else:
                    result['warnings'].append('Есть дубликаты координат')
                
            else:
                result['errors'].append('LWPOLYLINE отсутствует')
        else:
            result['errors'].append('ENTITIES отсутствуют')
        
        # Проверка EOF
        if content.endswith('0\nEOF'):
            result['success_checks'].append('EOF найден')
        else:
            result['warnings'].append('EOF отсутствует или некорректен')
        
        # Итоговая валидация
        result['is_valid'] = len(result['errors']) == 0
        
    except Exception as e:
        result['errors'].append(f'Ошибка чтения файла: {e}')
    
    return result


# Тестирование
if __name__ == "__main__":
    # Тестовый прямоугольник юбки
    test_points = [
        (-100, 0),   # левая талия
        (0, 0),      # правая талия
        (0, 60),     # правый низ
        (-100, 60)   # левый низ
    ]
    
    print("🧪 ТЕСТ LWPOLYLINE EXPORTER")
    print("=" * 50)
    
    try:
        # Экспорт
        filepath = export_lwpolyline_dxf(test_points, "output/test_lwpolyline_generated.dxf")
        
        # Валидация
        validation = validate_lwpolyline_dxf(filepath)
        
        print(f"\n🔍 ВАЛИДАЦИЯ:")
        print(f"   ✅ Успешных проверок: {len(validation['success_checks'])}")
        print(f"   ❌ Ошибок: {len(validation['errors'])}")
        print(f"   ⚠️  Предупреждений: {len(validation['warnings'])}")
        
        if validation['is_valid']:
            print(f"\n✅ DXF ВАЛИДЕН!")
            for check in validation['success_checks']:
                print(f"   ✅ {check}")
        else:
            print(f"\n❌ DXF НЕ ВАЛИДЕН!")
            for error in validation['errors']:
                print(f"   ❌ {error}")
        
        print(f"\n📊 ИНФО:")
        for key, value in validation['info'].items():
            print(f"   📋 {key}: {value}")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
