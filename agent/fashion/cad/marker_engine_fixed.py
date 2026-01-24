"""
ЭТАП 7 — MARKER ENGINE (РАСКЛАДКА ЛЕКАЛ) - ИСПРАВЛЕННАЯ ВЕРСИЯ
=================================================================

Это последний крупный CAD-этап, после него система считается производственно замкнутой.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import math
from pathlib import Path

from .pattern_semantics import PatternModel, PatternPoint, PatternSegment


class GrainAngle(Enum):
    DEG_0 = 0
    DEG_180 = 180


@dataclass
class BoundingBox:
    """Bounding Box для детали"""
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    
    @property
    def width(self) -> float:
        return self.xmax - self.xmin
    
    @property
    def height(self) -> float:
        return self.ymax - self.ymin
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    @property
    def center_x(self) -> float:
        return (self.xmin + self.xmax) / 2
    
    @property
    def center_y(self) -> float:
        return (self.ymin + self.ymax) / 2
    
    def offset(self, dx: float, dy: float) -> 'BoundingBox':
        return BoundingBox(
            xmin=self.xmin + dx,
            ymin=self.ymin + dy,
            xmax=self.xmax + dx,
            ymax=self.ymax + dy
        )
    
    def intersects(self, other: 'BoundingBox') -> bool:
        return not (
            self.xmax <= other.xmin or
            other.xmax <= self.xmin or
            self.ymax <= other.ymin or
            other.ymax <= self.ymin
        )


@dataclass
class MarkerPiece:
    """Одна деталь в маркере"""
    model: PatternModel
    size: str
    grain_angle: float
    bbox: BoundingBox
    x_offset: float = 0.0
    y_offset: float = 0.0
    placed: bool = False
    
    @property
    def name(self) -> str:
        return f"{self.size}_{self.model.__class__.__name__}"
    
    def get_actual_bbox(self) -> BoundingBox:
        return self.bbox.offset(self.x_offset, self.y_offset)
    
    def can_rotate_to(self, angle: float) -> bool:
        return angle in [0, 180]


@dataclass
class MarkerSheet:
    """Полотно ткани с раскладкой"""
    width: float
    pieces: List[MarkerPiece]
    height: float = 0.0
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    @property
    def pieces_area(self) -> float:
        return sum(piece.bbox.area for piece in self.pieces)
    
    @property
    def waste_area(self) -> float:
        return self.area - self.pieces_area
    
    @property
    def waste_percentage(self) -> float:
        if self.area == 0:
            return 0.0
        return (self.waste_area / self.area) * 100


class MarkerEngine:
    """Движок раскладки лекал"""
    
    ALLOWED_ROTATIONS = [0, 180]
    
    def __init__(self, fabric_width: float = 1400.0):
        self.fabric_width = fabric_width
        self.pieces = []
        self.marker_sheet = None
    
    def calculate_bounding_box(self, model: PatternModel) -> BoundingBox:
        """Рассчитать bounding box для модели"""
        if not model.points:
            return BoundingBox(0, 0, 0, 0)
        
        xs = [p.x for p in model.points]
        ys = [p.y for p in model.points]
        
        margin = 10.0
        
        return BoundingBox(
            xmin=min(xs) - margin,
            ymin=min(ys) - margin,
            xmax=max(xs) + margin,
            ymax=max(ys) + margin
        )
    
    def add_piece(self, model: PatternModel, size: str, grain_angle: float = 0.0) -> MarkerPiece:
        """Добавить деталь в раскладку"""
        bbox = self.calculate_bounding_box(model)
        
        piece = MarkerPiece(
            model=model,
            size=size,
            grain_angle=grain_angle,
            bbox=bbox
        )
        
        self.pieces.append(piece)
        return piece
    
    def step_1_sorting(self) -> List[MarkerPiece]:
        """ШАГ 1 — СОРТИРОВКА"""
        return sorted(self.pieces, key=lambda p: (p.bbox.height, p.bbox.width), reverse=True)
    
    def step_2_strip_packing(self, sorted_pieces: List[MarkerPiece]) -> MarkerSheet:
        """ШАГ 2 — ПОЛОСНАЯ УКЛАДКА (STRIP PACKING)"""
        marker_sheet = MarkerSheet(width=self.fabric_width, pieces=[])
        current_y = 0.0
        current_row_height = 0.0
        current_x = 0.0
        
        for piece in sorted_pieces:
            if current_x + piece.bbox.width <= self.fabric_width:
                piece.x_offset = current_x
                piece.y_offset = current_y
                piece.placed = True
                
                current_x += piece.bbox.width
                current_row_height = max(current_row_height, piece.bbox.height)
                
            else:
                current_y += current_row_height + 5.0
                current_x = 0.0
                current_row_height = piece.bbox.height
                
                piece.x_offset = current_x
                piece.y_offset = current_y
                piece.placed = True
                
                current_x += piece.bbox.width
            
            marker_sheet.pieces.append(piece)
        
        if marker_sheet.pieces:
            last_piece = max(marker_sheet.pieces, key=lambda p: p.y_offset + p.bbox.height)
            marker_sheet.height = last_piece.y_offset + last_piece.bbox.height + 10.0
        
        return marker_sheet
    
    def step_3_intersection_check(self, marker_sheet: MarkerSheet) -> bool:
        """ШАГ 3 — ПРОВЕРКА ПЕРЕСЕЧЕНИЙ"""
        placed_pieces = []
        
        for piece in marker_sheet.pieces:
            if not piece.placed:
                continue
            
            piece_bbox = piece.get_actual_bbox()
            
            for placed_piece in placed_pieces:
                placed_bbox = placed_piece.get_actual_bbox()
                
                if piece_bbox.intersects(placed_bbox):
                    return False
            
            placed_pieces.append(piece)
        
        return True
    
    def step_4_marker_height(self, marker_sheet: MarkerSheet) -> Dict[str, float]:
        """ШАГ 4 — ВЫСОТА МАРКЕРА"""
        stats = {
            'marker_height': marker_sheet.height,
            'marker_area': marker_sheet.area,
            'pieces_area': marker_sheet.pieces_area,
            'waste_area': marker_sheet.waste_area,
            'waste_percentage': marker_sheet.waste_percentage,
            'pieces_count': len(marker_sheet.pieces),
            'fabric_width': marker_sheet.width
        }
        
        return stats
    
    def create_marker(self, models_with_sizes: Dict[str, List[Tuple[PatternModel, str]]]) -> MarkerSheet:
        """Создать раскладку маркера"""
        self.pieces = []
        
        for pattern_type, model_list in models_with_sizes.items():
            for model, size in model_list:
                self.add_piece(model, size, grain_angle=0.0)
        
        sorted_pieces = self.step_1_sorting()
        marker_sheet = self.step_2_strip_packing(sorted_pieces)
        intersections_ok = self.step_3_intersection_check(marker_sheet)
        
        if not intersections_ok:
            raise ValueError("Обнаружены пересечения в раскладке")
        
        stats = self.step_4_marker_height(marker_sheet)
        
        self.marker_sheet = marker_sheet
        return marker_sheet


class MarkerDxfExporter:
    """DXF экспорт маркера"""
    
    def __init__(self):
        self.layer_map = {
            "pattern": "MARKER_PATTERN",
            "labels": "MARKER_LABELS",
            "grainline": "MARKER_GRAINLINE",
            "border": "MARKER_BORDER"
        }
    
    def export_marker_dxf(self, marker_sheet: MarkerSheet, filepath: str) -> Dict[str, Any]:
        """Экспорт маркера в DXF"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            dxf_content = f'''0
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
0.0
20
0.0
30
0.0
9
$EXTMAX
10
{marker_sheet.width}
20
{marker_sheet.height}
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
'''
            
            for layer_name in self.layer_map.values():
                dxf_content += f'''0
