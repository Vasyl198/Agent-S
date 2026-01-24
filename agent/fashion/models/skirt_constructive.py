"""
ЭТАП 2.2 — КОНСТРУКТИВНЫЕ КРИВЫЕ (НЕ spline, НЕ magic)
=========================================================

Добавить форму юбки как это делают конструкторы, а не графические редакторы.
Кривизна появляется только там, где она реально нужна.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import math


@dataclass
class SkirtConstructive:
    """
    Конструктивная модель юбки с инженерными кривыми.
    
    Args:
        waist: float          # обхват талии
        hip: float           # обхват бедер
        hip_height: float    # высота бедер от талии
        length: float        # длина юбки
        waist_ease: float = 0.0   # прибавка по талии
        hip_ease: float = 0.0     # прибавка по бедрам
        side_out: float = 12.0     # отклонение бока в зоне бедер (мм)
        waist_depth: float = 10.0  # прогиб талии вниз (мм)
    """
    waist: float
    hip: float
    hip_height: float
    length: float
    waist_ease: float = 0.0
    hip_ease: float = 0.0
    side_out: float = 12.0
    waist_depth: float = 10.0

    def waist_curve_points(self, A: Tuple[float, float], B: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        🔴 ТАЛИЯ — ТОЛЬКО ЛЁГКИЙ ПРОГИБ
        
        ❗️ Важное правило: Талия НИКОГДА не spline
        
        Args:
            A: Tuple[float, float] - начало талии
            B: Tuple[float, float] - конец талии
            
        Returns:
            List[Tuple[float, float]] - 3 точки талии с прогибом
        """
        ax, ay = A
        bx, by = B

        # Прогиб задаётся числом
        mid = ((ax + bx) / 2, ay + self.waist_depth)

        return [A, mid, B]

    def side_curve_points(self, B: Tuple[float, float], D: Tuple[float, float], 
                         F: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        🔵 БОК ЮБКИ — единственная обязательная кривая
        
        В реальной конструкции: бок НЕ вертикальный, он уходит наружу в области бёдр
        
        Args:
            B: Tuple[float, float] - бок талии
            D: Tuple[float, float] - бок бедер
            F: Tuple[float, float] - бок низа
            
        Returns:
            List[Tuple[float, float]] - 3 точки бока с отклонением
        """
        bx, by = B
        dx, dy = D
        fx, fy = F

        # Контрольная точка строго на уровне бедер
        C = (dx + self.side_out, dy)

        return [B, C, F]

    def hem_points(self, E: Tuple[float, float], F: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        🟢 НИЗ — ПОКА ПРЯМОЙ (ВАЖНО!)
        
        На этом этапе: никаких клёшей, никаких волн
        
        Args:
            E: Tuple[float, float] - середина низа
            F: Tuple[float, float] - бок низа
            
        Returns:
            List[Tuple[float, float]] - 2 точки низа
        """
        return [F, E]

    def build_constructive_contour(self) -> List[Tuple[float, float]]:
        """
        📐 СБОРКА КОНТУРА (СТРОГО)
        
        ⚠️ Порядок точек НИКОГДА не меняется
        
        Returns:
            List[Tuple[float, float]] - конструктивный контур
        """
        W = self.waist + self.waist_ease
        H = self.hip + self.hip_ease

        # Контрольные точки базовой конструкции
        A = (0.0, 0.0)                 # середина талии
        B = (W / 4, 0.0)               # бок талии
        C_mid = (0.0, self.hip_height) # середина бедер
        D = (H / 4, self.hip_height)   # бок бедер
        E = (0.0, self.length)         # середина низа
        F = (H / 4, self.length)       # бок низа

        # Конструктивные кривые
        waist = self.waist_curve_points(A, B)
        side = self.side_curve_points(B, D, F)
        hem = self.hem_points(E, F)

        # Сборка контура в строгом порядке
        contour = (
            waist +           # талия (3 точки)
            side[1:] +       # бок (2 точки, пропускаем B)
            hem[1:] +         # низ (1 точка, пропускаем F)
            [C_mid, A]        # середина и замыкание
        )

        return contour

    def get_segments(self) -> Dict[str, List[Tuple[float, float]]]:
        """
        Получить сегменты для визуального дебага
        
        Returns:
            Dict[str, List[Tuple[float, float]]] - сегменты
        """
        W = self.waist + self.waist_ease
        H = self.hip + self.hip_ease

        A = (0.0, 0.0)
        B = (W / 4, 0.0)
        C_mid = (0.0, self.hip_height)
        D = (H / 4, self.hip_height)
        E = (0.0, self.length)
        F = (H / 4, self.length)

        return {
            "waist": self.waist_curve_points(A, B),
            "side": self.side_curve_points(B, D, F),
            "hem": self.hem_points(E, F),
            "center": [C_mid, A]
        }

    def debug_visualization(self, save_path: str = "output/skirt_constructive_debug.png"):
        """
        🎨 Визуальный дебаг конструктивных кривых
        
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
        
        points = self.build_constructive_contour()
        segments = self.get_segments()
        
        debug_draw_contour(
            points=points,
            segments=segments,
            title="Skirt Constructive – Engineering Curves",
            save_path=save_path
        )

    def export_dxf(self, filepath: str):
        """
        📁 DXF ЭКСПОРТ (тот же, эталонный)
        
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
        points = self.build_constructive_contour()
        
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
        🔍 Валидация конструктивной модели
        
        Returns:
            Dict[str, Any] - результат валидации
        """
        points = self.build_constructive_contour()
        errors = []
        warnings = []
        
        # Проверка системы координат
        if points[0][1] != 0.0:
            errors.append("Талия не на Y=0")
        
        if points[0][0] != 0.0:
            errors.append("Середина не на X=0")
        
        # Проверка наличия кривых
        if len(points) < 7:
            errors.append("Недостаточно точек для конструктивного контура")
        
        # Проверка замыкания
        if points[0] != points[-1]:
            errors.append("Контур не замкнут")
        
        # Проверка отклонения бока
        W = self.waist + self.waist_ease
        expected_side_x = (W / 4) + self.side_out
        
        side_points = [p for p in points if abs(p[1] - self.hip_height) < 1.0]
        if side_points:
            max_side_x = max(p[0] for p in side_points)
            if abs(max_side_x - expected_side_x) > 1.0:
                warnings.append(f"Отклонение бока: {max_side_x:.1f} (ожидается {expected_side_x:.1f})")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'points_count': len(points),
            'construction_params': {
                'side_out': self.side_out,
                'waist_depth': self.waist_depth
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
            "hip_ease": self.hip_ease,
            "side_out": self.side_out,
            "waist_depth": self.waist_depth
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkirtConstructive':
        """
        Создание из словаря
        
        Args:
            data: Dict[str, Any] - параметры
            
        Returns:
            SkirtConstructive - экземпляр модели
        """
        return cls(**data)


def build_constructive_skirt(
    waist: float,
    hip: float,
    hip_height: float,
    length: float,
    waist_ease: float = 0.0,
    hip_ease: float = 0.0,
    side_out: float = 12.0,
    waist_depth: float = 10.0
) -> List[Tuple[float, float]]:
    """
    📐 Функция построения конструктивного контура юбки
    
    Args:
        waist: float          # обхват талии
        hip: float           # обхват бедер
        hip_height: float    # высота бедер от талии
        length: float        # длина юбки
        waist_ease: float    # прибавка по талии
        hip_ease: float     # прибавка по бедрам
        side_out: float     # отклонение бока в зоне бедер (мм)
        waist_depth: float  # прогиб талии вниз (мм)
        
    Returns:
        List[Tuple[float, float]] - конструктивный контур
    """
    skirt = SkirtConstructive(
        waist=waist,
        hip=hip,
        hip_height=hip_height,
        length=length,
        waist_ease=waist_ease,
        hip_ease=hip_ease,
        side_out=side_out,
        waist_depth=waist_depth
    )
    
    return skirt.build_constructive_contour()


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ SKIRT CONSTRUCTIVE")
    print("=" * 50)
    
    # Создание конструктивной юбки
    skirt = SkirtConstructive(
        waist=720,
        hip=960,
        hip_height=180,
        length=650,
        waist_ease=20,
        hip_ease=40,
        side_out=14,
        waist_depth=8
    )
    
    print("📊 Параметры юбки:")
    print(f"   Талия: {skirt.waist} + {skirt.waist_ease} = {skirt.waist + skirt.waist_ease}")
    print(f"   Бедра: {skirt.hip} + {skirt.hip_ease} = {skirt.hip + skirt.hip_ease}")
    print(f"   Высота бедер: {skirt.hip_height}")
    print(f"   Длина: {skirt.length}")
    print(f"   Отклонение бока: {skirt.side_out} мм")
    print(f"   Прогиб талии: {skirt.waist_depth} мм")
    
    # Построение контура
    points = skirt.build_constructive_contour()
    print(f"\n📐 Конструктивный контур: {len(points)} точек")
    
    print("📍 Контрольные точки:")
    for i, point in enumerate(points):
        print(f"   {i}: ({point[0]:.1f}, {point[1]:.1f})")
    
    # Валидация
    validation = skirt.validate_construction()
    print(f"\n🔍 Валидация конструкции:")
    print(f"   ✅ Корректность: {validation['is_valid']}")
    print(f"   ❌ Ошибок: {len(validation['errors'])}")
    print(f"   ⚠️  Предупреждений: {len(validation['warnings'])}")
    
    if validation['errors']:
        print("   Ошибки:")
        for error in validation['errors']:
            print(f"      ❌ {error}")
    
    if validation['warnings']:
        print("   Предупреждения:")
        for warning in validation['warnings']:
            print(f"      ⚠️  {warning}")
    
    # Визуальный дебаг
    print(f"\n🎨 Визуальный дебаг...")
    skirt.debug_visualization()
    
    # Экспорт DXF
    print(f"\n📁 Экспорт DXF...")
    result = skirt.export_dxf("output/skirt_constructive_v1.dxf")
    
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
    ml_params = skirt.to_dict()
    print(f"\n🤖 ML параметры:")
    for key, value in ml_params.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ SkirtConstructive готов!")
