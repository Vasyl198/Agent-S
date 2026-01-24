"""
🔵 EXPORTERS — СТАНОВЯТСЯ ТУПЫМИ
===================================

📁 agent/fashion/cad/exporters/dxf.py

Разрешено:
- взять готовый Contour
- сериализовать в DXF

🚫 Запрещено:
- исправлять
- сортировать
- замыкать
- "лечить"
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import math

from ..core.geometry import Point, Segment, Contour, SegmentRole, PointRole
from ..core.validation import validate_geometry, is_valid_geometry


class DXFExporter:
    """
    📤 DXF ЭКСПОРТЁР - ТУПОЙ СЕРИАЛИЗАТОР
    
    🚫 ЗАПРЕЩЕНО: исправлять геометрию
    ✅ РАЗРЕШЕНО: только сериализация в DXF
    """
    
    def __init__(self, version: str = "AC1027"):
        self.version = version
        self.layer_map = {}
        self.layer_colors = {}
    
    def export_contour(self, contour: Contour, filepath: str, 
                     layer_name: str = "CONTOUR") -> Dict[str, Any]:
        """
        Экспортировать контур в DXF
        
        Args:
            contour: готовый контур из CAD Core
            filepath: путь для сохранения
            layer_name: имя слоя
            
        Returns:
            результат экспорта
        """
        # 📛 ПРОВЕРКА ВАЛИДАЦИИ
        if not is_valid_geometry(contour):
            validation_report = validate_geometry(contour)
            return {
                'success': False,
                'error': f'Геометрия невалидна: {validation_report}',
                'filepath': None
            }
        
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Вычисляем границы
            xmin, ymin, xmax, ymax = contour.bounds
            
            # Создаем DXF контент
            dxf_content = self._create_dxf_header(xmin, ymin, xmax, ymax)
            dxf_content += self._create_layers(layer_name)
            dxf_content += self._create_entities(contour, layer_name)
            dxf_content += self._create_dxf_footer()
            
            # Записываем файл
            with open(path, 'w', encoding='utf-8') as f:
                f.write(dxf_content)
            
            return {
                'success': True,
                'filepath': str(path),
                'segments_count': len(contour.segments),
                'arc_count': contour.arc_count,
                'layer_name': layer_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка экспорта DXF: {str(e)}',
                'filepath': None
            }
    
    def export_multiple_contours(self, contours: Dict[str, Contour], 
                             filepath: str) -> Dict[str, Any]:
        """
        Экспортировать несколько контуров в DXF
        
        Args:
            contours: словарь {имя_слоя: контур}
            filepath: путь для сохранения
            
        Returns:
            результат экспорта
        """
        # 📛 ПРОВЕРКА ВАЛИДАЦИИ ВСЕХ КОНТУРОВ
        for layer_name, contour in contours.items():
            if not is_valid_geometry(contour):
                validation_report = validate_geometry(contour)
                return {
                    'success': False,
                    'error': f'Контур {layer_name} невалиден: {validation_report}',
                    'filepath': None
                }
        
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Вычисляем общие границы
            all_bounds = [contour.bounds for contour in contours.values()]
            xmin = min(bounds[0] for bounds in all_bounds)
            ymin = min(bounds[1] for bounds in all_bounds)
            xmax = max(bounds[2] for bounds in all_bounds)
            ymax = max(bounds[3] for bounds in all_bounds)
            
            # Создаем DXF контент
            dxf_content = self._create_dxf_header(xmin, ymin, xmax, ymax)
            dxf_content += self._create_layers_list(contours.keys())
            
            for layer_name, contour in contours.items():
                dxf_content += self._create_entities(contour, layer_name)
            
            dxf_content += self._create_dxf_footer()
            
            # Записываем файл
            with open(path, 'w', encoding='utf-8') as f:
                f.write(dxf_content)
            
            total_segments = sum(len(contour.segments) for contour in contours.values())
            total_arcs = sum(contour.arc_count for contour in contours.values())
            
            return {
                'success': True,
                'filepath': str(path),
                'contours_count': len(contours),
                'total_segments': total_segments,
                'total_arcs': total_arcs,
                'layers': list(contours.keys())
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка экспорта DXF: {str(e)}',
                'filepath': None
            }
    
    def _create_dxf_header(self, xmin: float, ymin: float, 
                         xmax: float, ymax: float) -> str:
        """Создать заголовок DXF"""
        return f"""0
SECTION
2
HEADER
9
$ACADVER
1
{self.version}
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
"""
    
    def _create_layers(self, layer_name: str) -> str:
        """Создать описание одного слоя"""
        return f"""0
