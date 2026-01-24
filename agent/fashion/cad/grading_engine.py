"""
ЭТАП 5 — ГРАДАЦИЯ (SIZE GRADING ENGINE)
==========================================

Это критический этап, который отличает:
❌ «чертёж»
✅ производственное лекало

Мы будем делать настоящую градацию, как в Lectra / Gerber.

🎯 ЦЕЛЬ ЭТАПА:
Система должна уметь:
- брать базовый размер (Base size)
- генерировать XS / S / M / L / XL
- НЕ ломать дуги
- НЕ ломать пропорции
- смещать точки по ролям, а не «как попало»

🧠 КЛЮЧЕВОЙ ПРИНЦИП (ОЧЕНЬ ВАЖНО):
❌ Градация ≠ масштабирование
❌ Градация ≠ offset
✅ Градация = контролируемые смещения точек по направлениям
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

from .pattern_semantics import PatternModel, PatternPoint, PatternSegment


class SizeStep(Enum):
    """Шаги градации"""
    XS = -2
    S = -1
    M = 0
    L = 1
    XL = 2


@dataclass
class GradeRule:
    """Правило градации для измерения"""
    x_increment: float  # приращение по X на полразмер
    y_increment: float  # приращение по Y на полразмер


class GradingEngine:
    """
    🔧 ДВИЖОК ГРАДАЦИИ
    
    Профессиональная градация как в Lectra / Gerber
    """
    
    # 1️⃣ ВВОДИМ ТАБЛИЦУ ГРАДАЦИИ
    GRADE_RULES = {
        "WAIST": GradeRule(x_increment=5.0, y_increment=0.0),      # 📌 Это ПРИРОСТ НА ПОЛРАЗМЕР (½ обхвата)
        "HIP": GradeRule(x_increment=6.0, y_increment=0.0),        # 📌 ½ обхвата бедер
        "HEM": GradeRule(x_increment=7.0, y_increment=0.0),        # 📌 ½ обхвата низа
        "LENGTH": GradeRule(x_increment=0.0, y_increment=3.0)      # 📌 длина юбки
    }
    
    # 2️⃣ ПРАВИЛА СМЕЩЕНИЯ ПО РОЛЯМ ТОЧЕК
    POINT_GRADE_BEHAVIOR = {
        "WAIST_CENTER": {"x_factor": 0.0, "y_factor": 0.0},    # 📌 Центр никогда не идет по X
        "WAIST_SIDE": {"x_factor": 1.0, "y_factor": 0.0},      # 📌 Бок двигается по X
        "HIP_SIDE": {"x_factor": 1.0, "y_factor": 0.0},        # 📌 Бок двигается по X
        "HEM_SIDE": {"x_factor": 1.0, "y_factor": 0.0},        # 📌 Бок двигается по X
        "HEM_CENTER": {"x_factor": 0.0, "y_factor": 0.0},    # 📌 Центр не двигается по X
        "CENTER_LINE": {"x_factor": 0.0, "y_factor": 1.0},     # 📌 Длина — только по Y
    }
    
    def __init__(self):
        self.graded_models = {}
        self.size_counter = 0
    
    def get_grade_rule(self, measurement: str) -> Optional[GradeRule]:
        """Получить правило градации для измерения"""
        return self.GRADE_RULES.get(measurement)
    
    def get_point_behavior(self, role: str) -> Dict[str, float]:
        """Получить поведение точки при градации"""
        return self.POINT_GRADE_BEHAVIOR.get(role, {"x_factor": 0.0, "y_factor": 0.0})
    
    def grade_point(self, point: PatternPoint, step: int) -> PatternPoint:
        """
        3️⃣ ФУНКЦИЯ ГРАДАЦИИ ОДНОЙ ТОЧКИ
        """
        Градация одной точки
        
        Args:
            point: PatternPoint - исходная точка
            step: int - шаг градации (-2, -1, 0, +1, +2)
            
        Returns:
            PatternPoint - градированная точка
        """
        behavior = self.get_point_behavior(point.role)
        
        # Определяем основное измерение для точки
        measurement = self._get_measurement_for_point(point.role)
        grade_rule = self.get_grade_rule(measurement)
        
        if not grade_rule:
            # Если нет правила, точка не двигается
            return PatternPoint(
                name=f"{point.name}_G{step}",
                role=point.role,
                x=point.x,
                y=point.y
            )
        
        # Вычисляем смещение
        dx = (behavior["x_factor"] * grade_rule.x_increment * step)
        dy = (behavior["y_factor"] * grade_rule.y_increment * step)
        
        return PatternPoint(
            name=f"{point.name}_G{step}",
            role=point.role,
            x=point.x + dx,
            y=point.y + dy
        )
    
    def _get_measurement_for_point(self, role: str) -> str:
        """Определить измерение для точки"""
        if "WAIST" in role:
            return "WAIST"
        elif "HIP" in role:
            return "HIP"
        elif "HEM" in role:
            return "HEM"
        elif "CENTER" in role:
            return "LENGTH"
        else:
            return "WAIST"  # по умолчанию
    
    def 4️⃣ ГРАДАЦИЯ ВСЕГО ЛЕКАЛА:
    def grade_pattern(self, model: PatternModel, step: int) -> PatternModel:
        """
        Градация всего лекала
        
        Args:
            model: PatternModel - базовая модель
            step: int - шаг градации
            
        Returns:
            PatternModel - градированная модель
        """
        # Градируем все точки
        new_points = [self.grade_point(p, step) for p in model.points]
        
        # ⚠️ ВАЖНО: сегменты копируем БЕЗ ИЗМЕНЕНИЯ bulge
        new_segments = []
        for seg in model.segments:
            # Находим соответствующие градированные точки
            p1 = next((p for p in new_points if p.role == seg.start.role), seg.start)
            p2 = next((p for p in new_points if p.role == seg.end.role), seg.end)
            
            new_segments.append(PatternSegment(
                start=p1,
                end=p2,
                bulge=seg.bulge,  # 📌 Bulge НЕ ТРОГАЕМ — дуги сохраняются идеально
                role=seg.role
            ))
        
        return PatternModel(points=new_points, segments=new_segments)
    
    def 5️⃣ ГЕНЕРАЦИЯ РАЗМЕРНОГО РЯДА:
    def generate_size_set(self, base_model: PatternModel) -> Dict[str, PatternModel]:
        """
        Генерация размерного ряда
        
        Args:
            base_model: PatternModel - базовая модель (обычно M)
            
        Returns:
            Dict[str, PatternModel] - словарь размеров
        """
        size_set = {}
        
        for size_name, step in [
            ("XS", SizeStep.XS.value),
            ("S", SizeStep.S.value),
            ("M", SizeStep.M.value),
            ("L", SizeStep.L.value),
            ("XL", SizeStep.XL.value)
        ]:
            graded_model = self.grade_pattern(base_model, step)
            size_set[size_name] = graded_model
            self.size_counter += 1
        
        return size_set
    
    def get_size_comparison(self, base_model: PatternModel) -> Dict[str, Any]:
        """
        Сравнить размеры для анализа градации
        
        Args:
            base_model: PatternModel - базовая модель
            
        Returns:
            Dict[str, Any] - анализ размеров
        """
        size_set = self.generate_size_set(base_model)
        
        comparison = {}
        
        for size_name, model in size_set.items():
            # Измеряем ключевые параметры
            from .dimension_engine import DimensionEngine
            dim_engine = DimensionEngine()
            dimensions = dim_engine.build_dimensions(model)
            
            main_dims = dim_engine.get_main_dimensions()
            
            size_info = {
                "model": model,
                "dimensions": {dim.name: dim.value for dim in main_dims}
            }
            
            comparison[size_name] = size_info
        
        return comparison


