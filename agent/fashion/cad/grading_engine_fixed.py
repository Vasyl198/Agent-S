"""
ЭТАП 5 — ГРАДАЦИЯ (SIZE GRADING ENGINE) - ИСПРАВЛЕННАЯ ВЕРСИЯ
================================================================

Это критический этап, который отличает:
❌ «чертёж»
✅ производственное лекало
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
    x_increment: float
    y_increment: float


class GradingEngine:
    """Движок градации как в Lectra / Gerber"""
    
    GRADE_RULES = {
        "WAIST": GradeRule(x_increment=5.0, y_increment=0.0),
        "HIP": GradeRule(x_increment=6.0, y_increment=0.0),
        "HEM": GradeRule(x_increment=7.0, y_increment=0.0),
        "LENGTH": GradeRule(x_increment=0.0, y_increment=3.0)
    }
    
    POINT_GRADE_BEHAVIOR = {
        "WAIST_CENTER": {"x_factor": 0.0, "y_factor": 0.0},
        "WAIST_SIDE": {"x_factor": 1.0, "y_factor": 0.0},
        "HIP_SIDE": {"x_factor": 1.0, "y_factor": 0.0},
        "HEM_SIDE": {"x_factor": 1.0, "y_factor": 0.0},
        "HEM_CENTER": {"x_factor": 0.0, "y_factor": 0.0},
        "CENTER_LINE": {"x_factor": 0.0, "y_factor": 1.0},
    }
    
    def __init__(self):
        self.graded_models = {}
        self.size_counter = 0
    
    def get_grade_rule(self, measurement: str) -> Optional[GradeRule]:
        return self.GRADE_RULES.get(measurement)
    
    def get_point_behavior(self, role: str) -> Dict[str, float]:
        return self.POINT_GRADE_BEHAVIOR.get(role, {"x_factor": 0.0, "y_factor": 0.0})
    
    def grade_point(self, point: PatternPoint, step: int) -> PatternPoint:
        """Градация одной точки"""
        behavior = self.get_point_behavior(point.role)
        measurement = self._get_measurement_for_point(point.role)
        grade_rule = self.get_grade_rule(measurement)
        
        if not grade_rule:
            return PatternPoint(
                name=f"{point.name}_G{step}",
                role=point.role,
                x=point.x,
                y=point.y
            )
        
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
            return "WAIST"
    
    def grade_pattern(self, model: PatternModel, step: int) -> PatternModel:
        """Градация всего лекала"""
        new_points = [self.grade_point(p, step) for p in model.points]
        
        # ВАЖНО: сегменты копируем БЕЗ ИЗМЕНЕНИЯ bulge
        new_segments = []
        for seg in model.segments:
            p1 = next((p for p in new_points if p.role == seg.start.role), seg.start)
            p2 = next((p for p in new_points if p.role == seg.end.role), seg.end)
            
            new_segments.append(PatternSegment(
                start=p1,
                end=p2,
                bulge=seg.bulge,  # Bulge НЕ ТРОГАЕМ
                role=seg.role
            ))
        
        return PatternModel(points=new_points, segments=new_segments)
    
    def generate_size_set(self, base_model: PatternModel) -> Dict[str, PatternModel]:
        """Генерация размерного ряда"""
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


class GradingDxfExporter:
    """DXF экспорт градации"""
    
    SIZE_LAYER = {
        "XS": "SIZE_XS",
        "S": "SIZE_S",
        "M": "SIZE_M",
        "L": "SIZE_L",
        "XL": "SIZE_XL"
    }
    
    LAYER_COLORS = {
        "SIZE_XS": 1,
        "SIZE_S": 2,
        "SIZE_M": 3,
        "SIZE_L": 4,
        "SIZE_XL": 5
    }
    
    def __init__(self):
        self.layer_map = self.SIZE_LAYER.copy()
        self.layer_colors = self.LAYER_COLORS.copy()
    
    def export_grading_dxf(self, size_set: Dict[str, PatternModel], filepath: str) -> Dict[str, Any]:
        """Экспорт размерного ряда в один DXF"""
        try:
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
