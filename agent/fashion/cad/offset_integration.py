"""
ЭТАП 2 — ИНТЕГРАЦИЯ OFFSET С КОНСТРУКТИВНОЙ ЮБКОЙ
====================================================

🎯 РЕЗУЛЬТАТ OFFSET ЭТАПА:
✅ отдельный контур припуска
✅ точный припуск 10 мм / 15 мм / любой
✅ без самопересечений
✅ с сохранением дуг
✅ готовый DXF для производства

🔗 И САМОЕ ВАЖНОЕ:
После offset:
👉 старый параметрический движок
👉 ML
👉 генерация размеров
всё это можно безопасно подключать.
"""

import math
from typing import List, Tuple, Dict, Any
from pathlib import Path

from .offset_engine import OffsetEngine, SegmentType
from .bulge_exporter import export_lwpolyline_dxf_with_bulge, validate_bulge_dxf


class OffsetIntegration:
    """
    🔧 ИНТЕГРАЦИЯ OFFSET С КОНСТРУКТИВНОЙ ЮБКОЙ
    
    Полный цикл: конструктивная юбка → offset → DXF припуска
    """
    
    def __init__(self, offset_distance: float = 10.0):
        """
        Args:
            offset_distance: float - расстояние припуска (мм)
        """
        self.offset_engine = OffsetEngine(offset_distance)
        self.offset_distance = offset_distance
    
    def offset_skirt_constructive(self, points: List[Tuple[float, float]], 
                                 bulges: List[float]) -> Dict[str, Any]:
        """
        Offset конструктивной юбки
        
        Args:
            points: List[Tuple[float, float]] - исходные точки
            bulges: List[float] - исходные bulge значения
            
        Returns:
            Dict[str, Any] - результат offset
        """
        # Проверка входных данных
        if len(points) < 3 or len(bulges) < 1:
            return {
                'success': False,
                'error': 'Недостаточно точек для offset',
                'offset_points': [],
                'offset_bulges': []
            }
        
        # Выполнение offset
        try:
            offset_points, offset_bulges = self.offset_engine.offset_contour(points, bulges)
            
            # Валидация результата
            validation = self._validate_offset_result(points, bulges, offset_points, offset_bulges)
            
            return {
                'success': validation['is_valid'],
                'error': None if validation['is_valid'] else 'Ошибка валидации offset',
                'offset_points': offset_points,
                'offset_bulges': offset_bulges,
                'validation': validation,
                'original_points_count': len(points),
                'offset_points_count': len(offset_points),
                'original_arcs': sum(1 for b in bulges if abs(b) > 0.001),
                'offset_arcs': sum(1 for b in offset_bulges if abs(b) > 0.001),
                'offset_distance': self.offset_distance
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка offset: {str(e)}',
                'offset_points': [],
                'offset_bulges': []
            }
    
    def _validate_offset_result(self, original_points: List[Tuple[float, float]], 
                               original_bulges: List[float],
                               offset_points: List[Tuple[float, float]], 
                               offset_bulges: List[float]) -> Dict[str, Any]:
        """
        Валидация результата offset
        
        Args:
            original_points: List[Tuple[float, float]] - исходные точки
            original_bulges: List[float] - исходные bulge
            offset_points: List[Tuple[float, float]] - смещённые точки
            offset_bulges: List[float] - смещённые bulge
            
        Returns:
            Dict[str, Any] - результат валидации
        """
        errors = []
        warnings = []
        
        # Проверка количества точек
        if len(offset_points) < 3:
            errors.append("Недостаточно точек в offset контуре")
        
        # Проверка замыкания контура
        if offset_points and offset_points[0] != offset_points[-1]:
            warnings.append("Offset контур не замкнут")
        
        # Проверка сохранения дуг
        original_arcs = sum(1 for b in original_bulges if abs(b) > 0.001)
        offset_arcs = sum(1 for b in offset_bulges if abs(b) > 0.001)
        
        if offset_arcs != original_arcs:
            warnings.append(f"Количество дуг изменилось: {original_arcs} → {offset_arcs}")
        
        # Проверка расстояния смещения (приблизительно)
        if len(original_points) >= 2 and len(offset_points) >= 2:
            # Проверяем несколько точек
            for i in range(min(3, len(original_points), len(offset_points))):
                orig_x, orig_y = original_points[i]
                off_x, off_y = offset_points[i]
                
                distance = math.sqrt((off_x - orig_x)**2 + (off_y - orig_y)**2)
                expected_distance = self.offset_distance
                
                if abs(distance - expected_distance) > expected_distance * 0.5:
                    warnings.append(f"Отклонение расстояния в точке {i}: {distance:.1f} мм (ожидается {expected_distance:.1f})")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def export_offset_dxf(self, offset_points: List[Tuple[float, float]], 
                          offset_bulges: List[float], filepath: str) -> Dict[str, Any]:
        """
        Экспорт offset контура в DXF
        
        Args:
            offset_points: List[Tuple[float, float]] - смещённые точки
            offset_bulges: List[float] - смещённые bulge
            filepath: str - путь для сохранения
            
        Returns:
            Dict[str, Any] - результат экспорта
        """
        try:
            # Экспорт DXF
            exported_path = export_lwpolyline_dxf_with_bulge(offset_points, offset_bulges, filepath)
            
            # Валидация DXF
            validation = validate_bulge_dxf(exported_path)
            
            return {
                'success': validation['is_valid'],
                'filepath': exported_path,
                'validation': validation,
                'points_count': len(offset_points),
                'bulge_count': sum(1 for b in offset_bulges if abs(b) > 0.001)
            }
        except Exception as e:
            return {
                'success': False,
                'filepath': None,
                'validation': {'is_valid': False, 'errors': [f'Ошибка экспорта: {str(e)}']},
                'points_count': 0,
                'bulge_count': 0
            }
    
    def process_skirt_with_offset(self, points: List[Tuple[float, float]], 
                                  bulges: List[float], 
                                  base_filepath: str = None,
                                  offset_filepath: str = None) -> Dict[str, Any]:
        """
        Полная обработка юбки с offset
        
        Args:
            points: List[Tuple[float, float]] - исходные точки
            bulges: List[float] - исходные bulge
            base_filepath: str - путь для базового DXF
            offset_filepath: str - путь для offset DXF
            
        Returns:
            Dict[str, Any] - полный результат
        """
        result = {
            'original': {
                'points': points,
                'bulges': bulges,
                'points_count': len(points),
                'arcs_count': sum(1 for b in bulges if abs(b) > 0.001)
            },
            'offset': None,
            'base_dxf': None,
            'offset_dxf': None
        }
        
        # 1. Выполнение offset
        offset_result = self.offset_skirt_constructive(points, bulges)
        result['offset'] = offset_result
        
        if not offset_result['success']:
            return result
        
        # 2. Экспорт базового контура
        if base_filepath:
            base_dxf_result = self.export_offset_dxf(points, bulges, base_filepath)
            result['base_dxf'] = base_dxf_result
        
        # 3. Экспорт offset контура
        if offset_filepath:
            offset_dxf_result = self.export_offset_dxf(
                offset_result['offset_points'], 
                offset_result['offset_bulges'], 
                offset_filepath
            )
            result['offset_dxf'] = offset_dxf_result
        
        return result


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ OFFSET INTEGRATION")
    print("=" * 60)
    
    # Тестовый контур (юбка с клёшом)
    points = [
        (0.0, 0.0),          # A
        (92.5, 8.0),         # M1
        (185.0, 0.0),        # B
        (264.0, 180.0),      # M2
        (250.0, 650.0),      # F
        (125.0, 662.0),      # H_mid
        (0.0, 650.0),        # E
        (0.0, 180.0),        # C_mid
        (0.0, 0.0)           # A (замыкание)
    ]
    
    bulges = [
        -0.086486,  # талия
        0.0,
        0.225381,   # бок
        0.0,
        0.095131,   # низ
        0.0,
        0.0,
        0.0,
        0.0
    ]
    
    print("📊 Исходный контур:")
    print(f"   Точек: {len(points)}")
    print(f"   Дуг: {sum(1 for b in bulges if abs(b) > 0.001)}")
    
    # Тест разных расстояний offset
    offset_distances = [5.0, 10.0, 15.0, 20.0]
    
    for distance in offset_distances:
        print(f"\n🔧 ТЕСТ OFFSET С РАССТОЯНИЕМ: {distance} мм")
        print("-" * 50)
        
        # Создание интеграции
        offset_integration = OffsetIntegration(offset_distance=distance)
        
        # Полная обработка
        result = offset_integration.process_skirt_with_offset(
            points=points,
            bulges=bulges,
            base_filepath=f"output/skirt_base_offset_{distance}.dxf",
            offset_filepath=f"output/skirt_offset_{distance}.dxf"
        )
        
        # Результаты
        offset_result = result['offset']
        print(f"   ✅ Offset успешен: {offset_result['success']}")
        
        if offset_result['success']:
            print(f"   📊 Точек: {offset_result['offset_points_count']}")
            print(f"   🔄 Дуг: {offset_result['offset_arcs']}")
            print(f"   📏 Расстояние: {offset_result['offset_distance']} мм")
            
            # Валидация
            validation = offset_result['validation']
            print(f"   🔍 Валидация: {'✅' if validation['is_valid'] else '❌'}")
            print(f"      ❌ Ошибок: {len(validation['errors'])}")
            print(f"      ⚠️  Предупреждений: {len(validation['warnings'])}")
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    print(f"         ⚠️  {warning}")
        else:
            print(f"   ❌ Ошибка: {offset_result['error']}")
        
        # DXF результаты
        base_dxf = result['base_dxf']
        offset_dxf = result['offset_dxf']
        
        if base_dxf and base_dxf['success']:
            print(f"   📁 Базовый DXF: {base_dxf['filepath']}")
        
        if offset_dxf and offset_dxf['success']:
            print(f"   📁 Offset DXF: {offset_dxf['filepath']}")
            print(f"   📊 Точек в DXF: {offset_dxf['points_count']}")
            print(f"   🔄 Дуг в DXF: {offset_dxf['bulge_count']}")
    
    print(f"\n✅ Offset Integration готов!")
