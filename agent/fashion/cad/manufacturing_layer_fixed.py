"""
ЭТАП 6 — ПРОИЗВОДСТВЕННЫЕ ЭЛЕМЕНТЫ (Manufacturing Layer) - ИСПРАВЛЕННАЯ ВЕРСИЯ
================================================================================

Это момент, где система из CAD-геометрии становится производственным лекалом.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import math
from pathlib import Path

from .pattern_semantics import PatternModel, PatternPoint, PatternSegment


class NotchRole(Enum):
    WAIST_CENTER = "WAIST_CENTER"
    HIP_CONTROL = "HIP_CONTROL"
    HEM_CONTROL = "HEM_CONTROL"
    BALANCE = "BALANCE"
    UNKNOWN = "UNKNOWN"


class AllowanceType(Enum):
    WAIST = "WAIST"
    SIDE = "SIDE"
    HEM = "HEM"
    CENTER = "CENTER"


@dataclass
class Notch:
    """Надсечки"""
    x: float
    y: float
    angle: float
    length: float = 4.0
    role: str = NotchRole.UNKNOWN.value
    
    def get_endpoints(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        dx = math.cos(self.angle) * self.length / 2
        dy = math.sin(self.angle) * self.length / 2
        
        start = (self.x - dx, self.y - dy)
        end = (self.x + dx, self.y + dy)
        
        return start, end


@dataclass
class GrainLine:
    """Направление долевой"""
    start: Tuple[float, float]
    end: Tuple[float, float]
    arrow_direction: str = "UP"
    
    def get_midpoint(self) -> Tuple[float, float]:
        x = (self.start[0] + self.end[0]) / 2
        y = (self.start[1] + self.end[1]) / 2
        return (x, y)
    
    def get_length(self) -> float:
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return math.sqrt(dx * dx + dy * dy)


@dataclass
class PatternLabel:
    """Подписи лекала"""
    text: str
    position: Tuple[float, float]
    height: float = 5.0
    rotation: float = 0.0
    layer: str = "LABELS"


@dataclass
class ManufacturingAllowance:
    """Припуски по ролям"""
    role: str
    allowance: float
    segment_indices: List[int]


class ManufacturingEngine:
    """Движок производственных элементов"""
    
    NOTCH_RULES = {
        "WAIST": {"count": 1, "positions": [0.5], "role": NotchRole.WAIST_CENTER.value},
        "HIP": {"count": 1, "positions": [0.5], "role": NotchRole.HIP_CONTROL.value},
        "HEM": {"count": 2, "positions": [0.3, 0.7], "role": NotchRole.HEM_CONTROL.value},
        "SIDE": {"count": 1, "positions": [0.5], "role": NotchRole.BALANCE.value}
    }
    
    ALLOWANCE_MAP = {
        "WAIST": 10.0,
        "SIDE": 15.0,
        "HEM": 30.0,
        "CENTER": 0.0
    }
    
    def __init__(self):
        self.notches = []
        self.grainline = None
        self.labels = []
        self.allowances = []
        self.mirrored_model = None
    
    def build_notch_on_segment(self, seg: PatternSegment, t: float = 0.5) -> Notch:
        """Генерация надсечки на сегменте"""
        x1, y1 = seg.start.x, seg.start.y
        x2, y2 = seg.end.x, seg.end.y
        
        # точка на сегменте
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        
        # нормаль (перпендикуляр)
        dx, dy = x2 - x1, y2 - y1
        angle = math.atan2(dy, dx) + math.pi / 2
        
        # Определяем роль надсечки
        notch_role = self.NOTCH_RULES.get(seg.role, {}).get("role", NotchRole.UNKNOWN.value)
        
        return Notch(x=x, y=y, angle=angle, role=notch_role)
    
    def build_notches_for_model(self, model: PatternModel) -> List[Notch]:
        """Построить все надсечки для модели"""
        notches = []
        
        for i, segment in enumerate(model.segments):
            role_rules = self.NOTCH_RULES.get(segment.role)
            
            if role_rules:
                for position in role_rules["positions"]:
                    notch = self.build_notch_on_segment(segment, position)
                    notches.append(notch)
        
        self.notches = notches
        return notches
    
    def build_grainline(self, model: PatternModel) -> GrainLine:
        """Построить направление долевой"""
        center_segments = model.get_segments_by_role("CENTER")
        
        if not center_segments:
            center_seg = model.segments[0]
            mid_x = center_seg.start.x
        else:
            center_seg = center_segments[0]
            mid_x = (center_seg.start.x + center_seg.end.x) / 2
        
        # Вычисляем границы модели
        xs = [p.x for p in model.points]
        ys = [p.y for p in model.points]
        ymin, ymax = min(ys), max(ys)
        
        # Долевая линия
        y1 = ymin + 50
        y2 = y1 + 120
        
        grainline = GrainLine(
            start=(mid_x, y1),
            end=(mid_x, y2),
            arrow_direction="UP"
        )
        
        self.grainline = grainline
        return grainline
    
    def build_labels(self, model: PatternModel, size: str = "M", 
                     pattern_name: str = "SKIRT FRONT") -> List[PatternLabel]:
        """Построить подписи лекала"""
        labels = []
        
        # Вычисляем границы для позиционирования
        xs = [p.x for p in model.points]
        ys = [p.y for p in model.points]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        
        # Основная подпись
        main_label = PatternLabel(
            text=f"{pattern_name} — SIZE {size}",
            position=(xmin + 30, ymin + 100),
            height=8.0
        )
        labels.append(main_label)
        
        # Подпись долевой
        if self.grainline:
            grain_label = PatternLabel(
                text="GRAINLINE",
                position=(self.grainline.start[0] + 15, self.grainline.start[1] + 10),
                height=4.0
            )
            labels.append(grain_label)
        
        # Количество деталей
        quantity_label = PatternLabel(
            text="CUT 1",
            position=(xmin + 30, ymin + 130),
            height=5.0
        )
        labels.append(quantity_label)
        
        # Версия
        version_label = PatternLabel(
            text="v1.0",
            position=(xmax - 50, ymax - 30),
            height=3.0
        )
        labels.append(version_label)
        
        self.labels = labels
        return labels
    
    def build_allowances(self, model: PatternModel) -> List[ManufacturingAllowance]:
        """Построить припуски по ролям"""
        allowances = []
        
        for role, allowance_value in self.ALLOWANCE_MAP.items():
            # Находим сегменты с этой ролью
            role_segments = []
            for i, seg in enumerate(model.segments):
                if seg.role == role:
                    role_segments.append(i)
            
            if role_segments:
                allowance = ManufacturingAllowance(
                    role=role,
                    allowance=allowance_value,
                    segment_indices=role_segments
                )
                allowances.append(allowance)
        
        self.allowances = allowances
        return allowances
    
    def mirror_model(self, model: PatternModel) -> PatternModel:
        """Зеркалирование модели"""
        # Зеркалируем точки
        mirrored_points = []
        for point in model.points:
            mirrored_point = PatternPoint(
                name=f"{point.name}_MIRROR",
                role=point.role,
                x=-point.x,  # Зеркалирование по X
                y=point.y
            )
            mirrored_points.append(mirrored_point)
        
        # Зеркалируем сегменты
        mirrored_segments = []
        for seg in model.segments:
            # Находим зеркальные точки
            start_point = next((p for p in mirrored_points if p.role == seg.start.role), seg.start)
            end_point = next((p for p in mirrored_points if p.role == seg.end.role), seg.end)
            
            mirrored_segment = PatternSegment(
                start=start_point,
                end=end_point,
                bulge=-seg.bulge,  # знак меняется при зеркалировании
                role=seg.role
            )
            mirrored_segments.append(mirrored_segment)
        
        mirrored_model = PatternModel(
            points=mirrored_points,
            segments=mirrored_segments
        )
        
        self.mirrored_model = mirrored_model
        return mirrored_model
    
    def build_manufacturing_layers(self, model: PatternModel, size: str = "M", 
                                 pattern_name: str = "SKIRT FRONT") -> Dict[str, Any]:
        """Построить все производственные слои"""
        # Надсечки
        notches = self.build_notches_for_model(model)
        
        # Долевая
        grainline = self.build_grainline(model)
        
        # Подписи
        labels = self.build_labels(model, size, pattern_name)
        
        # Припуски
        allowances = self.build_allowances(model)
        
        return {
            "notches": notches,
            "grainline": grainline,
            "labels": labels,
            "allowances": allowances,
            "mirrored_model": self.mirrored_model
        }


class ManufacturingDxfExporter:
    """DXF экспорт производственных слоев"""
    
    LAYER_MAP = {
        "notches": "MANUFACTURING_NOTCHES",
        "grainline": "MANUFACTURING_GRAINLINE",
        "labels": "MANUFACTURING_LABELS",
        "allowances": "MANUFACTURING_ALLOWANCES",
        "mirrored": "MANUFACTURING_MIRRORED"
    }
    
    LAYER_COLORS = {
        "MANUFACTURING_NOTCHES": 1,
        "MANUFACTURING_GRAINLINE": 2,
        "MANUFACTURING_LABELS": 3,
        "MANUFACTURING_ALLOWANCES": 4,
        "MANUFACTURING_MIRRORED": 5
    }
    
    def __init__(self):
        self.layer_map = self.LAYER_MAP.copy()
        self.layer_colors = self.LAYER_COLORS.copy()
    
    def export_manufacturing_dxf(self, model: PatternModel, 
                               manufacturing_layers: Dict[str, Any],
                               filepath: str) -> Dict[str, Any]:
        """Экспорт производственных слоев в DXF"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Вычисляем границы
            all_points = model.points.copy()
            
            if manufacturing_layers.get("mirrored_model"):
                all_points.extend(manufacturing_layers["mirrored_model"].points)
            
            xs = [p.x for p in all_points]
            ys = [p.y for p in all_points]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            
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
            for layer_name, color in self.layer_colors.items():
                if layer_name in self.layer_map.values():
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
            
            # Экспорт базовой модели
            for segment in model.segments:
                dxf_content += self._segment_to_dxf(segment, "PATTERN_BASE")
            
            # Экспорт надсечек
            notches = manufacturing_layers.get("notches", [])
            for notch in notches:
                dxf_content += self._notch_to_dxf(notch)
            
            # Экспорт долевой
            grainline = manufacturing_layers.get("grainline")
            if grainline:
                dxf_content += self._grainline_to_dxf(grainline)
            
            # Экспорт подписей
            labels = manufacturing_layers.get("labels", [])
            for label in labels:
                dxf_content += self._label_to_dxf(label)
            
            # Экспорт зеркальной модели
            mirrored_model = manufacturing_layers.get("mirrored_model")
            if mirrored_model:
                for segment in mirrored_model.segments:
                    dxf_content += self._segment_to_dxf(segment, self.layer_map["mirrored"])
            
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
                'notches_count': len(notches),
                'labels_count': len(labels),
                'has_grainline': grainline is not None,
                'has_mirrored': mirrored_model is not None
            }
            
        except Exception as e:
            return {
                'success': False,
                'filepath': None,
                'error': f'Ошибка экспорта производства: {str(e)}',
                'notches_count': 0,
                'labels_count': 0,
                'has_grainline': False,
                'has_mirrored': False
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
    
    def _notch_to_dxf(self, notch: Notch) -> str:
        """Преобразовать надсечку в DXF"""
        start, end = notch.get_endpoints()
        
        return f"""0
LINE
8
{self.layer_map["notches"]}
10
{start[0]}
20
{start[1]}
11
{end[0]}
21
{end[1]}
"""
    
    def _grainline_to_dxf(self, grainline: GrainLine) -> str:
        """Преобразовать долевую в DXF"""
        return f"""0
LINE
8
{self.layer_map["grainline"]}
10
{grainline.start[0]}
20
{grainline.start[1]}
11
{grainline.end[0]}
21
{grainline.end[1]}
"""
    
    def _label_to_dxf(self, label: PatternLabel) -> str:
        """Преобразовать подпись в DXF"""
        return f"""0
TEXT
8
{self.layer_map["labels"]}
10
{label.position[0]}
20
{label.position[1]}
40
{label.height}
1
{label.text}
50
{label.rotation}
7
STANDARD
"""


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ MANUFACTURING LAYER")
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
    
    print("📊 Базовая модель:")
    print(f"   Точек: {len(model.points)}")
    print(f"   Сегментов: {len(model.segments)}")
    print(f"   Дуг: {model.get_arc_count()}")
    
    # Создаем движок производственных элементов
    manufacturing_engine = ManufacturingEngine()
    
    # Строим производственные слои
    print(f"\n🔧 Построение производственных слоев...")
    manufacturing_layers = manufacturing_engine.build_manufacturing_layers(
        model, size="M", pattern_name="SKIRT FRONT"
    )
    
    print(f"   ✂️ Надсечки: {len(manufacturing_layers['notches'])}")
    for notch in manufacturing_layers['notches']:
        print(f"      {notch.role} в ({notch.x:.1f}, {notch.y:.1f})")
    
    print(f"   📐 Долевая: {manufacturing_layers['grainline'] is not None}")
    if manufacturing_layers['grainline']:
        gl = manufacturing_layers['grainline']
        print(f"      от {gl.start} до {gl.end}")
    
    print(f"   📝 Подписи: {len(manufacturing_layers['labels'])}")
    for label in manufacturing_layers['labels']:
        print(f"      {label.text} в {label.position}")
    
    print(f"   📏 Припуски: {len(manufacturing_layers['allowances'])}")
    for allowance in manufacturing_layers['allowances']:
        print(f"      {allowance.role}: {allowance.allowance} мм")
    
    # Зеркалирование
    print(f"\n🔄 Зеркалирование...")
    mirrored_model = manufacturing_engine.mirror_model(model)
    print(f"   ✅ Зеркальная модель: {len(mirrored_model.points)} точек")
    
    # Экспорт
    print(f"\n📁 Экспорт производственных слоев...")
    exporter = ManufacturingDxfExporter()
    
    result = exporter.export_manufacturing_dxf(
        model, manufacturing_layers, "output/skirt_manufacturing.dxf"
    )
    
    if result['success']:
        print(f"   ✅ DXF создан: {result['filepath']}")
        print(f"   ✂️ Надсечки: {result['notches_count']}")
        print(f"   📝 Подписи: {result['labels_count']}")
        print(f"   📐 Долевая: {'Да' if result['has_grainline'] else 'Нет'}")
        print(f"   🔄 Зеркальная: {'Да' if result['has_mirrored'] else 'Нет'}")
    else:
        print(f"   ❌ Ошибка: {result['error']}")
    
    print(f"\n✅ Manufacturing Layer готов!")
