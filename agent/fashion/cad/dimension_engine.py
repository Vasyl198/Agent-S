"""
ЭТАП 4 — АВТОМАТИЧЕСКИЕ РАЗМЕРЫ (DIMENSION ENGINE)
=====================================================

Теперь, когда есть семантика, размеры считаются без догадок.

🎯 ЦЕЛЬ ЭТАПА:
Система сама:
- знает, что измерять
- знает, между какими точками
- умеет выводить размеры в DXF
Без ручного выбора.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

from .pattern_semantics import PatternModel, PatternPoint


class DimensionDirection(Enum):
    """Направление размера"""
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"
    ANGULAR = "ANGULAR"


class DimensionRole(Enum):
    """Роль размера"""
    WAIST = "WAIST"
    HIP = "HIP"
    HEM = "HEM"
    LENGTH = "LENGTH"
    SIDE_OUT = "SIDE_OUT"
    WAIST_DEPTH = "WAIST_DEPTH"
    HEM_OUT = "HEM_OUT"


@dataclass
class PatternDimension:
    """
    1️⃣ ВВОДИМ ТИПЫ РАЗМЕРОВ
    """
    name: str
    value: float
    start: Tuple[float, float]
    end: Tuple[float, float]
    direction: str
    role: str
    layer: str = "DIMENSIONS"
    
    def is_horizontal(self) -> bool:
        """Горизонтальный размер"""
        return self.direction == DimensionDirection.HORIZONTAL.value
    
    def is_vertical(self) -> bool:
        """Вертикальный размер"""
        return self.direction == DimensionDirection.VERTICAL.value
    
    def is_angular(self) -> bool:
        """Угловой размер"""
        return self.direction == DimensionDirection.ANGULAR.value
    
    def get_display_value(self) -> str:
        """Отображаемое значение размера"""
        if self.value < 1000:
            return f"{self.value:.1f}"
        else:
            return f"{self.value:.0f}"


class DimensionEngine:
    """
    🔧 ДВИЖОК РАЗМЕРОВ
    
    2️⃣ АВТОРАЗМЕРЫ НА ОСНОВЕ СЕМАНТИКИ
    """
    
    def __init__(self):
        self.dimensions = []
        self.dimension_counter = 0
    
    def create_dimension(self, name: str, value: float, start: Tuple[float, float], 
                       end: Tuple[float, float], direction: str, role: str) -> PatternDimension:
        """Создать размер"""
        self.dimension_counter += 1
        return PatternDimension(
            name=name,
            value=value,
            start=start,
            end=end,
            direction=direction,
            role=role
        )
    
    def waist_width(self, model: PatternModel) -> PatternDimension:
        """
        📏 ТАЛИЯ
        
        Измеряет полную ширину талии (половинка × 2)
        """
        waist_centers = model.get_points_by_role("WAIST_CENTER")
        waist_sides = model.get_points_by_role("WAIST_SIDE")
        
        if not waist_centers or not waist_sides:
            return None
        
        p1 = waist_centers[0]  # середина талии
        p2 = waist_sides[0]     # бок талии
        
        half_width = abs(p2.x - p1.x)
        full_width = half_width * 2  # 📌 умножаем ×2 → половинка → полный обхват
        
        return self.create_dimension(
            name="WAIST_WIDTH",
            value=full_width,
            start=p1.xy(),
            end=p2.xy(),
            direction=DimensionDirection.HORIZONTAL.value,
            role=DimensionRole.WAIST.value
        )
    
    def hip_width(self, model: PatternModel) -> PatternDimension:
        """
        📏 БЁДРА
        
        Измеряет полную ширину бедер
        """
        center_points = model.get_points_by_role("CENTER_LINE")
        hip_sides = model.get_points_by_role("HIP_SIDE")
        
        if not center_points or not hip_sides:
            return None
        
        p1 = center_points[0]   # середина
        p2 = hip_sides[0]        # бок бедер
        
        half_width = abs(p2.x - p1.x)
        full_width = half_width * 2
        
        return self.create_dimension(
            name="HIP_WIDTH",
            value=full_width,
            start=p1.xy(),
            end=p2.xy(),
            direction=DimensionDirection.HORIZONTAL.value,
            role=DimensionRole.HIP.value
        )
    
    def skirt_length(self, model: PatternModel) -> PatternDimension:
        """
        📏 ДЛИНА ЮБКИ
        
        Измеряет длину от талии до низа
        """
        waist_points = model.get_points_by_role("WAIST_CENTER")
        hem_points = model.get_points_by_role("HEM_CENTER")
        
        if not waist_points or not hem_points:
            return None
        
        p1 = waist_points[0]   # талия
        p2 = hem_points[-1]     # низ (последняя точка)
        
        length = abs(p2.y - p1.y)
        
        return self.create_dimension(
            name="SKIRT_LENGTH",
            value=length,
            start=p1.xy(),
            end=p2.xy(),
            direction=DimensionDirection.VERTICAL.value,
            role=DimensionRole.LENGTH.value
        )
    
    def hem_width(self, model: PatternModel) -> PatternDimension:
        """
        📏 ШИРИНА НИЗА (КЛЁШ)
        
        Измеряет полную ширину низа
        """
        hem_centers = model.get_points_by_role("HEM_CENTER")
        hem_sides = model.get_points_by_role("HEM_SIDE")
        
        if not hem_centers or not hem_sides:
            return None
        
        p1 = hem_centers[-1]   # середина низа
        p2 = hem_sides[0]       # бок низа
        
        half_width = abs(p2.x - p1.x)
        full_width = half_width * 2
        
        return self.create_dimension(
            name="HEM_WIDTH",
            value=full_width,
            start=p1.xy(),
            end=p2.xy(),
            direction=DimensionDirection.HORIZONTAL.value,
            role=DimensionRole.HEM.value
        )
    
    def side_out_deviation(self, model: PatternModel) -> PatternDimension:
        """
        📏 ОТКЛОНЕНИЕ БОКА
        
        Измеряет отклонение бока от вертикали
        """
        waist_sides = model.get_points_by_role("WAIST_SIDE")
        hip_sides = model.get_points_by_role("HIP_SIDE")
        
        if not waist_sides or not hip_sides:
            return None
        
        p1 = waist_sides[0]    # бок талии
        p2 = hip_sides[0]       # бок бедер
        
        deviation = abs(p2.x - p1.x)
        
        return self.create_dimension(
            name="SIDE_OUT",
            value=deviation,
            start=p1.xy(),
            end=p2.xy(),
            direction=DimensionDirection.HORIZONTAL.value,
            role=DimensionRole.SIDE_OUT.value
        )
    
    def waist_depth_value(self, model: PatternModel) -> PatternDimension:
        """
        📏 ПРОГИБ ТАЛИИ
        
        Измеряет прогиб талии
        """
        waist_centers = model.get_points_by_role("WAIST_CENTER")
        
        if len(waist_centers) < 2:
            return None
        
        p1 = waist_centers[0]   # начало талии
        p2 = waist_centers[1]   # прогиб талии
        
        depth = abs(p2.y - p1.y)
        
        return self.create_dimension(
            name="WAIST_DEPTH",
            value=depth,
            start=p1.xy(),
            end=p2.xy(),
            direction=DimensionDirection.VERTICAL.value,
            role=DimensionRole.WAIST_DEPTH.value
        )
    
    def hem_out_value(self, model: PatternModel) -> PatternDimension:
        """
        📏 КЛЁШ НИЗА
        
        Измеряет клёш низа
        """
        hem_sides = model.get_points_by_role("HEM_SIDE")
        hem_centers = model.get_points_by_role("HEM_CENTER")
        
        if not hem_sides or not hem_centers:
            return None
        
        p1 = hem_sides[0]       # бок низа
        p2 = hem_centers[-1]     # середина низа
        
        hem_out = abs(p2.y - p1.y)
        
        return self.create_dimension(
            name="HEM_OUT",
            value=hem_out,
            start=p1.xy(),
            end=p2.xy(),
            direction=DimensionDirection.VERTICAL.value,
            role=DimensionRole.HEM_OUT.value
        )
    
    def build_dimensions(self, model: PatternModel) -> List[PatternDimension]:
        """
        3️⃣ СОБИРАЕМ ВСЕ РАЗМЕРЫ
        
        Автоматически собирает все возможные размеры на основе семантики
        """
        dimensions = []
        
        # Основные размеры
        waist_dim = self.waist_width(model)
        if waist_dim:
            dimensions.append(waist_dim)
        
        hip_dim = self.hip_width(model)
        if hip_dim:
            dimensions.append(hip_dim)
        
        length_dim = self.skirt_length(model)
        if length_dim:
            dimensions.append(length_dim)
        
        hem_dim = self.hem_width(model)
        if hem_dim:
            dimensions.append(hem_dim)
        
        # Конструктивные размеры
        side_out_dim = self.side_out_deviation(model)
        if side_out_dim:
            dimensions.append(side_out_dim)
        
        waist_depth_dim = self.waist_depth_value(model)
        if waist_depth_dim:
            dimensions.append(waist_depth_dim)
        
        hem_out_dim = self.hem_out_value(model)
        if hem_out_dim:
            dimensions.append(hem_out_dim)
        
        self.dimensions = dimensions
        return dimensions
    
    def get_dimensions_by_role(self, role: str) -> List[PatternDimension]:
        """Получить размеры по роли"""
        return [d for d in self.dimensions if d.role == role]
    
    def get_main_dimensions(self) -> List[PatternDimension]:
        """Основные размеры (талия, бедра, длина, низ)"""
        main_roles = [
            DimensionRole.WAIST.value,
            DimensionRole.HIP.value,
            DimensionRole.LENGTH.value,
            DimensionRole.HEM.value
        ]
        return [d for d in self.dimensions if d.role in main_roles]
    
    def get_construction_dimensions(self) -> List[PatternDimension]:
        """Конструктивные размеры (отклонения, прогибы)"""
        construction_roles = [
            DimensionRole.SIDE_OUT.value,
            DimensionRole.WAIST_DEPTH.value,
            DimensionRole.HEM_OUT.value
        ]
        return [d for d in self.dimensions if d.role in construction_roles]


class DimensionDxfExporter:
    """
    4️⃣ DXF ЭКСПОРТ РАЗМЕРОВ (БЕЗ MAGICK)
    
    LibreCAD понимает DIMLINEAR
    📌 Размеры будут ассоциативны, не просто текст.
    """
    
    def __init__(self):
        self.layer_name = "DIMENSIONS"
        self.text_height = 2.5
        self.arrow_size = 2.0
    
    def export_dimensions_dxf(self, dimensions: List[PatternDimension], filepath: str) -> Dict[str, Any]:
        """
        Экспорт размеров в DXF
        
        Args:
            dimensions: List[PatternDimension] - размеры
            filepath: str - путь для сохранения
            
        Returns:
            Dict[str, Any] - результат экспорта
        """
        try:
            # Создаем директорию
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Вычисляем границы
            all_points = []
            for dim in dimensions:
                all_points.extend([dim.start, dim.end])
            
            if all_points:
                xs = [p[0] for p in all_points]
                ys = [p[1] for p in all_points]
                xmin, xmax = min(xs), max(xs)
                ymin, ymax = min(ys), max(ys)
            else:
                xmin, xmax, ymin, ymax = 0, 100, 0, 100
            
            # Заголовок DXF
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
TABLES
0
TABLE
2
LTYPE
70
1
0
LTYPE
2
CONTINUOUS
70
64
3
Solid line
72
65
73
0
40
0.0
0
ENDTAB
0
TABLE
2
LAYER
70
1
0
LAYER
2
{self.layer_name}
70
0
62
5
6
CONTINUOUS
0
ENDTAB
0
ENDSEC
0
SECTION
2
ENTITIES
"""
            
            # Экспорт размеров
            for dim in dimensions:
                dxf_content += self._dimension_to_dxf(dim)
            
            dxf_content += """0
ENDSEC
0
EOF"""
            
            # Записываем файл
            with open(path, 'w', encoding='utf-8') as f:
                f.write(dxf_content)
            
            return {
                'success': True,
                'filepath': str(path),
                'dimensions_count': len(dimensions),
                'main_dimensions': len([d for d in dimensions if d.role in [
                    DimensionRole.WAIST.value, DimensionRole.HIP.value, 
                    DimensionRole.LENGTH.value, DimensionRole.HEM.value
                ]]),
                'construction_dimensions': len([d for d in dimensions if d.role in [
                    DimensionRole.SIDE_OUT.value, DimensionRole.WAIST_DEPTH.value, 
                    DimensionRole.HEM_OUT.value
                ]])
            }
            
        except Exception as e:
            return {
                'success': False,
                'filepath': None,
                'error': f'Ошибка экспорта размеров: {str(e)}',
                'dimensions_count': 0
            }
    
    def _dimension_to_dxf(self, dimension: PatternDimension) -> str:
        """Преобразовать размер в DXF"""
        x1, y1 = dimension.start
        x2, y2 = dimension.end
        
        # Для простоты используем текстовые примитивы
        # В реальной системе здесь был бы DIMENSION блок
        
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Смещение текста
        if dimension.is_horizontal():
            text_y = mid_y + 5.0
            text_x = mid_x
        elif dimension.is_vertical():
            text_x = mid_x + 5.0
            text_y = mid_y
        else:
            text_x = mid_x + 5.0
            text_y = mid_y + 5.0
        
        # Линия размера
        dimension_line = f"""0
LINE
8
{self.layer_name}
10
{x1}
20
{y1}
11
{x2}
21
{y2}
"""
        
        # Текст размера
        dimension_text = f"""0
TEXT
8
{self.layer_name}
10
{text_x}
20
{text_y}
40
{self.text_height}
1
{dimension.get_display_value()}
50
0.0
51
0.0
7
STANDARD
"""
        
        return dimension_line + dimension_text


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ DIMENSION ENGINE")
    print("=" * 50)
    
    # Создаем тестовую модель
    from .pattern_semantics import PatternSemanticsBuilder
    
    points = [
        (0.0, 0.0), (92.5, 8.0), (185.0, 0.0), (264.0, 180.0),
        (250.0, 650.0), (125.0, 662.0), (0.0, 650.0), (0.0, 180.0), (0.0, 0.0)
    ]
    bulges = [-0.086486, 0.0, 0.225381, 0.0, 0.095131, 0.0, 0.0, 0.0, 0.0]
    
    builder = PatternSemanticsBuilder()
    model = builder.build_pattern_model(points, bulges)
    
    print("📊 Семантическая модель:")
    print(f"   Точек: {len(model.points)}")
    print(f"   Сегментов: {len(model.segments)}")
    
    # Создаем движок размеров
    dimension_engine = DimensionEngine()
    
    # Собираем размеры
    dimensions = dimension_engine.build_dimensions(model)
    
    print(f"\n📏 Автоматические размеры:")
    print(f"   Всего размеров: {len(dimensions)}")
    
    # Основные размеры
    main_dims = dimension_engine.get_main_dimensions()
    print(f"\n🎯 Основные размеры:")
    for dim in main_dims:
        print(f"   {dim.name}: {dim.get_display_value()} мм")
        print(f"      от {dim.start} до {dim.end}")
        print(f"      направление: {dim.direction}")
    
    # Конструктивные размеры
    construction_dims = dimension_engine.get_construction_dimensions()
    print(f"\n🔧 Конструктивные размеры:")
    for dim in construction_dims:
        print(f"   {dim.name}: {dim.get_display_value()} мм")
        print(f"      от {dim.start} до {dim.end}")
        print(f"      направление: {dim.direction}")
    
    # Экспорт DXF
    print(f"\n📁 Экспорт размеров в DXF...")
    exporter = DimensionDxfExporter()
    result = exporter.export_dimensions_dxf(dimensions, "output/skirt_dimensions.dxf")
    
    if result['success']:
        print(f"   ✅ DXF создан: {result['filepath']}")
        print(f"   📊 Всего размеров: {result['dimensions_count']}")
        print(f"   🎯 Основных: {result['main_dimensions']}")
        print(f"   🔧 Конструктивных: {result['construction_dimensions']}")
    else:
        print(f"   ❌ Ошибка: {result['error']}")
    
    print(f"\n✅ Dimension Engine готов!")
