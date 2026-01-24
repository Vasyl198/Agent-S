"""
ЭТАП 2.1 — ЖЁСТКАЯ КОНСТРУКТОРСКАЯ ОСНОВА (без кривых)
========================================================

Фиксированная система координат, строгие контрольные точки,
минимальное число линий, нулевой curve reconstruction.
"""

from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class SkirtBase:
    """
    Жёсткая конструктивная основа юбки.
    
    Args:
        waist: float          # обхват талии
        hip: float           # обхват бедер
        hip_height: float    # высота бедер от талии
        length: float        # длина юбки
        waist_ease: float = 0.0   # прибавка по талии
        hip_ease: float = 0.0     # прибавка по бедрам
    """
    waist: float
    hip: float
    hip_height: float
    length: float
    waist_ease: float = 0.0
    hip_ease: float = 0.0

    def build_base_points(self) -> List[Tuple[float, float]]:
        """
        📐 Базовый контур половины юбки (прямая база)
        
        📌 Система координат (фиксируем навсегда):
        Y = 0     — линия талии
        Y > 0     — вниз
        X = 0     — середина
        
        Returns:
            List[Tuple[float, float]] - точки контура в правильном порядке
        """
        W = self.waist + self.waist_ease
        H = self.hip + self.hip_ease

        # Контрольные точки
        A = (0.0, 0.0)                 # середина талии
        B = (W / 4, 0.0)               # бок талии

        C = (0.0, self.hip_height)     # середина бедер
        D = (H / 4, self.hip_height)   # бок бедер

        E = (0.0, self.length)         # середина низа
        F = (H / 4, self.length)       # бок низа

        # 📌 Это уже корректное лекало, даже без кривых
        return [
            A, B,        # талия
            D, F,        # бок
            E, C,        # низ и возврат
            A            # замыкание
        ]

    def get_segments(self) -> Dict[str, List[Tuple[float, float]]]:
        """
        Получить сегменты для визуального дебага
        
        Returns:
            Dict[str, List[Tuple[float, float]]] - сегменты
        """
        points = self.build_base_points()
        
        return {
            "waist": [points[0], points[1]],           # талия
            "side": [points[2], points[3]],             # бок  
            "hem": [points[4], points[5]],             # низ
            "center": [points[5], points[0]],          # середина
        }

    def debug_visualization(self, save_path: str = "output/skirt_base_correct.png"):
        """
        🎨 Визуальный дебаг (ОБЯЗАТЕЛЬНО)
        
        Args:
            save_path: str - путь для сохранения
        """
        try:
            from ..cad.visual_debug import debug_draw_contour
        except ImportError:
            # Для прямого запуска
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from agent.fashion.cad.visual_debug import debug_draw_contour
        
        points = self.build_base_points()
        segments = self.get_segments()
        
        debug_draw_contour(
            points=points,
            segments=segments,
            title="Skirt Base – Correct Construction",
            save_path=save_path
        )

    def export_dxf(self, filepath: str):
        """
        📁 DXF ЭКСПОРТ — БЕЗ МАГИИ
        
        Args:
            filepath: str - путь для сохранения
            
        Returns:
            Dict[str, Any] - результат экспорта
        """
        try:
            from ..cad.lwpolyline_exporter import export_lwpolyline_dxf, validate_lwpolyline_dxf
        except ImportError:
            # Для прямого запуска
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from agent.fashion.cad.lwpolyline_exporter import export_lwpolyline_dxf, validate_lwpolyline_dxf
        
        # Получаем точки в правильном порядке
        points = self.build_base_points()
        
        # Экспорт БЕЗ сортировки, сглаживания, реконструкции
        exported_path = export_lwpolyline_dxf(points, filepath)
        
        # Валидация
        validation = validate_lwpolyline_dxf(exported_path)
        
        return {
            'success': validation['is_valid'],
            'filepath': exported_path,
            'points_count': len(points),
            'validation': validation
        }

    def validate_construction(self) -> Dict[str, Any]:
        """
        🔍 Валидация конструкции
        
        Returns:
            Dict[str, Any] - результат валидации
        """
        points = self.build_base_points()
        errors = []
        warnings = []
        
        # Проверка системы координат
        if points[0][1] != 0.0:
            errors.append("Талия не на Y=0")
        
        if points[0][0] != 0.0:
            errors.append("Середина не на X=0")
        
        # Проверка логичности точек
        if len(points) < 7:
            errors.append("Недостаточно точек для контура")
        
        # Проверка замыкания
        if points[0] != points[-1]:
            errors.append("Контур не замкнут")
        
        # Проверка направления (Y должен расти вниз)
        for i in range(len(points) - 1):
            if points[i][1] > points[i+1][1] and i not in [1, 2]:  # исключаем переходы вверх
                warnings.append(f"Неожиданное направление Y в точке {i}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'points_count': len(points),
            'coordinate_system': {
                'waist_y': points[0][1],
                'center_x': points[0][0],
                'length_y': points[4][1]
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертация в словарь для ML
        
        Returns:
            Dict[str, Any] - параметры модели
        """
        return {
            "waist": self.waist,
            "hip": self.hip,
            "hip_height": self.hip_height,
            "length": self.length,
            "waist_ease": self.waist_ease,
            "hip_ease": self.hip_ease
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkirtBase':
        """
        Создание из словаря
        
        Args:
            data: Dict[str, Any] - параметры
            
        Returns:
            SkirtBase - экземпляр модели
        """
        return cls(**data)


def build_base_skirt_points(
    waist: float,
    hip: float,
    hip_height: float,
    length: float,
    waist_ease: float = 0.0,
    hip_ease: float = 0.0,
) -> List[Tuple[float, float]]:
    """
    📐 Функция построения базовых точек юбки
    
    Args:
        waist: float          # обхват талии
        hip: float           # обхват бедер
        hip_height: float    # высота бедер от талии
        length: float        # длина юбки
        waist_ease: float    # прибавка по талии
        hip_ease: float     # прибавка по бедрам
        
    Returns:
        List[Tuple[float, float]] - точки контура
    """
    base = SkirtBase(
        waist=waist,
        hip=hip,
        hip_height=hip_height,
        length=length,
        waist_ease=waist_ease,
        hip_ease=hip_ease
    )
    
    return base.build_base_points()


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ SKIRT BASE")
    print("=" * 40)
    
    # Создание базовой юбки
    base = SkirtBase(
        waist=720,
        hip=960,
        hip_height=180,
        length=650,
        waist_ease=20,
        hip_ease=40
    )
    
    print(f"📊 Параметры юбки:")
    print(f"   Талия: {base.waist} + {base.waist_ease} = {base.waist + base.waist_ease}")
    print(f"   Бедра: {base.hip} + {base.hip_ease} = {base.hip + base.hip_ease}")
    print(f"   Высота бедер: {base.hip_height}")
    print(f"   Длина: {base.length}")
    
    # Построение контура
    points = base.build_base_points()
    print(f"\n📐 Контур построен: {len(points)} точек")
    
    # Валидация конструкции
    validation = base.validate_construction()
    print(f"\n🔍 Валидация конструкции:")
    print(f"   ✅ Корректность: {validation['is_valid']}")
    print(f"   ❌ Ошибок: {len(validation['errors'])}")
    print(f"   ⚠️  Предупреждений: {len(validation['warnings'])}")
    
    if validation['errors']:
        print(f"   Ошибки:")
        for error in validation['errors']:
            print(f"      ❌ {error}")
    
    # Визуальный дебаг
    print(f"\n🎨 Визуальный дебаг...")
    base.debug_visualization()
    
    # Экспорт DXF
    print(f"\n📁 Экспорт DXF...")
    result = base.export_dxf("output/skirt_base_correct.dxf")
    
    if result['success']:
        print(f"   ✅ DXF создан: {result['filepath']}")
        print(f"   📊 Точек: {result['points_count']}")
        
        validation = result['validation']
        print(f"   🔍 Валидация:")
        print(f"      ✅ Успешных проверок: {len(validation['success_checks'])}")
        print(f"      ❌ Ошибок: {len(validation['errors'])}")
    else:
        print(f"   ❌ Ошибка: {result['validation']['errors']}")
    
    # ML параметры
    ml_params = base.to_dict()
    print(f"\n🤖 ML параметры:")
    for key, value in ml_params.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ SkirtBase готов!")