TABLE
2
LAYER
70
1
0
LAYER
2
{layer_name}
70
0
62
7
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
    
    def _create_layers_list(self, layer_names: List[str]) -> str:
        """Создать описание нескольких слоев"""
        layers_content = f"""0
TABLE
2
LAYER
70
{len(layer_names)}
"""
        
        for layer_name in layer_names:
            layers_content += f"""0
LAYER
2
{layer_name}
70
0
62
7
6
CONTINUOUS
"""
        
        layers_content += """0
ENDTAB
0
ENDSEC
0
SECTION
2
ENTITIES
"""
        
        return layers_content
    
    def _create_entities(self, contour: Contour, layer_name: str) -> str:
        """Создать секцию ENTITIES для контура"""
        entities_content = ""
        
        for segment in contour.segments:
            if segment.is_arc:
                entities_content += self._segment_to_dxf_arc(segment, layer_name)
            else:
                entities_content += self._segment_to_dxf_line(segment, layer_name)
        
        return entities_content
    
    def _segment_to_dxf_line(self, segment: Segment, layer_name: str) -> str:
        """Преобразовать линейный сегмент в DXF"""
        return f"""0
LWPOLYLINE
8
{layer_name}
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
    
    def _segment_to_dxf_arc(self, segment: Segment, layer_name: str) -> str:
        """Преобразовать сегмент с дугой в DXF"""
        return f"""0
LWPOLYLINE
8
{layer_name}
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
    
    def _create_dxf_footer(self) -> str:
        """Создать завершение DXF"""
        return """0
ENDSEC
0
EOF"""


class SemanticDXFExporter(DXFExporter):
    """
    🏷️ СЕМАНТИЧЕСКИЙ DXF ЭКСПОРТЁР
    
    Экспортирует контуры с семантическими слоями
    """
    
    def __init__(self):
        super().__init__()
        
        # Семантические слои
        self.semantic_layers = {
            SegmentRole.WAIST: "SEAM_WAIST",
            SegmentRole.SIDE: "SEAM_SIDE", 
            SegmentRole.HEM: "SEAM_HEM",
            SegmentRole.CENTER: "SEAM_CENTER",
            SegmentRole.UNKNOWN: "SEAM_UNKNOWN"
        }
    
    def export_semantic_contour(self, contour: Contour, filepath: str) -> Dict[str, Any]:
        """
        Экспортировать контур с семантическими слоями
        
        Args:
            contour: контур с ролями сегментов
            filepath: путь для сохранения
            
        Returns:
            результат экспорта
        """
        # 📛 ПРОВЕРКА ВАЛИДАЦИИ
        if not is_valid_geometry(contour):
            validation_report = validate_geometry(contour)
            return {
                'success': False,
                'error': f'Геометрия невалидна: {validation_report}',
                'filepath': None
            }
        
        # Группируем сегменты по ролям
        segments_by_role = {}
        for segment in contour.segments:
            role = segment.role or SegmentRole.UNKNOWN
            if role not in segments_by_role:
                segments_by_role[role] = []
            segments_by_role[role].append(segment)
        
        # Создаем контуры для каждой роли
        role_contours = {}
        for role, segments in segments_by_role.items():
            layer_name = self.semantic_layers.get(role, "SEAM_UNKNOWN")
            role_contours[layer_name] = Contour(segments, False)  # Не замкнутые
        
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Вычисляем границы
            xmin, ymin, xmax, ymax = contour.bounds
            
            # Создаем DXF контент
            dxf_content = self._create_dxf_header(xmin, ymin, xmax, ymax)
            dxf_content += self._create_layers_list(list(role_contours.keys()))
            
            for layer_name, role_contour in role_contours.items():
                dxf_content += self._create_entities(role_contour, layer_name)
            
            dxf_content += self._create_dxf_footer()
            
            # Записываем файл
            with open(path, 'w', encoding='utf-8') as f:
                f.write(dxf_content)
            
            return {
                'success': True,
                'filepath': str(path),
                'segments_count': len(contour.segments),
                'arc_count': contour.arc_count,
                'semantic_layers': list(role_contours.keys()),
                'roles_used': [role.value for role in segments_by_role.keys()]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка экспорта семантического DXF: {str(e)}',
                'filepath': None
            }


# 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА
def export_contour_to_dxf(contour: Contour, filepath: str, 
                        layer_name: str = "CONTOUR") -> Dict[str, Any]:
    """Экспортировать контур в DXF - ЕДИНСТВЕННЫЙ СПОСОБ"""
    exporter = DXFExporter()
    return exporter.export_contour(contour, filepath, layer_name)


def export_semantic_contour_to_dxf(contour: Contour, filepath: str) -> Dict[str, Any]:
    """Экспортировать семантический контур в DXF - ЕДИНСТВЕННЫЙ СПОСОБ"""
    exporter = SemanticDXFExporter()
    return exporter.export_semantic_contour(contour, filepath)


def export_multiple_contours_to_dxf(contours: Dict[str, Contour], 
                                filepath: str) -> Dict[str, Any]:
    """Экспортировать несколько контуров в DXF - ЕДИНСТВЕННЫЙ СПОСОБ"""
    exporter = DXFExporter()
    return exporter.export_multiple_contours(contours, filepath)


print("📤 CAD Core DXF Exporter загружен")
print("🔵 DXFExporter, 🏷️ SemanticDXFExporter - ЕДИНСТВЕННЫЕ КЛАССЫ")
print("🚫 ЗАПРЕЩЕНО: исправлять геометрию в экспортёрах")
