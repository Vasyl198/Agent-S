"""
БАЗОВАЯ МОДЕЛЬ: SkirtPattern
===========================

Параметрическая модель юбки как объекта.
Язык конструктора, а не программиста.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import math


@dataclass
class SkirtPattern:
    """
    Базовая модель юбки с параметрической геометрией.
    
    Args:
        waist_width: float      # ширина по талии
        height: float           # длина юбки
        waist_curve: float      # прогиб талии (мм)
        side_curvature: float   # 0..1 - кривизна бока
        hem_curve: float = 0.0  # прогиб низа (мм)
    """
    waist_width: float
    height: float
    waist_curve: float
    side_curvature: float
    hem_curve: float = 0.0

    def get_waist_curve(self, n: int = 10) -> List[Tuple[float, float]]:
        """
        🔴 Талия — всегда контролируемая
        
        Args:
            n: int - количество точек
            
        Returns:
            List[Tuple[float, float]] - точки талии
        """
        x0 = -self.waist_width
        x1 = 0
        y = self.height

        return arc_points(
            (x0, y),
            (x1, y),
            depth=self.waist_curve,
            n=n
        )

    def get_side_curve(self, n: int = 20) -> List[Tuple[float, float]]:
        """
        🔵 Бок — управляемый радиус
        
        Args:
            n: int - количество точек
            
        Returns:
            List[Tuple[float, float]] - точки бока
        """
        return bezier_curve(
            start=(0, self.height),
            control=(self.side_curvature * self.waist_width, self.height / 2),
            end=(0, 0),
            n=n
        )

    def get_hem_curve(self, n: int = 10) -> List[Tuple[float, float]]:
        """
        🟢 Низ — дуга или прямая
        
        Args:
            n: int - количество точек
            
        Returns:
            List[Tuple[float, float]] - точки низа
        """
        return arc_points(
            (0, 0),
            (-self.waist_width, 0),
            depth=-self.hem_curve,
            n=n
        )

    def build_contour(self) -> List[Tuple[float, float]]:
        """
        🟢 ШАГ 3 — Сборка КОНТУРА (а не «точек»)
        
        Returns:
            List[Tuple[float, float]] - замкнутый контур CCW
        """
        waist = self.get_waist_curve()
        side = self.get_side_curve()
        hem = self.get_hem_curve()

        contour = (
            waist +
            side[1:] +      # пропускаем первую точку (дубликат)
            hem[1:]         # пропускаем первую точку (дубликат)
        )

        return close_contour_ccw(contour)

    def get_segments(self) -> Dict[str, List[Tuple[float, float]]]:
        """
        Получить сегменты для визуального дебага
        
        Returns:
            Dict[str, List[Tuple[float, float]]] - сегменты
        """
        return {
            "waist": self.get_waist_curve(),
            "side": self.get_side_curve(),
            "hem": self.get_hem_curve()
        }

    def debug_visualization(self, save_path: str = "output/skirt_parametric.png"):
        """
        🟢 ШАГ 4 — ВИЗУАЛЬНЫЙ ДЕБАГ
        
        Args:
            save_path: str - путь для сохранения
        """
        from ..cad.visual_debug import debug_draw_contour
        
        contour = self.build_contour()
        segments = self.get_segments()
        
        debug_draw_contour(
            points=contour,
            segments=segments,
            title="SkirtPattern – Parametric Geometry",
            save_path=save_path
        )

    def export_dxf(self, filepath: str, enable_curve_reconstruction: bool = False):
        """
        Экспорт в DXF через LWPOLYLINE
        
        Args:
            filepath: str - путь для сохранения
            enable_curve_reconstruction: bool - включить сглаживание
        """
        from ..cad.proper_dxf_exporter import export_proper_dxf
        
        # Создаем Mock CAD с нашим контуром
        class ParametricCAD:
            def __init__(self, contour):
                self.lines = []
                self.polylines = [contour]
        
        contour = self.build_contour()
        cad = ParametricCAD(contour)
        
        result = export_proper_dxf(
            cad,
            filepath,
            debug=False,
            enable_curve_reconstruction=enable_curve_reconstruction
        )
        
        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертация в словарь для ML
        
        Returns:
            Dict[str, Any] - параметры модели
        """
        return {
            "waist_width": self.waist_width,
            "height": self.height,
            "waist_curve": self.waist_curve,
            "side_curvature": self.side_curvature,
            "hem_curve": self.hem_curve
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkirtPattern':
        """
        Создание из словаря
        
        Args:
            data: Dict[str, Any] - параметры
            
        Returns:
            SkirtPattern - экземпляр модели
        """
        return cls(**data)

    def scale(self, factor: float) -> 'SkirtPattern':
        """
        Масштабирование модели
        
        Args:
            factor: float - коэффициент масштабирования
            
        Returns:
            SkirtPattern - новая масштабированная модель
        """
        return SkirtPattern(
            waist_width=self.waist_width * factor,
            height=self.height * factor,
            waist_curve=self.waist_curve * factor,
            side_curvature=self.side_curvature,
            hem_curve=self.hem_curve * factor
        )


# Вспомогательные функции геометрии
def arc_points(start: Tuple[float, float], 
               end: Tuple[float, float], 
               depth: float, 
               n: int = 10) -> List[Tuple[float, float]]:
    """
    Генерация точек дуги
    
    Args:
        start: Tuple[float, float] - начальная точка
        end: Tuple[float, float] - конечная точка
        depth: float - глубина прогиба
        n: int - количество точек
        
    Returns:
        List[Tuple[float, float]] - точки дуги
    """
    points = []
    x0, y0 = start
    x1, y1 = end
    
    # Центр дуги
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    
    # Радиус и угол
    chord_length = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
    if chord_length == 0:
        return [start, end]
    
    # Высота дуги
    sagitta = depth
    
    # Радиус дуги
    radius = (chord_length**2 + 4 * sagitta**2) / (8 * abs(sagitta)) if sagitta != 0 else float('inf')
    
    # Угол дуги
    if radius != float('inf'):
        angle = 2 * math.asin(chord_length / (2 * radius))
    else:
        angle = 0
    
    # Начальный угол
    start_angle = math.atan2(y0 - cy, x0 - cx)
    
    # Генерация точек
    for i in range(n):
        if n == 1:
            t = 0
        else:
            t = i / (n - 1)
        
        if radius != float('inf'):
            current_angle = start_angle + angle * t
            x = cx + radius * math.cos(current_angle)
            y = cy + radius * math.sin(current_angle)
        else:
            # Прямая линия
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
        
        points.append((x, y))
    
    return points


def bezier_curve(start: Tuple[float, float], 
                 control: Tuple[float, float], 
                 end: Tuple[float, float], 
                 n: int = 20) -> List[Tuple[float, float]]:
    """
    Генерация точек кривой Безье
    
    Args:
        start: Tuple[float, float] - начальная точка
        control: Tuple[float, float] - контрольная точка
        end: Tuple[float, float] - конечная точка
        n: int - количество точек
        
    Returns:
        List[Tuple[float, float]] - точки кривой
    """
    points = []
    x0, y0 = start
    x1, y1 = control
    x2, y2 = end
    
    for i in range(n):
        if n == 1:
            t = 0
        else:
            t = i / (n - 1)
        
        # Квадратичная кривая Безье
        x = (1-t)**2 * x0 + 2*(1-t)*t * x1 + t**2 * x2
        y = (1-t)**2 * y0 + 2*(1-t)*t * y1 + t**2 * y2
        
        points.append((x, y))
    
    return points


def close_contour_ccw(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Замыкание контура в CCW порядке
    
    Args:
        points: List[Tuple[float, float]] - точки контура
        
    Returns:
        List[Tuple[float, float]] - замкнутый контур
    """
    if len(points) < 3:
        return points
    
    # Проверяем, нужно ли замыкать
    if points[0] != points[-1]:
        points = points + [points[0]]
    
    return points


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ SKIRTPATTERN")
    print("=" * 40)
    
    # Создание базовой модели
    skirt = SkirtPattern(
        waist_width=96.0,
        height=65.0,
        waist_curve=2.0,
        side_curvature=0.42,
        hem_curve=1.0
    )
    
    print(f"📊 Параметры юбки:")
    print(f"   Ширина талии: {skirt.waist_width} мм")
    print(f"   Длина: {skirt.height} мм")
    print(f"   Прогиб талии: {skirt.waist_curve} мм")
    print(f"   Кривизна бока: {skirt.side_curvature}")
    print(f"   Прогиб низа: {skirt.hem_curve} мм")
    
    # Построение контура
    contour = skirt.build_contour()
    print(f"\n📐 Контур построен: {len(contour)} точек")
    
    # Визуальный дебаг
    print(f"\n🎨 Визуальный дебаг...")
    skirt.debug_visualization()
    
    # Экспорт DXF
    print(f"\n📁 Экспорт DXF...")
    result = skirt.export_dxf("output/skirt_pattern.dxf")
    
    if result['success']:
        print(f"   ✅ DXF создан: {result['filepath']}")
        print(f"   📊 Точек: {result['original_points']}")
    else:
        print(f"   ❌ Ошибка: {result['error']}")
    
    # ML параметры
    ml_params = skirt.to_dict()
    print(f"\n🤖 ML параметры:")
    for key, value in ml_params.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ SkirtPattern готов!")
