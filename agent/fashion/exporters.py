"""
Fashion Exporters Module

Классы для экспорта дизайнов и лекал в различные форматы.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
import base64
import io
from datetime import datetime


class ExportFormat(Enum):
    """Поддерживаемые форматы экспорта"""
    JSON = "json"
    SVG = "svg"
    PDF = "pdf"
    DXF = "dxf"
    PLT = "plt"
    AAMA = "aama"
    GERBER = "gerber"
    SEAMLY2D = "seamly2d"
    BLENDER = "blender"


@dataclass
class ExportOptions:
    """Опции экспорта"""
    format: ExportFormat
    include_measurements: bool = True
    include_grain_lines: bool = True
    include_notches: bool = True
    include_seam_allowances: bool = True
    scale: float = 1.0
    units: str = "cm"  # cm, mm, inches


class FashionExporter:
    """Основной класс для экспорта fashion данных"""
    
    def __init__(self):
        self.exporters = {
            ExportFormat.JSON: self._export_json,
            ExportFormat.SVG: self._export_svg,
            ExportFormat.DXF: self._export_dxf,
            ExportFormat.AAMA: self._export_aama,
            ExportFormat.SEAMLY2D: self._export_seamly2d,
            ExportFormat.BLENDER: self._export_blender
        }
    
    def export_design(self, 
                     design_data: Dict[str, Any],
                     output_path: Union[str, Path],
                     options: ExportOptions) -> bool:
        """
        Экспорт дизайна
        
        Args:
            design_data: Данные дизайна
            output_path: Путь для сохранения
            options: Опции экспорта
            
        Returns:
            True если успешно
        """
        output_path = Path(output_path)
        
        try:
            exporter_func = self.exporters.get(options.format)
            if not exporter_func:
                raise ValueError(f"Unsupported format: {options.format}")
            
            result = exporter_func(design_data, options)
            
            # Сохранение результата
            if options.format == ExportFormat.JSON:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
            
            return True
            
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def export_pattern(self,
                      pattern_data: Dict[str, Any],
                      output_path: Union[str, Path],
                      options: ExportOptions) -> bool:
        """
        Экспорт лекал
        
        Args:
            pattern_data: Данные лекал
            output_path: Путь для сохранения
            options: Опции экспорта
            
        Returns:
            True если успешно
        """
        output_path = Path(output_path)
        
        try:
            exporter_func = self.exporters.get(options.format)
            if not exporter_func:
                raise ValueError(f"Unsupported format: {options.format}")
            
            result = exporter_func(pattern_data, options)
            
            # Сохранение результата
            if options.format == ExportFormat.JSON:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
            
            return True
            
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def export_pattern_to_dict(self,
                             pattern_data: Dict[str, Any],
                             options: Optional[ExportOptions] = None) -> Dict[str, Any]:
        """
        Экспорт лекал в словарь для анализа AI
        
        Args:
            pattern_data: Данные лекал
            options: Опции экспорта
            
        Returns:
            Словарь с данными лекала для анализа
        """
        if options is None:
            options = ExportOptions(format=ExportFormat.JSON)
        
        try:
            # Подготовка данных для анализа AI
            analysis_data = {
                "format": "json",
                "version": "1.0",
                "units": options.units,
                "scale": options.scale,
                "timestamp": datetime.now().isoformat(),
                "generator": "Agent-S Fashion",
                "pattern_analysis": {
                    "points_count": len(pattern_data.get("points", {})),
                    "lines_count": len(pattern_data.get("lines", {})),
                    "curves_count": len(pattern_data.get("curves", {})),
                    "points": pattern_data.get("points", {}),
                    "lines": pattern_data.get("lines", {}),
                    "curves": pattern_data.get("curves", {})
                },
                "modifications": pattern_data.get("modification_history", []),
                "skirt_modifications": pattern_data.get("skirt_modifications", {}),
                "metadata": {
                    "include_measurements": options.include_measurements,
                    "include_grain_lines": options.include_grain_lines,
                    "include_notches": options.include_notches,
                    "include_seam_allowances": options.include_seam_allowances
                }
            }
            
            return analysis_data
            
        except Exception as e:
            print(f"Export to dict error: {e}")
            return {}
    
    def export_to_svg(self, 
                     lines: List[Dict[str, Any]], 
                     output_filename: str = "pattern.svg",
                     scale_mm: float = 1.0,
                     width_mm: float = 800.0,
                     height_mm: float = 600.0,
                     scale_to_page: str = "A4",
                     full_scale: bool = True,
                     add_paper_frame: bool = True,
                     add_scale_ruler: bool = True,
                     font_size: int = 12,
                     padding: float = 30.0,
                     background: str = "white") -> str:
        """
        Экспорт списка линий в SVG файл с улучшенным форматированием
        
        Args:
            lines: Список линий в формате [{'start': {'x': 0, 'y': 0}, 'end': {'x': 100, 'y': 50}}, ...]
            output_filename: Имя выходного файла
            scale_mm: Масштаб в миллиметрах (1.0 = 1мм)
            width_mm: Ширина SVG холста в миллиметрах
            height_mm: Высота SVG холста в миллиметрах
            scale_to_page: "A4" или "A3" - подогнать под формат бумаги
            full_scale: true/false - 1:1 реальный размер или fit-to-page
            add_paper_frame: true - нарисовать рамку A4/A3
            add_scale_ruler: true - контрольная линейка 10 см в углу
            font_size: размер шрифта для текстов
            padding: отступы от краев в мм
            background: цвет фона ("white", "transparent", etc.)
            
        Returns:
            Путь к созданному SVG файлу
        """
        try:
            # Создание выходной директории
            output_dir = Path.cwd() / "output" / "fashion"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / output_filename
            
            # Расчёт bounding box и центрирование
            bbox_info = self._calculate_bounding_box(lines)
            layout_info = self._calculate_enhanced_layout(lines, bbox_info, scale_to_page, full_scale, padding)
            
            # Группировка деталей для вертикального размещения
            grouped_parts = self._group_pattern_parts(lines)
            
            # Создание SVG документа с улучшенной структурой
            svg_content = self._generate_enhanced_svg_content_v2(
                grouped_parts=grouped_parts,
                bbox_info=bbox_info,
                layout_info=layout_info,
                scale_mm=scale_mm,
                scale_to_page=scale_to_page,
                full_scale=full_scale,
                add_paper_frame=add_paper_frame,
                add_scale_ruler=add_scale_ruler,
                font_size=font_size,
                padding=padding,
                background=background
            )
            
            # Сохранение файла
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            return str(output_path)
            
        except Exception as e:
            print(f"SVG export error: {e}")
            return ""
    
    def _calculate_bounding_box(self, lines: List[Dict[str, Any]]) -> Dict[str, float]:
        """Расчёт bounding box всех деталей"""
        if not lines:
            return {"min_x": 0, "min_y": 0, "max_x": 100, "max_y": 100, "width": 100, "height": 100}
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for line in lines:
            start_x = line['start']['x']
            start_y = line['start']['y']
            end_x = line['end']['x']
            end_y = line['end']['y']
            
            min_x = min(min_x, start_x, end_x)
            min_y = min(min_y, start_y, end_y)
            max_x = max(max_x, start_x, end_x)
            max_y = max(max_y, start_y, end_y)
        
        return {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y
        }
    
    def _calculate_enhanced_layout(self, lines: List[Dict[str, Any]], bbox_info: Dict[str, float], 
                                scale_to_page: str, full_scale: bool, padding: float) -> Dict[str, Any]:
        """Расчёт улучшенного макета с масштабом 10x для пикселей"""
        
        # Размеры бумаги в мм
        paper_sizes = {
            "A4": {"width": 210, "height": 297},
            "A3": {"width": 297, "height": 420}
        }
        
        paper = paper_sizes.get(scale_to_page, paper_sizes["A4"])
        paper_width = paper["width"]
        paper_height = paper["height"]
        
        # Увеличиваем масштаб в 10 раз для пикселей
        pixel_scale = 10.0
        
        # Расчёт доступной области с учётом отступов
        available_width = (paper_width - 2 * padding) * pixel_scale
        available_height = (paper_height - 2 * padding) * pixel_scale
        
        # Расчёт масштаба
        if full_scale:
            scale = pixel_scale  # 10x для пикселей
        else:
            # Fit-to-page с сохранением пропорций
            bbox_width_pixels = bbox_info["width"] * pixel_scale
            bbox_height_pixels = bbox_info["height"] * pixel_scale
            
            scale_x = available_width / bbox_width_pixels if bbox_width_pixels > 0 else pixel_scale
            scale_y = available_height / bbox_height_pixels if bbox_height_pixels > 0 else pixel_scale
            scale = min(scale_x, scale_y, pixel_scale)  # Не увеличиваем больше 10x
        
        return {
            "paper_width": paper_width * pixel_scale,
            "paper_height": paper_height * pixel_scale,
            "scale": scale,
            "pixel_scale": pixel_scale,
            "offset_x": padding * pixel_scale,
            "offset_y": padding * pixel_scale,
            "padding": padding * pixel_scale,
            "available_width": available_width,
            "available_height": available_height
        }
    
    def _group_pattern_parts(self, lines: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Группировка линий по деталям (перед, зад, пояс)"""
        
        # Простая группировка по X координатам
        # Левая часть - зад, правая часть - перед
        front_lines = []
        back_lines = []
        waistband_lines = []
        
        if not lines:
            return {"front": front_lines, "back": back_lines, "waistband": waistband_lines}
        
        # Находим среднюю X координату
        all_x = []
        for line in lines:
            all_x.append(line['start']['x'])
            all_x.append(line['end']['x'])
        
        if not all_x:
            return {"front": front_lines, "back": back_lines, "waistband": waistband_lines}
        
        center_x = sum(all_x) / len(all_x)
        
        # Группируем линии
        for line in lines:
            line_center_x = (line['start']['x'] + line['end']['x']) / 2
            
            # Пояс - линии с Y близко к 0
            if line['start']['y'] < 5 and line['end']['y'] < 5:
                waistband_lines.append(line)
            # Перед - правая часть
            elif line_center_x > center_x:
                front_lines.append(line)
            # Зад - левая часть
            else:
                back_lines.append(line)
        
        return {
            "front": front_lines,
            "back": back_lines,
            "waistband": waistband_lines
        }
    
    def _calculate_part_bbox(self, lines: List[Dict[str, Any]]) -> Dict[str, float]:
        """Расчёт bounding box для конкретной детали"""
        if not lines:
            return {"min_x": 0, "min_y": 0, "max_x": 100, "max_y": 100, "width": 100, "height": 100}
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for line in lines:
            start_x = line['start']['x']
            start_y = line['start']['y']
            end_x = line['end']['x']
            end_y = line['end']['y']
            
            min_x = min(min_x, start_x, end_x)
            min_y = min(min_y, start_y, end_y)
            max_x = max(max_x, start_x, end_x)
            max_y = max(max_y, start_y, end_y)
        
        return {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y
        }
    
    def _generate_enhanced_svg_content_v2(self, 
                                       grouped_parts: Dict[str, List[Dict[str, Any]]],
                                       bbox_info: Dict[str, float],
                                       layout_info: Dict[str, Any],
                                       scale_mm: float,
                                       scale_to_page: str,
                                       full_scale: bool,
                                       add_paper_frame: bool,
                                       add_scale_ruler: bool,
                                       font_size: int,
                                       padding: float,
                                       background: str) -> str:
        """Генерация улучшенного SVG контента v2 с большими деталями"""
        
        layout = layout_info
        scale = layout["scale"]
        
        # Расчёт вертикального размещения деталей
        part_spacing = 100  # 100 единиц (10 мм) между деталями
        current_y = layout["offset_y"]
        
        # Расчёт bounding box для каждой детали
        front_bbox = self._calculate_part_bbox(grouped_parts.get("front", []))
        back_bbox = self._calculate_part_bbox(grouped_parts.get("back", []))
        waistband_bbox = self._calculate_part_bbox(grouped_parts.get("waistband", []))
        
        # SVG заголовок с метаданными
        svg_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
            f'<svg width="{layout["paper_width"]}" height="{layout["paper_height"]}" ',
            f'viewBox="0 0 {layout["paper_width"]} {layout["paper_height"]}" xmlns="http://www.w3.org/2000/svg">',
            '',
            '  <!--',
            '     Generated by Agent-S Fashion Module',
            '     Enhanced SVG Export v2.1 - Large & Readable',
            f'     Paper: {scale_to_page}',
            f'     Scale: {scale:.1f}x (10x for pixels)',
            f'     Units: millimeters × 10',
            f'     Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            '  -->',
            '',
            '  <!-- Белый фон -->',
            f'  <rect width="100%" height="100%" fill="{background}"/>',
            '',
            '  <!-- Стили для линий, точек и текстов -->',
            '  <defs>',
            '    <style type="text/css">',
            '      .pattern-line {',
            '        stroke: black;',
            '        stroke-width: 1;',
            '        fill: none;',
            '        stroke-linecap: round;',
            '        stroke-linejoin: round;',
            '      }',
            '      .pattern-point {',
            '        fill: black;',
            '        stroke: black;',
            '        stroke-width: 0.5;',
            '      }',
            '      .pattern-grid {',
            '        stroke: #e0e0e0;',
            '        stroke-width: 0.5;',
            '        stroke-dasharray: 5,5;',
            '      }',
            '      .paper-frame {',
            '        stroke: black;',
            '        stroke-width: 2;',
            '        fill: none;',
            '      }',
            '      .ruler-line {',
            '        stroke: black;',
            '        stroke-width: 2;',
            '      }',
            '      .ruler-text {',
            '        font-family: Arial, sans-serif;',
            '        font-size: 12pt;',
            '        fill: black;',
            '        font-weight: bold;',
            '      }',
            '      .pattern-label {',
            '        font-family: Arial, sans-serif;',
            '        font-size: 20pt;',
            '        font-weight: bold;',
            '        fill: blue;',
            '      }',
            '      .grain-line {',
            '        stroke: #0066cc;',
            '        stroke-width: 2;',
            '        stroke-dasharray: 15,5;',
            '      }',
            '    </style>',
            '  </defs>',
            ''
        ]
        
        # Рамка бумаги
        if add_paper_frame:
            svg_lines.extend([
                '  <!-- Рамка бумаги A4 -->',
                '  <rect x="0" y="0" width="100%" height="100%" class="paper-frame"/>',
                ''
            ])
        
        # Сетка (крупная для удобства)
        svg_lines.extend([
            '  <!-- Сетка для удобства -->',
            '  <g class="pattern-grid">'
        ])
        
        grid_spacing = 100  # 100 единиц (10 мм)
        for x in range(int(layout["offset_x"]), int(layout["paper_width"] - layout["offset_x"] + 1), int(grid_spacing)):
            svg_lines.append(f'    <line x1="{x}" y1="{layout["offset_y"]}" x2="{x}" y2="{layout["paper_height"] - layout["offset_y"]}" class="pattern-grid"/>')
        
        for y in range(int(layout["offset_y"]), int(layout["paper_height"] - layout["offset_y"] + 1), int(grid_spacing)):
            svg_lines.append(f'    <line x1="{layout["offset_x"]}" y1="{y}" x2="{layout["paper_width"] - layout["offset_x"]}" y2="{y}" class="pattern-grid"/>')
        
        svg_lines.extend([
            '  </g>',
            '',
            '  <!-- Детали лекала -->',
            '  <g class="pattern-parts">'
        ])
        
        # Функция для добавления детали с центрированием
        def add_part(lines, part_name, y_position):
            if not lines:
                return y_position
            
            part_bbox = self._calculate_part_bbox(lines)
            part_width = part_bbox["width"] * scale
            part_height = part_bbox["height"] * scale
            
            # Центрируем деталь горизонтально
            center_x = layout["paper_width"] / 2
            part_offset_x = center_x - (part_width / 2)
            
            # Сдвигаем деталь в начало координат
            part_offset_x -= part_bbox["min_x"] * scale
            part_offset_y = y_position - part_bbox["min_y"] * scale
            
            svg_lines.append(f'    <!-- {part_name} -->')
            svg_lines.append(f'    <g id="{part_name}">')
            
            # Добавляем линии детали
            for line in lines:
                start_x = (line['start']['x'] * scale) + part_offset_x
                start_y = (line['start']['y'] * scale) + part_offset_y
                end_x = (line['end']['x'] * scale) + part_offset_x
                end_y = (line['end']['y'] * scale) + part_offset_y
                
                # Основная линия
                svg_lines.append(f'      <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" class="pattern-line"/>')
                
                # Большие точки в начале и конце линии
                svg_lines.append(f'      <circle cx="{start_x}" cy="{start_y}" r="3" class="pattern-point"/>')
                svg_lines.append(f'      <circle cx="{end_x}" cy="{end_y}" r="3" class="pattern-point"/>')
            
            # Добавляем надпись детали
            label_x = center_x
            label_y = y_position + (part_height / 2)
            svg_lines.append(f'      <text x="{label_x}" y="{label_y}" text-anchor="middle" class="pattern-label">{part_name.upper()}</text>')
            
            # Добавляем линию зерна
            grain_y = label_y + 30
            grain_start_x = center_x - 50
            grain_end_x = center_x + 50
            svg_lines.append(f'      <line x1="{grain_start_x}" y1="{grain_y}" x2="{grain_end_x}" y2="{grain_y}" class="grain-line"/>')
            svg_lines.append(f'      <text x="{center_x}" y="{grain_y + 20}" text-anchor="middle" class="ruler-text">GRAIN LINE</text>')
            
            svg_lines.append(f'    </g>')
            svg_lines.append('')
            
            return y_position + part_height + part_spacing
        
        # Добавляем детали вертикально: перед сверху, зад снизу
        current_y = add_part(grouped_parts.get("front", []), "Front Part", current_y)
        current_y = add_part(grouped_parts.get("back", []), "Back Part", current_y)
        current_y = add_part(grouped_parts.get("waistband", []), "Waistband", current_y)
        
        svg_lines.extend([
            '  </g>',
            ''
        ])
        
        # Контрольная линейка 10 см (100 единиц)
        if add_scale_ruler:
            ruler_x = layout["paper_width"] - layout["offset_x"] - 200
            ruler_y = layout["paper_height"] - layout["offset_y"] - 50
            
            svg_lines.extend([
                '  <!-- Контрольная линейка 10 см -->',
                '  <g class="scale-ruler">',
                f'    <line x1="{ruler_x}" y1="{ruler_y}" x2="{ruler_x + 100}" y2="{ruler_y}" class="ruler-line"/>',
                f'    <line x1="{ruler_x}" y1="{ruler_y - 10}" x2="{ruler_x}" y2="{ruler_y + 10}" class="ruler-line"/>',
                f'    <line x1="{ruler_x + 100}" y1="{ruler_y - 10}" x2="{ruler_x + 100}" y2="{ruler_y + 10}" class="ruler-line"/>',
                f'    <text x="{ruler_x + 50}" y="{ruler_y - 15}" text-anchor="middle" class="ruler-text">10 cm</text>',
                '  </g>',
                ''
            ])
        
        # Метаданные SVG
        svg_lines.extend([
            '  <!-- Метаданные лекала -->',
            '  <metadata>',
            f'    <pattern-data>',
            f'      <generator>Agent-S Fashion Enhanced SVG Export v2.1</generator>',
            f'      <version>2.1</version>',
            f'      <created>{datetime.now().isoformat()}</created>',
            f'      <paper-format>{scale_to_page}</paper-format>',
            f'      <scale-multiplier>{scale:.1f}x</scale-multiplier>',
            f'      <full-scale>{full_scale}</full-scale>',
            f'      <units>millimeters × 10 (pixels)</units>',
            f'      <background>{background}</background>',
            f'      <front-lines>{len(grouped_parts.get("front", []))}</front-lines>',
            f'      <back-lines>{len(grouped_parts.get("back", []))}</back-lines>',
            f'      <waistband-lines>{len(grouped_parts.get("waistband", []))}</waistband-lines>',
            f'      <total-lines>{len(grouped_parts.get("front", [])) + len(grouped_parts.get("back", [])) + len(grouped_parts.get("waistband", []))}</total-lines>',
            f'      <layout-scale>{scale:.2f}</layout-scale>',
            f'      <pixel-scale>{layout["pixel_scale"]}</pixel-scale>',
            f'      <part-spacing>{part_spacing}</part-spacing>',
            f'    </pattern-data>',
            '  </metadata>',
            '',
            '</svg>'
        ])
        
        return '\n'.join(svg_lines)
    
    def _generate_svg_content(self, 
                            lines: List[Dict[str, Any]], 
                            scale_mm: float,
                            width_mm: float,
                            height_mm: float) -> str:
        """
        Генерация SVG контента
        
        Args:
            lines: Список линий
            scale_mm: Масштаб в миллиметрах
            width_mm: Ширина холста
            height_mm: Высота холста
            
        Returns:
            SVG контент в виде строки
        """
        # SVG заголовок с метаданными
        svg_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
            f'<svg width="{width_mm}mm" height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}" xmlns="http://www.w3.org/2000/svg">',
            '',
            '  <!--',
            '     Generated by Universal Agent Fashion Module',
            '     Compatible with Inkscape and Seamly2D',
            '     Units: millimeters',
            f'     Scale: {scale_mm}mm = 1 unit',
            '  -->',
            '',
            '  <!-- Стили для линий и точек -->',
            '  <defs>',
            '    <style type="text/css">',
            '      .pattern-line {',
            '        stroke: #000000;',
            '        stroke-width: 0.5;',
            '        fill: none;',
            '        stroke-linecap: round;',
            '        stroke-linejoin: round;',
            '      }',
            '      .pattern-point {',
            '        fill: #ff0000;',
            '        stroke: #000000;',
            '        stroke-width: 0.3;',
            '      }',
            '      .pattern-grid {',
            '        stroke: #e0e0e0;',
            '        stroke-width: 0.2;',
            '        stroke-dasharray: 2,2;',
            '      }',
            '    </style>',
            '  </defs>',
            '',
            '  <!-- Сетка для удобства -->',
            '  <g class="pattern-grid">'
        ]
        
        # Добавление сетки (каждые 50мм)
        grid_spacing = 50.0
        for x in range(0, int(width_mm) + 1, int(grid_spacing)):
            svg_lines.append(f'    <line x1="{x}" y1="0" x2="{x}" y2="{height_mm}" class="pattern-grid"/>')
        
        for y in range(0, int(height_mm) + 1, int(grid_spacing)):
            svg_lines.append(f'    <line x1="0" y1="{y}" x2="{width_mm}" y2="{y}" class="pattern-grid"/>')
        
        svg_lines.extend([
            '  </g>',
            '',
            '  <!-- Основные линии лекала -->',
            '  <g class="pattern-lines">'
        ])
        
        # Добавление линий лекала
        for i, line in enumerate(lines):
            start_x = line['start']['x'] * scale_mm
            start_y = line['start']['y'] * scale_mm
            end_x = line['end']['x'] * scale_mm
            end_y = line['end']['y'] * scale_mm
            
            # Основная линия
            svg_lines.append(f'    <line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" class="pattern-line"/>')
            
            # Точки в начале и конце линии
            svg_lines.append(f'    <circle cx="{start_x}" cy="{start_y}" r="1.5" class="pattern-point"/>')
            svg_lines.append(f'    <circle cx="{end_x}" cy="{end_y}" r="1.5" class="pattern-point"/>')
        
        svg_lines.extend([
            '  </g>',
            '',
            '  <!-- Метаданные лекала -->',
            '  <metadata>',
            f'    <pattern-data>',
            f'      <lines-count>{len(lines)}</lines-count>',
            f'      <scale-mm>{scale_mm}</scale-mm>',
            f'      <width-mm>{width_mm}</width-mm>',
            f'      <height-mm>{height_mm}</height-mm>',
            f'      <generator>Universal Agent Fashion Module</generator>',
            f'      <created>{datetime.now().isoformat()}</created>',
            f'    </pattern-data>',
            '  </metadata>',
            '',
            '</svg>'
        ])
        
        return '\n'.join(svg_lines)
    
    def _export_json(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """Экспорт в JSON формат"""
        export_data = {
            "format": "json",
            "version": "1.0",
            "units": options.units,
            "scale": options.scale,
            "timestamp": datetime.now().isoformat(),
            "generator": "Agent-S Fashion",
            "data": data,
            "ai_analysis_ready": True
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_svg(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """Экспорт в SVG формат"""
        # Создание SVG документа
        svg = ET.Element("svg")
        svg.set("xmlns", "http://www.w3.org/2000/svg")
        svg.set("width", "800")
        svg.set("height", "600")
        svg.set("viewBox", "0 0 800 600")
        
        # Добавление лекал
        if "geometry" in data:
            self._add_pattern_to_svg(svg, data["geometry"], options)
        
        # Добавление метаданных
        metadata = ET.SubElement(svg, "metadata")
        metadata.text = json.dumps({
            "format": "svg",
            "units": options.units,
            "scale": options.scale
        })
        
        return ET.tostring(svg, encoding='unicode')
    
    def _add_pattern_to_svg(self, svg: ET.Element, geometry: Dict[str, Any], options: ExportOptions):
        """Добавление лекал в SVG с группировкой и подписями"""
        
        # Создаем группы для спинки и переда
        back_group = ET.SubElement(svg, "g")
        back_group.set("id", "back")
        
        front_group = ET.SubElement(svg, "g")
        front_group.set("id", "front")
        
        # Добавление линий с группировкой
        if "lines" in geometry:
            for line_name, line_data in geometry["lines"].items():
                # Определяем группу по имени линии
                if "back" in line_name.lower():
                    parent_group = back_group
                    stroke_color = "blue"
                elif "front" in line_name.lower():
                    parent_group = front_group
                    stroke_color = "red"
                else:
                    parent_group = svg
                    stroke_color = "black"
                
                line = ET.SubElement(parent_group, "line")
                line.set("x1", str(line_data["start"]["x"] * options.scale))
                line.set("y1", str(line_data["start"]["y"] * options.scale))
                line.set("x2", str(line_data["end"]["x"] * options.scale))
                line.set("y2", str(line_data["end"]["y"] * options.scale))
                line.set("stroke", stroke_color)
                line.set("stroke-width", "1")
                line.set("id", line_name)
        
        # Добавление кривых с группировкой
        if "curves" in geometry:
            for curve_name, curve_data in geometry["curves"].items():
                # Определяем группу по имени кривой
                if "back" in curve_name.lower():
                    parent_group = back_group
                    stroke_color = "blue"
                elif "front" in curve_name.lower():
                    parent_group = front_group
                    stroke_color = "red"
                else:
                    parent_group = svg
                    stroke_color = "black"
                
                path = ET.SubElement(parent_group, "path")
                d = f"M {curve_data['start']['x'] * options.scale} {curve_data['start']['y'] * options.scale} "
                d += f"C {curve_data['control1']['x'] * options.scale} {curve_data['control1']['y'] * options.scale}, "
                d += f"{curve_data['control2']['x'] * options.scale} {curve_data['control2']['y'] * options.scale}, "
                d += f"{curve_data['end']['x'] * options.scale} {curve_data['end']['y'] * options.scale}"
                path.set("d", d)
                path.set("stroke", stroke_color)
                path.set("stroke-width", "1")
                path.set("fill", "none")
                path.set("id", curve_name)
        
        # Добавление точек с группировкой
        if "points" in geometry:
            for point_name, point_data in geometry["points"].items():
                # Определяем группу по имени точки
                if "back" in point_name.lower():
                    parent_group = back_group
                    fill_color = "blue"
                elif "front" in point_name.lower():
                    parent_group = front_group
                    fill_color = "red"
                else:
                    parent_group = svg
                    fill_color = "black"
                
                circle = ET.SubElement(parent_group, "circle")
                circle.set("cx", str(point_data["x"] * options.scale))
                circle.set("cy", str(point_data["y"] * options.scale))
                circle.set("r", "2")
                circle.set("fill", fill_color)
                circle.set("id", point_name)
        
        # Добавляем текстовые подписи
        # Подпись для спинки
        back_text = ET.SubElement(back_group, "text")
        back_text.set("x", "10")
        back_text.set("y", "30")
        back_text.set("font-family", "Arial, sans-serif")
        back_text.set("font-size", "14")
        back_text.set("font-weight", "bold")
        back_text.set("fill", "blue")
        back_text.text = "BACK"
        
        # Подпись для переда
        front_text = ET.SubElement(front_group, "text")
        front_text.set("x", "10")
        front_text.set("y", "30")
        front_text.set("font-family", "Arial, sans-serif")
        front_text.set("font-size", "14")
        front_text.set("font-weight", "bold")
        front_text.set("fill", "red")
        front_text.text = "FRONT"
    
    def _export_dxf(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """Экспорт в DXF формат с правильными замкнутыми полилиниями"""
        dxf_header = """0
SECTION
2
HEADER
9
$INSUNITS
70
4
0
ENDSEC
0
SECTION
2
TABLES
0
TABLE
2
LAYER
70
4
0
LAYER
2
MAIN_CONTOUR
70
0
62
7
420
0
LAYER
2
SEAM_ALLOWANCE
70
2
62
1
420
0
LAYER
2
AXES
70
3
62
2
420
0
LAYER
2
ANNOTATIONS
70
4
62
3
420
0
ENDTAB
0
SECTION
2
ENTITIES
"""
        
        dxf_footer = """0
ENDSEC
0
EOF"""
        
        entities = []
        
        # Собираем все сегменты для построения графа
        segments = []
        points_dict = {}
        
        # Извлекаем линии
        if "geometry" in data and "lines" in data["geometry"]:
            for line_name, line_data in data["geometry"]["lines"].items():
                start = (line_data["start"]["x"] * options.scale, line_data["start"]["y"] * options.scale)
                end = (line_data["end"]["x"] * options.scale, line_data["end"]["y"] * options.scale)
                segments.append((start, end))
                points_dict[start] = True
                points_dict[end] = True
        
        # Извлекаем сплайны (если есть)
        if "geometry" in data and "splines" in data["geometry"]:
            for spline_name, spline_data in data["geometry"]["splines"].items():
                # Преобразуем сплайн в сегменты
                control_points = spline_data.get("control_points", [])
                for i in range(len(control_points) - 1):
                    start = (control_points[i][0] * options.scale, control_points[i][1] * options.scale)
                    end = (control_points[i+1][0] * options.scale, control_points[i+1][1] * options.scale)
                    segments.append((start, end))
                    points_dict[start] = True
                    points_dict[end] = True
        
        # Строим граф соединений
        graph = {}
        for start, end in segments:
            if start not in graph:
                graph[start] = []
            if end not in graph:
                graph[end] = []
            graph[start].append(end)
            graph[end].append(start)
        
        # Находим замкнутые контуры
        visited = set()
        contours = []
        
        for point in graph:
            if point in visited:
                continue
                
            # Ищем контур
            contour = [point]
            visited.add(point)
            current = point
            
            while True:
                neighbors = graph[current]
                next_point = None
                
                for neighbor in neighbors:
                    if neighbor not in visited:
                        next_point = neighbor
                        break
                
                if next_point is None:
                    break
                    
                contour.append(next_point)
                visited.add(next_point)
                current = next_point
                
                # Проверяем замыкание
                if len(contour) > 2 and self._same_point(contour[0], current):
                    break
            
            # Если контур замкнутый (более 2 точек и замыкается)
            if len(contour) > 2 and self._same_point(contour[0], contour[-1]):
                contours.append(contour)
        
        # Создаем POLYLINE для каждого замкнутого контура
        for i, contour in enumerate(contours):
            if len(contour) < 3:
                continue
                
            # Формируем POLYLINE
            polyline = f"""0
POLYLINE
8
MAIN_CONTOUR
66
1
70
0
40
0.0
"""
            
            # Добавляем вершины
            for point in contour:
                x, y = point
                polyline += f"""0
VERTEX
8
MAIN_CONTOUR
10
{x:.6f}
20
{y:.6f}
30
0.0
"""
            
            # Закрываем POLYLINE
            polyline += """0
SEQEND
"""
            
            entities.append(polyline)
        
        # Seam Allowance (если есть)
        if options.include_seam_allowances and "geometry" in data and "seam_allowance" in data["geometry"]:
            for seam_name, seam_data in data["geometry"]["seam_allowance"].items():
                start = (seam_data["x"] * options.scale, seam_data["y"] * options.scale)
                end = (seam_data["end_x"] * options.scale, seam_data["end_y"] * options.scale)
                
                # Создаем POLYLINE для припуска
                seam_polyline = f"""0
POLYLINE
8
SEAM_ALLOWANCE
66
1
70
0
40
0.0
0
VERTEX
8
SEAM_ALLOWANCE
10
{start[0]:.6f}
20
{start[1]:.6f}
30
0.0
0
VERTEX
8
SEAM_ALLOWANCE
10
{end[0]:.6f}
20
{end[1]:.6f}
30
0.0
0
SEQEND
"""
                entities.append(seam_polyline)
        
        # Notches (метки)
        if options.include_notches and "geometry" in data and "notches" in data["geometry"]:
            for notch_name, notch_data in data["geometry"]["notches"].items():
                x = notch_data["x"] * options.scale
                y = notch_data["y"] * options.scale
                
                entities.append(f"""0
LINE
8
ANNOTATIONS
10
{x}
20
{y}
11
{x + 10}
21
{y}
""")
        
        # Grain lines (оси)
        if options.include_grain_lines and "geometry" in data and "grain_lines" in data["geometry"]:
            for grain_name, grain_data in data["geometry"]["grain_lines"].items():
                start_x = grain_data["start"]["x"] * options.scale
                start_y = grain_data["start"]["y"] * options.scale
                end_x = grain_data["end"]["x"] * options.scale
                end_y = grain_data["end"]["y"] * options.scale
                
                entities.append(f"""0
LINE
8
AXES
10
{start_x}
20
{start_y}
11
{end_x}
21
{end_y}
""")
                
                # Текст grain line
                text_x = (start_x + end_x) / 2
                text_y = (start_y + end_y) / 2 + 20
                
                entities.append(f"""0
TEXT
8
ANNOTATIONS
10
{text_x}
20
{text_y}
40
2.5
1
0
GRAIN LINE
""")
        
        return dxf_header + "".join(entities) + dxf_footer
    
    def _same_point(self, a, b, eps=1e-3):
        """Проверяет совпадение точек с допуском"""
        return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps
    
    def export_assembly_svg(self, layout: Dict[str, Any]) -> str:
        """
        Экспорт общей картины на A3 (viewBox "0 0 420 297 mm"), с центрированием и отступами
        
        Args:
            layout: Layout с assembly данными
            
        Returns:
            SVG строка для общей картины
        """
        if 'assembly' not in layout:
            return ""
        
        assembly = layout['assembly']
        parts = assembly.get('parts', [])
        alignment_lines = assembly.get('alignment_lines', [])
        notches = assembly.get('notches', [])
        labels = assembly.get('labels', [])
        
        # A3 размеры в мм
        a3_width = 420
        a3_height = 297
        
        # Отступы
        margin = 20
        
        # Вычисляем общие границы
        all_x = []
        all_y = []
        
        for part in parts:
            for point in part.get('points', {}).values():
                all_x.append(point['x'])
                all_y.append(point['y'])
        
        for notch in notches:
            all_x.append(notch['x'])
            all_y.append(notch['y'])
        
        for label in labels:
            all_x.append(label['x'])
            all_y.append(label['y'])
        
        if not all_x or not all_y:
            return ""
        
        min_x = min(all_x)
        max_x = max(all_x)
        min_y = min(all_y)
        max_y = max(all_y)
        
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        # Масштабирование для A3
        scale_x = (a3_width - 2 * margin) / content_width
        scale_y = (a3_height - 2 * margin) / content_height
        scale = min(scale_x, scale_y, 1.0)  # Не увеличиваем, только уменьшаем
        
        # Центрирование
        offset_x = margin + (a3_width - 2 * margin - content_width * scale) / 2
        offset_y = margin + (a3_height - 2 * margin - content_height * scale) / 2
        
        # Создаем SVG
        svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{a3_width}mm" height="{a3_height}mm" viewBox="0 0 {a3_width} {a3_height}" xmlns="http://www.w3.org/2000/svg">
<defs>
    <style>
        .pattern-line {{ stroke: #000; stroke-width: 0.5; fill: none; }}
        .pattern-curve {{ stroke: #000; stroke-width: 0.5; fill: none; }}
        .alignment-line {{ stroke: #666; stroke-width: 0.3; stroke-dasharray: 2,2; fill: none; }}
        .notch {{ stroke: #f00; stroke-width: 0.8; fill: none; }}
        .label-title {{ font-family: Arial, sans-serif; font-size: 12pt; font-weight: bold; fill: #000; }}
        .label-part {{ font-family: Arial, sans-serif; font-size: 8pt; fill: #333; }}
        .part-outline {{ stroke: #000; stroke-width: 0.3; fill: #f0f0f0; opacity: 0.3; }}
    </style>
</defs>
"""
        
        # Фон
        svg_content += f"""<rect x="0" y="0" width="{a3_width}" height="{a3_height}" fill="white"/>
<rect x="{margin}" y="{margin}" width="{a3_width - 2*margin}" height="{a3_height - 2*margin}" fill="white" stroke="#ccc" stroke-width="0.5"/>
"""
        
        # Части паттерна
        for part in parts:
            part_name = part['part_name']
            
            # Заливка части
            if part.get('points'):
                points_str = " ".join([
                    f"{(p['x'] - min_x) * scale + offset_x},{(p['y'] - min_y) * scale + offset_y}"
                    for p in part['points'].values()
                ])
                svg_content += f'<polygon points="{points_str}" class="part-outline"/>\n'
            
            # Линии
            for line_name, line_data in part.get('lines', {}).items():
                x1 = (line_data['start']['x'] - min_x) * scale + offset_x
                y1 = (line_data['start']['y'] - min_y) * scale + offset_y
                x2 = (line_data['end']['x'] - min_x) * scale + offset_x
                y2 = (line_data['end']['y'] - min_y) * scale + offset_y
                
                svg_content += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="pattern-line"/>\n'
            
            # Кривые (упрощенно как линии)
            for curve_name, curve_data in part.get('curves', {}).items():
                # Проверяем формат curve_data
                if isinstance(curve_data, dict):
                    # Получаем координаты по именам точек
                    start_name = curve_data.get('start')
                    end_name = curve_data.get('end')
                    
                    # Ищем координаты в points
                    start_point = part.get('points', {}).get(start_name)
                    end_point = part.get('points', {}).get(end_name)
                    
                    if start_point and end_point:
                        # Для простоты рисуем как линию от start до end
                        start_x = (start_point['x'] - min_x) * scale + offset_x
                        start_y = (start_point['y'] - min_y) * scale + offset_y
                        end_x = (end_point['x'] - min_x) * scale + offset_x
                        end_y = (end_point['y'] - min_y) * scale + offset_y
                        
                        svg_content += f'<line x1="{start_x}" y1="{start_y}" x2="{end_x}" y2="{end_y}" class="pattern-curve"/>\n'
                    else:
                        # Пропускаем если точки не найдены
                        continue
                else:
                    # Пропускаем нестандартный формат
                    continue
        
        # Линии совмещения
        for line in alignment_lines:
            x1 = (line['start']['x'] - min_x) * scale + offset_x
            y1 = (line['start']['y'] - min_y) * scale + offset_y
            x2 = (line['end']['x'] - min_x) * scale + offset_x
            y2 = (line['end']['y'] - min_y) * scale + offset_y
            
            svg_content += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="alignment-line"/>\n'
        
        # Notches
        for notch in notches:
            x = (notch['x'] - min_x) * scale + offset_x
            y = (notch['y'] - min_y) * scale + offset_y
            
            # Notch как крестик
            size = 3
            svg_content += f'<line x1="{x-size}" y1="{y}" x2="{x+size}" y2="{y}" class="notch"/>\n'
            svg_content += f'<line x1="{x}" y1="{y-size}" x2="{x}" y2="{y+size}" class="notch"/>\n'
        
        # Метки
        for label in labels:
            x = (label['x'] - min_x) * scale + offset_x
            y = (label['y'] - min_y) * scale + offset_y
            
            css_class = "label-title" if label.get('size') == 'large' else "label-part"
            svg_content += f'<text x="{x}" y="{y}" text-anchor="middle" class="{css_class}">{label["text"]}</text>\n'
        
        # Информация о сборке
        metadata = assembly.get('metadata', {})
        info_text = f"Parts: {metadata.get('total_parts', 0)} | Layout: {metadata.get('layout_width', 0):.1f} x {metadata.get('layout_height', 0):.1f} mm"
        svg_content += f'<text x="{a3_width/2}" y="{a3_height - 5}" text-anchor="middle" class="label-part">{info_text}</text>\n'
        
        svg_content += "</svg>"
        
        return svg_content
    
    def preview_3d_assembly(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        """
        3D предпросмотр сборки на аватаре (базовый манекен)
        
        Args:
            layout: Layout с assembly данными
            
        Returns:
            Dict с 3D данными для рендера
        """
        if 'assembly' not in layout:
            return {"error": "No assembly data found"}
        
        assembly = layout['assembly']
        parts = assembly.get('parts', [])
        
        # Базовый манекен (упрощенный)
        avatar_data = {
            "type": "human_avatar",
            "gender": "female",  # Можно определить из типа паттерна
            "measurements": {
                "height": 1680,  # мм
                "bust": 900,
                "waist": 680,
                "hips": 940
            },
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0}
        }
        
        # Конвертация частей в 3D
        parts_3d = []
        for part in parts:
            part_name = part['part_name']
            points = part.get('points', {})
            
            if not points:
                continue
            
            # Определяем позицию на теле
            if 'front' in part_name.lower():
                position = {"x": 0, "y": 400, "z": 100}  # Передняя часть
            elif 'back' in part_name.lower():
                position = {"x": 0, "y": 400, "z": -100}  # Задняя часть
            elif 'waistband' in part_name.lower():
                position = {"x": 0, "y": 600, "z": 0}  # Пояс
            else:
                position = {"x": 0, "y": 400, "z": 0}  # По умолчанию
            
            # Создаем 3D меш из 2D точек
            vertices = []
            for point_name, point_data in points.items():
                # Конвертируем 2D в 3D (X,Y -> X,Z) с масштабированием
                vertices.append({
                    "x": point_data['x'] * 0.1,  # мм в см
                    "y": position['y'],
                    "z": point_data['y'] * 0.1
                })
            
            # Создаем грани (упрощенно)
            faces = []
            if len(vertices) >= 3:
                # Триангуляция простая
                for i in range(1, len(vertices) - 1):
                    faces.append([0, i, i + 1])
            
            part_3d = {
                "name": part_name,
                "type": "pattern_piece",
                "vertices": vertices,
                "faces": faces,
                "position": position,
                "rotation": {"x": 0, "y": 0, "z": 0},
                "material": {
                    "color": "#f0f0f0",
                    "opacity": 0.8,
                    "wireframe": True
                }
            }
            
            parts_3d.append(part_3d)
        
        # Освещение и камера
        scene_data = {
            "camera": {
                "position": {"x": 500, "y": 800, "z": 500},
                "target": {"x": 0, "y": 600, "z": 0},
                "type": "perspective"
            },
            "lights": [
                {
                    "type": "directional",
                    "position": {"x": 1000, "y": 1000, "z": 1000},
                    "intensity": 0.8,
                    "color": "#ffffff"
                },
                {
                    "type": "ambient",
                    "intensity": 0.3,
                    "color": "#ffffff"
                }
            ]
        }
        
        return {
            "avatar": avatar_data,
            "parts": parts_3d,
            "scene": scene_data,
            "metadata": {
                "total_parts": len(parts_3d),
                "assembly_type": "3d_preview",
                "render_engine": "basic_threejs"
            }
        }
    
    def _export_aama(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """Экспорт в AAMA/ASTM формат"""
        aama_data = {
            "format": "AAMA",
            "version": "2.1",
            "units": options.units,
            "patterns": []
        }
        
        if "geometry" in data:
            pattern = {
                "name": data.get("id", "pattern1"),
                "pieces": []
            }
            
            # Конвертация геометрии в AAMA формат
            if "lines" in data["geometry"]:
                for line_name, line_data in data["geometry"]["lines"].items():
                    piece = {
                        "type": "line",
                        "name": line_name,
                        "points": [
                            line_data["start"],
                            line_data["end"]
                        ]
                    }
                    pattern["pieces"].append(piece)
            
            aama_data["patterns"].append(pattern)
        
        return json.dumps(aama_data, indent=2)
    
    def _export_seamly2d(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """Экспорт в Seamly2D формат (.val)"""
        val_content = []
        
        # Заголовок файла
        val_content.append("<?xml version='1.0' encoding='UTF-8'?>")
        val_content.append("<pattern>")
        val_content.append(f"  <name>{data.get('id', 'pattern1')}</name>")
        val_content.append(f"  <description>Generated by Universal Agent</description>")
        val_content.append("  <measurements>")
        
        # Добавление мерок
        if "measurements" in data:
            for key, value in data["measurements"].items():
                val_content.append(f"    <measurement name='{key}' value='{value}'/>")
        
        val_content.append("  </measurements>")
        val_content.append("  <pieces>")
        
        # Добавление лекал
        if "geometry" in data and "lines" in data["geometry"]:
            piece_id = 0
            for line_name, line_data in data["geometry"]["lines"].items():
                val_content.append(f"    <piece id='{piece_id}'>")
                val_content.append(f"      <name>{line_name}</name>")
                val_content.append(f"      <points>")
                val_content.append(f"        <point x='{line_data['start']['x']}' y='{line_data['start']['y']}'/>")
                val_content.append(f"        <point x='{line_data['end']['x']}' y='{line_data['end']['y']}'/>")
                val_content.append(f"      </points>")
                val_content.append(f"    </piece>")
                piece_id += 1
        
        val_content.append("  </pieces>")
        val_content.append("</pattern>")
        
        return "\n".join(val_content)
    
    def _export_blender(self, data: Dict[str, Any], options: ExportOptions) -> str:
        """Экспорт в Blender Python скрипт"""
        scale = options.scale
        
        blender_script = """
import bpy
import json

def create_pattern_from_data(data):
    '''Создание 3D модели из данных лекал'''
    
    # Очистка сцены
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    scale = """ + str(scale) + """
    
    # Создание линий лекал
"""
        
        if "geometry" in data and "lines" in data["geometry"]:
            blender_script += "    lines = data['geometry']['lines']\n"
            blender_script += "    for line_name, line_data in lines.items():\n"
            blender_script += "        # Создание кривой для линии\n"
            blender_script += "        bpy.ops.curve.primitive_bezier_curve_add(\n"
            blender_script += "            location=(0, 0, 0)\n"
            blender_script += "        )\n"
            blender_script += "        obj = bpy.context.active_object\n"
            blender_script += "        obj.name = line_name\n"
            blender_script += "        # Настройка точек\n"
            blender_script += "        obj.data.splines[0].bezier_points[0].co = (\n"
            blender_script += "            line_data['start']['x'] * scale,\n"
            blender_script += "            line_data['start']['y'] * scale,\n"
            blender_script += "            0\n"
            blender_script += "        )\n"
            blender_script += "        obj.data.splines[0].bezier_points[1].co = (\n"
            blender_script += "            line_data['end']['x'] * scale,\n"
            blender_script += "            line_data['end']['y'] * scale,\n"
            blender_script += "            0\n"
            blender_script += "        )\n"
        
        # Добавление кривых
        if "geometry" in data and "curves" in data["geometry"]:
            blender_script += "    # Создание кривых\n"
            for curve_name, curve_data in data["geometry"]["curves"].items():
                blender_script += f"""
    # Кривая {curve_name}
    bpy.ops.curve.primitive_bezier_curve_add(
        location=({curve_data['start']['x'] * scale}, {curve_data['start']['y'] * scale}, 0)
    )
    obj = bpy.context.active_object
    obj.name = "{curve_name}"
    # Настройка контрольных точек
    obj.data.splines[0].bezier_points[0].co = ({curve_data['control1']['x'] * scale}, {curve_data['control1']['y'] * scale}, 0)
    obj.data.splines[0].bezier_points[1].co = ({curve_data['control2']['x'] * scale}, {curve_data['control2']['y'] * scale}, 0)
"""
        
        blender_script += """
# Выполнение создания
create_pattern_from_data(""" + json.dumps(data) + """)
print("3D модель создана успешно!")
"""
        
        return blender_script
    
    def batch_export(self,
                    items: List[Dict[str, Any]],
                    output_dir: Union[str, Path],
                    options: ExportOptions) -> Dict[str, bool]:
        """
        Пакетный экспорт
        
        Args:
            items: Список данных для экспорта
            output_dir: Директория для сохранения
            options: Опции экспорта
            
        Returns:
            Словарь с результатами экспорта
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for i, item in enumerate(items):
            item_type = item.get("type", "unknown")
            item_id = item.get("id", f"item_{i}")
            
            filename = f"{item_id}.{options.format.value}"
            output_path = output_dir / filename
            
            if item_type == "design":
                success = self.export_design(item, output_path, options)
            elif item_type == "pattern":
                success = self.export_pattern(item, output_path, options)
            else:
                success = self.export_design(item, output_path, options)
            
            results[item_id] = success
        
        return results
    
    def get_supported_formats(self) -> List[ExportFormat]:
        """Получить список поддерживаемых форматов"""
        return list(self.exporters.keys())
    
    def validate_export_data(self, data: Dict[str, Any], format: ExportFormat) -> bool:
        """Валидация данных для экспорта"""
        required_fields = ["id", "type"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        # Специфическая валидация для форматов
        if format in [ExportFormat.SVG, ExportFormat.DXF, ExportFormat.SEAMLY2D]:
            if "geometry" not in data:
                return False
        
        return True