LAYER
2
{layer_name}
70
0
62
7
6
CONTINUOUS
'''
            
            dxf_content += '''0
ENDTAB
0
ENDSEC
0
SECTION
2
ENTITIES
'''
            
            dxf_content += self._export_marker_border(marker_sheet)
            
            for piece in marker_sheet.pieces:
                if piece.placed:
                    dxf_content += self._export_piece(piece)
            
            dxf_content += '''0
ENDSEC
0
EOF'''
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(dxf_content)
            
            return {
                'success': True,
                'filepath': str(path),
                'pieces_exported': len([p for p in marker_sheet.pieces if p.placed]),
                'marker_width': marker_sheet.width,
                'marker_height': marker_sheet.height,
                'waste_percentage': marker_sheet.waste_percentage
            }
            
        except Exception as e:
            return {
                'success': False,
                'filepath': None,
                'error': f'Ошибка экспорта маркера: {str(e)}',
                'pieces_exported': 0
            }
    
    def _export_marker_border(self, marker_sheet: MarkerSheet) -> str:
        """Экспорт границ маркера"""
        return f'''0
LWPOLYLINE
8
{self.layer_map["border"]}
90
4
70
1
10
0.0
20
0.0
42
0.0
10
{marker_sheet.width}
20
0.0
42
0.0
10
{marker_sheet.width}
20
{marker_sheet.height}
42
0.0
10
0.0
20
{marker_sheet.height}
42
0.0
'''
    
    def _export_piece(self, piece: MarkerPiece) -> str:
        """Экспорт одной детали"""
        dxf_content = ""
        
        for segment in piece.model.segments:
            start_x = segment.start.x + piece.x_offset
            start_y = segment.start.y + piece.y_offset
            end_x = segment.end.x + piece.x_offset
            end_y = segment.end.y + piece.y_offset
            
            if segment.is_arc():
                dxf_content += f'''0
