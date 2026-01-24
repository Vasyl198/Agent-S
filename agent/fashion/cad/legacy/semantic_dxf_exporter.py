"""
ЭТАП 3 — DXF ЭКСПОРТ С ЛОГИЧЕСКИМИ СЛОЯМИ
================================================

📤 4️⃣ DXF ЭКСПОРТ С ЛОГИЧЕСКИМИ СЛОЯМИ

📌 В LibreCAD ты увидишь:
- слои
- можно скрывать/показывать зоны
- можно выделять только талию / низ / бок
"""

from typing import List, Dict, Any
from pathlib import Path

from .pattern_semantics import PatternModel, PatternSegment, PatternPoint, SegmentRole


class SemanticDxfExporter:
    """
    📤 DXF ЭКСПОРТ С ЛОГИЧЕСКИМИ СЛОЯМИ
    """
    
    # 📤 Экспорт сегментов по ролям
    LAYER_MAP = {
        "WAIST": "CONTOUR_WAIST",
        "SIDE": "CONTOUR_SIDE", 
        "HEM": "CONTOUR_HEM",
        "CENTER": "CONTOUR_CENTER",
        "UNKNOWN": "CONTOUR_MISC"
    }
    
    # Цвета слоев для LibreCAD
    LAYER_COLORS = {
        "CONTOUR_WAIST": 1,    # Красный
        "CONTOUR_SIDE": 2,     # Желтый
        "CONTOUR_HEM": 3,      # Зеленый
        "CONTOUR_CENTER": 4,    # Голубой
        "CONTOUR_MISC": 7       # Белый
    }
    
    def __init__(self):
        self.layer_map = self.LAYER_MAP.copy()
        self.layer_colors = self.LAYER_COLORS.copy()
    
    def export_pattern_dxf(self, model: PatternModel, filepath: str) -> Dict[str, Any]:
        """
        Экспорт семантической модели в DXF
        
        Args:
            model: PatternModel - семантическая модель
            filepath: str - путь для сохранения
            
        Returns:
            Dict[str, Any] - результат экспорта
        """
        try:
            # Создаем директорию
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Собираем DXF контент
            dxf_content = self._build_dxf_content(model)
            
            # Записываем файл
            with open(path, 'w', encoding='utf-8') as f:
                f.write(dxf_content)
            
            # Статистика
            layer_stats = self._get_layer_statistics(model)
            
            return {
                'success': True,
                'filepath': str(path),
                'layers_used': list(self.layer_map.values()),
                'layer_stats': layer_stats,
                'total_points': len(model.points),
                'total_segments': len(model.segments),
                'arc_segments': model.get_arc_count(),
                'line_segments': model.get_line_count()
            }
            
        except Exception as e:
            return {
                'success': False,
                'filepath': None,
                'error': f'Ошибка экспорта: {str(e)}',
                'layers_used': [],
                'layer_stats': {},
                'total_points': 0,
                'total_segments': 0,
                'arc_segments': 0,
                'line_segments': 0
            }
    
    def _build_dxf_content(self, model: PatternModel) -> str:
        """Построить DXF контент"""
        
        # Вычисляем границы
        xs = [p.x for p in model.points]
        ys = [p.y for p in model.points]
        
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
        
        # Экспорт сегментов по слоям
        for segment in model.segments:
            layer = self.layer_map.get(segment.role, "CONTOUR_MISC")
            dxf_content += self._segment_to_dxf(segment, layer)
        
        dxf_content += """0
ENDSEC
0
EOF"""
        
        return dxf_content
    
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
    
    def _get_layer_statistics(self, model: PatternModel) -> Dict[str, Any]:
        """Получить статистику по слоям"""
        stats = {}
        
        for layer_name in self.layer_map.values():
            layer_segments = [s for s in model.segments 
                           if self.layer_map.get(s.role, "CONTOUR_MISC") == layer_name]
            
            stats[layer_name] = {
                'segment_count': len(layer_segments),
                'arc_count': sum(1 for s in layer_segments if s.is_arc()),
                'line_count': sum(1 for s in layer_segments if s.is_line()),
                'total_length': sum(s.length() for s in layer_segments)
            }
        
        return stats
    
    def export_separated_layers_dxf(self, model: PatternModel, base_filepath: str) -> Dict[str, Any]:
        """
        Экспорт отдельных DXF файлов для каждого слоя
        
        Args:
            model: PatternModel - семантическая модель
            base_filepath: str - базовый путь (без расширения)
            
        Returns:
            Dict[str, Any] - результат экспорта
        """
        results = {}
        
        for role, layer_name in self.layer_map.items():
            if role == "UNKNOWN":
                continue
            
            # Создаем модель только для этого слоя
            layer_segments = model.get_segments_by_role(role)
            if not layer_segments:
                continue
            
            # Собираем все точки из сегментов этого слоя
            layer_points = set()
            for seg in layer_segments:
                layer_points.add(seg.start)
                layer_points.add(seg.end)
            
            layer_model = PatternModel(
                points=list(layer_points),
                segments=layer_segments
            )
            
            # Экспорт
            filepath = f"{base_filepath}_{layer_name.lower()}.dxf"
            result = self.export_pattern_dxf(layer_model, filepath)
            results[layer_name] = result
        
        return {
            'success': all(r['success'] for r in results.values()),
            'layers': results,
            'base_filepath': base_filepath
        }


# Тестирование
if __name__ == "__main__":
    print("🧪 ТЕСТ SEMANTIC DXF EXPORTER")
    print("=" * 60)
    
    # Импортируем билдер
    from .pattern_semantics import PatternSemanticsBuilder
    
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
    
    # Создаем семантическую модель
    builder = PatternSemanticsBuilder()
    model = builder.build_pattern_model(points, bulges)
    
    print(f"\n🏗️ Семантическая модель:")
    print(f"   Точек: {len(model.points)}")
    print(f"   Сегментов: {len(model.segments)}")
    print(f"   Дуг: {model.get_arc_count()}")
    print(f"   Линий: {model.get_line_count()}")
    
    # Создаем экспортер
    exporter = SemanticDxfExporter()
    
    # Экспорт в один файл с слоями
    print(f"\n📁 Экспорт в один DXF с слоями...")
    result = exporter.export_pattern_dxf(model, "output/skirt_semantic_layers.dxf")
    
    if result['success']:
        print(f"   ✅ DXF создан: {result['filepath']}")
        print(f"   📊 Слои: {', '.join(result['layers_used'])}")
        print(f"   📏 Статистика по слоям:")
        for layer, stats in result['layer_stats'].items():
            if stats['segment_count'] > 0:
                print(f"      {layer}: {stats['segment_count']} сегментов, "
                      f"{stats['arc_count']} дуг, {stats['line_count']} линий, "
                      f"{stats['total_length']:.1f} мм")
    else:
        print(f"   ❌ Ошибка: {result['error']}")
    
    # Экспорт отдельных файлов для каждого слоя
    print(f"\n📁 Экспорт отдельных DXF файлов...")
    separated_result = exporter.export_separated_layers_dxf(model, "output/skirt_layer")
    
    if separated_result['success']:
        print(f"   ✅ Создано файлов: {len(separated_result['layers'])}")
        for layer_name, layer_result in separated_result['layers'].items():
            print(f"      {layer_name}: {layer_result['filepath']}")
    else:
        print(f"   ❌ Ошибка разделения слоев")
    
    print(f"\n✅ Semantic DXF Exporter готов!")