class GradingDxfExporter:
    """
    6️⃣ DXF ЭКСПОРТ ГРАДАЦИИ
    
    💡 Профессиональный вариант:
    - один DXF
    - каждый размер — свой слой
    """
    
    # 💡 SIZE_LAYER_MAP:
    SIZE_LAYER = {
        "XS": "SIZE_XS",
        "S": "SIZE_S",
        "M": "SIZE_M",
        "L": "SIZE_L",
        "XL": "SIZE_XL"
    }
    
    # Цвета слоев для разных размеров
    LAYER_COLORS = {
        "SIZE_XS": 1,   # Красный
        "SIZE_S": 2,    # Желтый
        "SIZE_M": 3,    # Зеленый
        "SIZE_L": 4,    # Голубой
        "SIZE_XL": 5    # Синий
    }
    
    def __init__(self):
        self.layer_map = self.SIZE_LAYER.copy()
        self.layer_colors = self.LAYER_COLORS.copy()
    
    def export_grading_dxf(self, size_set: Dict[str, PatternModel], filepath: str) -> Dict[str, Any]:
        """
        Экспорт размерного ряда в один DXF
        
        Args:
            size_set: Dict[str, PatternModel] - размерный ряд
            filepath: str - путь для сохранения
            
        Returns:
            Dict[str, Any] - результат экспорта
        """
        try:
            # Создаем директорию
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Собираем все точки для вычисления границ
            all_points = []
            for model in size_set.values():
                all_points.extend(model.points)
            
            # Вычисляем границы
            if all_points:
                xs = [p.x for p in all_points]
                ys = [p.y for p in all_points]
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
{len(self.layer_map)}
"""
            
            # Описание слоев
            for size_name, layer_name in self.layer_map.items():
                if size_name in size_set:
                    color = self.layer_colors.get(layer_name, 7)
                    dxf_content += f"""0
LAYER
2
{layer_name}
70
0
62
{color}
6
CONTINUOUS
"""
            
            dxf_content += """0
