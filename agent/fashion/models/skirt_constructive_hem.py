"""
ЭТАП 2.2 — КОНСТРУКТИВНЫЕ КРИВЫЕ С КЛЁШЕМ НИЗА
=========================================================

Добавляем клёш низа с bulge как у талии.
НИЗ ЮБКИ С BULGE (ПРЯМО СЕЙЧАС)
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import math


@dataclass
class SkirtConstructiveHem:
    """
    Конструктивная модель юбки с клёшом низа.
    
    Args:
        waist: float          # обхват талии
        hip: float           # обхват бедер
        hip_height: float    # высота бедер от талии
        length: float        # длина юбки
        waist_ease: float = 0.0   # прибавка по талии
        hip_ease: float = 0.0     # прибавка по бедрам
        side_out: float = 12.0     # отклонение бока в зоне бедер (мм)
        waist_depth: float = 10.0  # прогиб талии вниз (мм)
        hem_out: float = 0.0      # клёш низа (мм)
    """
    waist: float
    hip: float
    hip_height: float
    length: float
    waist_ease: float = 0.0
    hip_ease: float = 0.0
    side_out: float = 12.0
    waist_depth: float = 10.0
    hem_out: float = 0.0

    def waist_curve_points(self, A: Tuple[float, float], B: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        🔴 ТАЛИЯ — ТОЛЬКО ЛЁГКИЙ ПРОГИБ
        
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

    def hem_curve_points(self, F: Tuple[float, float], E: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        🟢 НИЗ ЮБКИ С BULGE (ПРЯМО СЕЙЧАС)
        
        Добавляем ОДНУ величину: hem_out: float = 0.0  # клёш низа (мм)
        
        Конструктивная логика:
        0 → прямая
        0 → клёш
        <0 → заужение
        
        Args:
            F: Tuple[float, float] - бок низа
            E: Tuple[float, float] - середина низа
            
        Returns:
            List[Tuple[float, float]] - 3 точки низа с клёшом
        """
        fx, fy = F
        ex, ey = E

        # 📌 Ровно как талия
        # 📌 Одна величина → одна дуга
        # 📌 Никакой магии
        mid = ((fx + ex) / 2, fy + self.hem_out)

        return [F, mid, E]

    def build_constructive_contour(self) -> List[Tuple[float, float]]:
        """
        📐 СБОРКА КОНТУРА (СТРОГО)
        
        ⚠️ Порядок точек НИКОГДА не меняется
        
        Returns:
            List[Tuple[float, float]] - конструктивный контур с клёшом
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
        hem = self.hem_curve_points(F, E)

        # Сборка контура в строгом порядке
        contour = (
            waist +           # талия (3 точки)
            side[1:] +       # бок (2 точки, пропускаем B)
            hem[1:] +         # низ (2 точки, пропускаем F)
            [C_mid, A]        # середина и замыкание
        )

        return contour

    def get_segments(self) -> Dict[str, List[Tuple[float, float]]]:
        """
        Получить сегменты для визуального дебага
        
        Returns:
            Dict[str, List[Tuple[float, float]] - сегменты
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
            "hem": self.hem_curve_points(F, E),
            "center": [C_mid, A]
        }

    def debug_visualization(self, save_path: str = "output/skirt_constructive_hem_debug.png"):
        """
        🎨 Визуальный дебаг конструктивных кривых с клёшом
        
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
            title="Skirt Constructive – Hem Bulge",
            save_path=save_path
        )

    def export_dxf(self, filepath: str):
        """
        📁 DXF ЭКСПОРТ с BULGE для всех кривых
        
        Args:
            filepath: str - путь для сохранения
            
        Returns:
            Dict[str, Any] - результат экспорта
        """
        try:
            from ..cad.bulge_exporter import bulge_from_constructive_points, export_lwpolyline_dxf_with_bulge, validate_bulge_dxf
        except ImportError:
            # Для прямого запуска
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from agent.fashion.cad.bulge_exporter import bulge_from_constructive_points, export_lwpolyline_dxf_with_bulge, validate_bulge_dxf
        
        # Получаем точки в правильном порядке
        points = self.build_constructive_contour()
        
        # Вычисляем bulge для всех кривых
        bulges = bulge_from_constructive_points(points)
        
        # 🔢 Bulge для низа
        # Для низа нужно вычислить bulge отдельно, т.к. теперь 3 точки
        if len(points) >= 6:
            # F (точка 4) → hem_mid (новая) → E (точка 5)
            hem_points = self.hem_curve_points(
                (points[4][0], points[4][1]),  # F
                (points[5][0], points[5][1])   # E
            )
            # Заменяем сегмент низа
            if len(hem_points) == 3:
                # Вставляем hem_mid между F и E
                hem_mid = hem_points[1]
                # Обновляем bulge для точки F (индекс 4)
                bulges[4] = bulge_from_3_points(points[4], hem_mid, points[5])
        
        # Экспорт БЕЗ сортировки, сглаживания, реконструкции
        exported_path = export_lwpolyline_dxf_with_bulge(points, bulges, filepath)
        
        # Валидация
        validation = validate_bulge_dxf(exported_path)
        
        return {
            'success': validation['is_valid'],
            'filepath': exported_path,
            'points_count': len(points),
            'bulge_count': sum(1 for b in bulges if abs(b) > 0.001),
            'validation': validation
        }

    def validate_construction(self) -> Dict[str, Any]:
        """
        🔍 Валидация конструктивной модели с клёшом
        
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
        if len(points) < 9:  # теперь 9 точек с клёшом
            errors.append("Недостаточно точек для конструктивного контура с клёшом")
        
        # Проверка замыкания
        if points[0] != points[-1]:
            errors.append("Контур не замкнут")
        
        # Проверка клёша
        if abs(self.hem_out) > 0.1:
            warnings.append(f"Клёш низа: {self.hem_out} мм")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'points_count': len(points),
            'construction_params': {
                'side_out': self.side_out,
                'waist_depth': self.waist_depth,
                'hem_out': self.hem_out
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
            "waist_depth": self.waist_depth,
            "hem_out": self.hem_out
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkirtConstructiveHem':
        """
        Создание из словаря
        
        Args:
            data: Dict[str, Any] - параметры
            
        Returns:
            SkirtConstructiveHem - экземпляр модели
        """
        return cls(**data)


def build_constructive_skirt_hem(
    waist: float,
    hip: float,
    hip_height: float,
    length: float,
    waist_ease: float = 0.0,
    hip_ease: float = 0.0,
    side_out: float = 12.0,
    waist_depth: float = 10.0,
    hem_out: float = 0.0
) -> List[Tuple[float, float]]:
    """
    📐 Функция построения конструктивного контура юбки с клёшом
    
    Args:
        waist: float          # обхват талии
        hip: float           # обхват бедер
        hip_height: float    # высота бедер от талии
        length: float        # длина юбки
        waist_ease: float    # прибавка по талии
        hip_ease: float     # прибавка по бедрам
        side_out: float     # отклонение бока в зоне бедер (мм)
        waist_depth: float  # прогиб талии вниз (мм)
        hem_out: float     # клёш низа (мм)
        
    Returns:
        List[Tuple[float, float]] - конструктивный контур с клёшом
    """
    skirt = SkirtConstructiveHem(
        waist=waist,
        hip=hip,
        hip_height=hip_height,
        length=length,
        waist_ease=waist_ease,
        hip_ease=hip_ease,
        side_out=side_out,
        waist_depth=waist_depth,
        hem_out=hem_out
    )
    
    return skirt.build_constructive_contour()


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ SKIRT CONSTRUCTIVE HEM")
    print("=" * 50)
    
    # Создание конструктивной юбки с клёшом
    skirt = SkirtConstructiveHem(
        waist=720,
        hip=960,
        hip_height=180,
        length=650,
        waist_ease=20,
        hip_ease=40,
        side_out=14,
        waist_depth=8,
        hem_out=12  # клёш низа 12 мм
    )
    
    print("📊 Параметры юбки:")
    print(f"   Талия: {skirt.waist} + {skirt.waist_ease} = {skirt.waist + skirt.waist_ease}")
    print(f"   Бедра: {skirt.hip} + {skirt.hip_ease} = {skirt.hip + skirt.hip_ease}")
    print(f"   Высота бедер: {skirt.hip_height}")
    print(f"   Длина: {skirt.length}")
    print(f"   Отклонение бока: {skirt.side_out} мм")
    print(f"   Прогиб талии: {skirt.waist_depth} мм")
    print(f"   Клёш низа: {skirt.hem_out} мм")
    
    # Построение контура
    points = skirt.build_constructive_contour()
    print(f"\n📐 Конструктивный контур: {len(points)} точек")
    
    print("📍 Точки контура:")
    point_names = ['A', 'M1', 'B', 'M2', 'F', 'H_mid', 'E', 'C_mid', 'A']
    for i, (name, point) in enumerate(zip(point_names, points)):
        print(f"   {i} {name}: ({point[0]:.1f}, {point[1]:.1f})")
    
    # Валидация
    validation = skirt.validate_construction()
    print(f"\n🔍 Валидация:")
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
    print(f"\n📁 Экспорт DXF с bulge...")
    result = skirt.export_dxf("output/skirt_constructive_hem.dxf")
    
    if result['success']:
        print(f"   ✅ DXF создан: {result['filepath']}")
        print(f"   📊 Точек: {result['points_count']}")
        print(f"   🔄 Дуг: {result['bulge_count']}")
        
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
    
    print(f"\n✅ SkirtConstructiveHem готов!")