LWPOLYLINE
8
{self.layer_map["pattern"]}
90
2
70
0
10
{start_x}
20
{start_y}
42
{segment.bulge}
10
{end_x}
20
{end_y}
'''
            else:
                dxf_content += f'''0
LWPOLYLINE
8
{self.layer_map["pattern"]}
90
2
70
0
10
{start_x}
20
{start_y}
42
0.0
10
{end_x}
20
{end_y}
'''
        
        label_x = piece.x_offset + piece.bbox.width / 2
        label_y = piece.y_offset + piece.bbox.height / 2
        
        dxf_content += f'''0
TEXT
8
{self.layer_map["labels"]}
10
{label_x}
20
{label_y}
40
8.0
1
{piece.size}
7
STANDARD
'''
        
        return dxf_content


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ MARKER ENGINE")
    print("=" * 50)
    
    # Создаем тестовые модели разных размеров
    from .pattern_semantics import PatternSemanticsBuilder
    
    # Базовая модель
    points = [
        (0.0, 0.0), (92.5, 8.0), (185.0, 0.0), (264.0, 180.0),
        (250.0, 650.0), (125.0, 662.0), (0.0, 650.0), (0.0, 180.0), (0.0, 0.0)
    ]
    bulges = [-0.086486, 0.0, 0.225381, 0.0, 0.095131, 0.0, 0.0, 0.0, 0.0]
    
    builder = PatternSemanticsBuilder()
    base_model = builder.build_pattern_model(points, bulges)
    
    # Создаем простую градацию (упрощенно)
    size_set = {}
    sizes = [
        ("XS", -2), ("S", -1), ("M", 0), ("L", 1), ("XL", 2)
    ]
    
    for size_name, step in sizes:
        # Простое смещение для теста
        graded_points = []
        for point in base_model.points:
            new_x = point.x + step * 10
            new_y = point.y + step * 5
            graded_points.append(PatternPoint(
                name=f"{point.name}_{size_name}",
                role=point.role,
                x=new_x,
                y=new_y
            ))
        
        graded_segments = []
        for seg in base_model.segments:
            start_point = next((p for p in graded_points if p.role == seg.start.role), seg.start)
            end_point = next((p for p in graded_points if p.role == seg.end.role), seg.end)
            
            graded_segments.append(PatternSegment(
                start=start_point,
                end=end_point,
                bulge=seg.bulge,
                role=seg.role
            ))
        
        size_set[size_name] = PatternModel(points=graded_points, segments=graded_segments)
    
    print("📊 Созданы модели:")
    for size_name, model in size_set.items():
        print(f"   {size_name}: {len(model.points)} точек")
    
    # Создаем движок маркера
    marker_engine = MarkerEngine(fabric_width=1400.0)
    
    models_with_sizes = {
        "skirt_front": [(model, size) for size, model in size_set.items()]
    }
    
    print(f"\n🔧 Создание маркера...")
    marker_sheet = marker_engine.create_marker(models_with_sizes)
    
    stats = marker_engine.step_4_marker_height(marker_sheet)
    
    print(f"   📏 Ширина ткани: {stats['fabric_width']:.0f} мм")
    print(f"   📏 Высота маркера: {stats['marker_height']:.0f} мм")
    print(f"   📊 Площадь маркера: {stats['marker_area']:.0f} мм²")
    print(f"   📊 Площадь деталей: {stats['pieces_area']:.0f} мм²")
    print(f"   🗑️ Площадь отходов: {stats['waste_area']:.0f} мм²")
    print(f"   📊 Процент отходов: {stats['waste_percentage']:.1f}%")
    print(f"   📦 Количество деталей: {stats['pieces_count']}")
    
    print(f"\n📍 Позиции деталей:")
    for piece in marker_sheet.pieces:
        if piece.placed:
            print(f"   {piece.name}: ({piece.x_offset:.0f}, {piece.y_offset:.0f})")
    
    # Экспорт
    print(f"\n📁 Экспорт маркера...")
    exporter = MarkerDxfExporter()
    
    result = exporter.export_marker_dxf(marker_sheet, "output/skirt_marker.dxf")
    
    if result['success']:
        print(f"   ✅ DXF создан: {result['filepath']}")
        print(f"   📦 Деталей экспортировано: {result['pieces_exported']}")
        print(f"   📏 Размер маркера: {result['marker_width']:.0f} × {result['marker_height']:.0f} мм")
        print(f"   🗑️ Отходы: {result['waste_percentage']:.1f}%")
    else:
        print(f"   ❌ Ошибка: {result['error']}")
    
    print(f"\n✅ Marker Engine готов!")
    print(f"\n🧠 РЕЗУЛЬТАТ ЭТАПА 7:")
    print(f"После этого этапа система умеет:")
    print(f"✅ строить лекало")
    print(f"✅ градацию")
    print(f"✅ припуски")
    print(f"✅ производственные элементы")
    print(f"✅ раскладку на ткани")
    print(f"\n📌 Это полный цикл.")