ENDTAB
0
ENDSEC
0
SECTION
2
ENTITIES
"""
            
            # Экспорт каждого размера в свой слой
            for size_name, model in size_set.items():
                layer_name = self.layer_map.get(size_name, "SIZE_MISC")
                
                # Экспорт сегментов
                for segment in model.segments:
                    dxf_content += self._segment_to_dxf(segment, layer_name)
            
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
                'sizes_exported': list(size_set.keys()),
                'total_segments': sum(len(m.segments) for m in size_set.values()),
                'layers_used': [self.layer_map[s] for s in size_set.keys() if s in self.layer_map]
            }
            
        except Exception as e:
            return {
                'success': False,
                'filepath': None,
                'error': f'Ошибка экспорта градации: {str(e)}',
                'sizes_exported': [],
                'total_segments': 0
            }
    
    def _segment_to_dxf(self, segment: PatternSegment, layer: str) -> str:
        """Преобразовать сегмент в DXF"""
        
        # Для дуги используем LWPOLYLINE с bulge
        if segment.is_arc():
            return f"""0
LWPOLYLINE
8
{layer}
90
2
70
0
10
{segment.start.x}
20
{segment.start.y}
42
{segment.bulge}
10
{segment.end.x}
20
{segment.end.y}
"""
        else:
            # Для линии тоже используем LWPOLYLINE
            return f"""0
LWPOLYLINE
8
{layer}
90
2
70
0
10
{segment.start.x}
20
{segment.start.y}
42
0.0
10
{segment.end.x}
20
{segment.end.y}
"""
    
    def export_separated_sizes_dxf(self, size_set: Dict[str, PatternModel], base_filepath: str) -> Dict[str, Any]:
        """
        Экспорт отдельных DXF файлов для каждого размера
        
        Args:
            size_set: Dict[str, PatternModel] - размерный ряд
            base_filepath: str - базовый путь (без расширения)
            
        Returns:
            Dict[str, Any] - результат экспорта
        """
        results = {}
        
        for size_name, model in size_set.items():
            filepath = f"{base_filepath}_{size_name.lower()}.dxf"
            single_size_set = {size_name: model}
            result = self.export_grading_dxf(single_size_set, filepath)
            results[size_name] = result
        
        return {
            'success': all(r['success'] for r in results.values()),
            'sizes': results,
            'base_filepath': base_filepath
        }


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ GRADING ENGINE")
    print("=" * 50)
    
    # Создаем тестовую базовую модель
    from .pattern_semantics import PatternSemanticsBuilder
    
    points = [
        (0.0, 0.0), (92.5, 8.0), (185.0, 0.0), (264.0, 180.0),
        (250.0, 650.0), (125.0, 662.0), (0.0, 650.0), (0.0, 180.0), (0.0, 0.0)
    ]
    bulges = [-0.086486, 0.0, 0.225381, 0.0, 0.095131, 0.0, 0.0, 0.0, 0.0]
    
    builder = PatternSemanticsBuilder()
    base_model = builder.build_pattern_model(points, bulges)
    
    print("📊 Базовая модель (M):")
    print(f"   Точек: {len(base_model.points)}")
    print(f"   Сегментов: {len(base_model.segments)}")
    print(f"   Дуг: {base_model.get_arc_count()}")
    
    # Создаем движок градации
    grading_engine = GradingEngine()
    
    # Генерируем размерный ряд
    print(f"\n🔧 Генерация размерного ряда...")
    size_set = grading_engine.generate_size_set(base_model)
    
    print(f"   📏 Создано размеров: {len(size_set)}")
    for size_name, model in size_set.items():
        print(f"      {size_name}: {len(model.points)} точек, {len(model.segments)} сегментов")
    
    # Анализ градации
    print(f"\n📊 Анализ градации:")
    comparison = grading_engine.get_size_comparison(base_model)
    
    for size_name, size_info in comparison.items():
        dims = size_info["dimensions"]
        print(f"   {size_name}:")
        if "WAIST_WIDTH" in dims:
            print(f"      Талия: {dims['WAIST_WIDTH']:.1f} мм")
        if "HIP_WIDTH" in dims:
            print(f"      Бедра: {dims['HIP_WIDTH']:.1f} мм")
        if "SKIRT_LENGTH" in dims:
            print(f"      Длина: {dims['SKIRT_LENGTH']:.1f} мм")
    
    # Экспорт градации
    print(f"\n📁 Экспорт градации в DXF...")
    exporter = GradingDxfExporter()
    
    # Один DXF со всеми размерами
    result = exporter.export_grading_dxf(size_set, "output/skirt_grading_all_sizes.dxf")
    
    if result['success']:
        print(f"   ✅ DXF создан: {result['filepath']}")
        print(f"   📏 Размеры: {', '.join(result['sizes_exported'])}")
        print(f"   📊 Всего сегментов: {result['total_segments']}")
        print(f"   🎨 Слои: {', '.join(result['layers_used'])}")
    else:
        print(f"   ❌ Ошибка: {result['error']}")
    
    print(f"\n✅ Grading Engine готов!")
