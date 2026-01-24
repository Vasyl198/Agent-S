"""
Fashion инструменты для работы с дизайном одежды, лекалами и CAD системами
"""
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from ..fashion import (
    GarmentType, DesignStyle, FashionDesigner, 
    PatternMaker, FashionExporter, CADBridge, CADSystem
)
from ..fashion.exporters import ExportOptions, ExportFormat
from ..fashion.grading import PatternGrader, grade_pattern, export_graded_svg
from ..fashion.seamly_exporter import SeamlyExporter, export_to_seamly
from ..fashion.fit_analyzer import FitAnalyzer, check_armhole_vs_sleeve, check_balance, check_shoulder_slope, validate_pattern, validate_pattern_with_dataset
from ..fashion.seam_allowance import SeamAllowance, add_seam_allowances, create_standard_allowances, validate_piece_indices
from ..fashion.style_engine import StyleEngine, apply_style, get_style_preview
from ..fashion.text_design_interface import TextDesignInterface, interpret_design_request, apply_text_modifications

# Опциональная интеграция с датасетом
try:
    from ..fashion.dataset_integration import DatasetIntegration, DatasetConfig
    from ..config import CONFIG
    DATASET_AVAILABLE = True
except ImportError:
    DATASET_AVAILABLE = False


class FashionTools:
    """Fashion инструменты для работы с дизайном одежды"""
    
    def __init__(self):
        """Инициализация fashion инструментов"""
        self.fashion_designer = FashionDesigner()
        self.pattern_maker = PatternMaker()
        self.fashion_exporter = FashionExporter()
        self.cad_bridge = CADBridge()
        self.pattern_grader = PatternGrader()
        self.seamly_exporter = SeamlyExporter()
        self.fit_analyzer = FitAnalyzer()
        self.seam_allowance = SeamAllowance()
        self.style_engine = StyleEngine()
        self.text_design_interface = TextDesignInterface()
        
        # Инициализация датасета (если доступен)
        self.dataset_integration = None
        if DATASET_AVAILABLE:
            try:
                fashion_config = CONFIG.get('fashion', {})
                dataset_config = DatasetConfig(
                    dataset_path=fashion_config.get('dataset_path', ''),
                    index_path=fashion_config.get('dataset_index_path', ''),
                    metadata_path=fashion_config.get('dataset_metadata_path', ''),
                    embedding_model=fashion_config.get('embedding_model', 'all-MiniLM-L6-v2'),
                    max_patterns=fashion_config.get('max_dataset_patterns', 1000)
                )
                self.dataset_integration = DatasetIntegration(dataset_config)
                logging.info("Dataset integration enabled for FashionTools")
            except Exception as e:
                logging.warning(f"Failed to initialize dataset integration: {e}")
                self.dataset_integration = None
    
    def design_clothing(self, 
                       garment_type: str,
                       style: str,
                       measurements: Dict[str, float],
                       output_formats: List[str] = None,
                       cad: str = None,
                       use_dataset_reference: bool = False,
                       generate_assembly: bool = False) -> Dict[str, Any]:
        """
        Создает дизайн одежды с лекалами и экспортом в CAD системы
        
        Args:
            garment_type: Тип одежды (dress, shirt, pants, skirt, etc.)
            style: Стиль (casual, formal, sport, evening, business, vintage, modern)
            measurements: Словарь с мерками (bust, waist, hips, height, etc.)
            output_formats: Список форматов для экспорта (json, svg, dxf, seamly2d, blender)
            cad: CAD система для интеграции (seamly2d, blender, autocad, inkscape)
            use_dataset_reference: Использовать примеры из датасета как референсы
            generate_assembly: Создать общую картину изделия
            
        Returns:
            Dict с результатом выполнения
        """
        try:
            # Если запрошены референсы из датасета, получаем их сначала
            reference_patterns = []
            if use_dataset_reference and self.dataset_integration:
                try:
                    reference_patterns = self.dataset_integration.get_reference_examples(
                        clothing_type=garment_type, 
                        num=5  # Используем 5 референсов как просили
                    )
                    logging.info(f"Loaded {len(reference_patterns)} reference patterns for {garment_type}")
                    
                    # Усредняем референсы и адаптируем под мерки
                    if reference_patterns:
                        averaged_pattern = self.dataset_integration.average_reference_patterns(
                            reference_patterns, 
                            measurements
                        )
                        
                        # Добавляем усредненный паттерн в референсы
                        reference_patterns.insert(0, averaged_pattern)
                        logging.info(f"Created averaged pattern from {len(reference_patterns)-1} references")
                        
                except Exception as e:
                    logging.warning(f"Failed to load reference patterns: {e}")
            
            # Конвертация параметров в enum типы
            garment_enum = GarmentType(garment_type.lower())
            style_enum = DesignStyle(style.lower())
            
            # Создание дизайна
            design_id = self.fashion_designer.create_design(
                garment_type=garment_enum,
                style=style_enum,
                measurements=measurements
            )
            
            design_data = self.fashion_designer.get_design(design_id)
            if not design_data:
                return {
                    'success': False,
                    'error': 'Не удалось создать дизайн'
                }
            
            # Создание лекал
            patterns = []
            pattern_types = self._get_pattern_types_for_garment(garment_enum)
            
            # Добавляем garment_type в мерки для правильного выбора метода конструирования
            enhanced_measurements = measurements.copy()
            enhanced_measurements["garment_type"] = garment_type
            
            # Добавляем референсы в мерки (если доступны)
            if reference_patterns:
                enhanced_measurements["reference_patterns"] = reference_patterns
            
            for pattern_type in pattern_types:
                pattern_data = self.pattern_maker.create_basic_pattern(
                    pattern_type=pattern_type,
                    measurements=enhanced_measurements  # Используем enhanced_measurements с garment_type и референсами
                )
                if pattern_data:
                    patterns.append(pattern_data)
            
            # Настройка форматов экспорта
            if output_formats is None:
                output_formats = ['json', 'svg']
            
            # Экспорт файлов
            exported_files = []
            export_dir = Path.cwd() / 'fashion_exports' / design_id
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Опции экспорта по умолчанию
            default_options = ExportOptions(
                format=ExportFormat.SVG,
                include_measurements=True,
                include_grain_lines=True,
                include_notches=True
            )
            
            # Экспорт дизайна
            for format_name in output_formats:
                try:
                    export_format = ExportFormat(format_name)
                    options = ExportOptions(
                        format=export_format,
                        include_measurements=True,
                        include_grain_lines=True,
                        include_notches=True
                    )
                    
                    design_file = export_dir / f"design.{format_name}"
                    self.fashion_exporter.export_design(design_data, design_file, options)
                    exported_files.append(str(design_file))
                except ValueError:
                    # Пропускаем неподдерживаемые форматы
                    continue
            
            # Экспорт лекал
            for i, pattern in enumerate(patterns):
                # Экспорт в каждый запрошенный формат
                for format_name in output_formats:
                    try:
                        export_format = ExportFormat(format_name)
                        
                        if format_name == 'svg':
                            # Улучшенный SVG экспорт с опциями по умолчанию
                            options = ExportOptions(
                                format=export_format,
                                include_measurements=True,
                                include_grain_lines=True,
                                include_notches=True
                            )
                            
                            pattern_file = export_dir / f"pattern_{i+1}.{format_name}"
                            
                            # Обработка новой структуры build_shirt_base
                            if isinstance(pattern, dict) and 'back' in pattern and 'front' in pattern:
                                # Конвертируем новую структуру в старую
                                converted_pattern = {
                                    "points": {},
                                    "lines": {},
                                    "curves": {}
                                }
                                
                                # Объединяем все точки
                                all_points = {}
                                for part_name in ['back', 'front']:
                                    if part_name in pattern and isinstance(pattern[part_name], list):
                                        for line_data in pattern[part_name]:
                                            if 'start' in line_data:
                                                start_point = line_data['start']
                                                if isinstance(start_point, dict):
                                                    all_points[f"{part_name}_start_{len(all_points)}"] = start_point
                                            if 'end' in line_data:
                                                end_point = line_data['end']
                                                if isinstance(end_point, dict):
                                                    all_points[f"{part_name}_end_{len(all_points)}"] = end_point
                                
                                converted_pattern["points"] = all_points
                                
                                # Объединяем все линии
                                all_lines = {}
                                line_index = 0
                                for part_name in ['back', 'front']:
                                    if part_name in pattern and isinstance(pattern[part_name], list):
                                        for line_data in pattern[part_name]:
                                            if isinstance(line_data, dict) and 'start' in line_data and 'end' in line_data:
                                                all_lines[f"line_{line_index}"] = {
                                                    "start": line_data["start"],
                                                    "end": line_data["end"]
                                                }
                                                line_index += 1
                                
                                converted_pattern["lines"] = all_lines
                                
                                # Создаем структуру с geometry для экспортера
                                export_data = {
                                    "geometry": converted_pattern,
                                    "metadata": {
                                        "pattern_type": pattern.get("pattern_type", "unknown"),
                                        "pattern_index": i,
                                        "format": format_name
                                    }
                                }
                                
                                # Используем улучшенный SVG экспорт
                                lines_list = list(converted_pattern["lines"].values())
                                svg_path = self.fashion_exporter.export_to_svg(
                                    lines=lines_list,
                                    output_filename=f"pattern_{i+1}.svg",
                                    scale_to_page="A4",
                                    full_scale=False,
                                    add_paper_frame=True,
                                    add_scale_ruler=True,
                                    font_size=12,
                                    padding=30.0
                                )
                                if svg_path:
                                    exported_files.append(svg_path)
                            else:
                                # Старый формат для совместимости
                                lines_list = list(pattern.get("lines", {}).values())
                                svg_path = self.fashion_exporter.export_to_svg(
                                    lines=lines_list,
                                    output_filename=f"pattern_{i+1}.svg",
                                    scale_to_page="A4",
                                    full_scale=False,
                                    add_paper_frame=True,
                                    add_scale_ruler=True,
                                    font_size=12,
                                    padding=30.0
                                )
                                if svg_path:
                                    exported_files.append(svg_path)
                        else:
                            # Другие форматы (JSON и др.)
                            options = ExportOptions(
                                format=export_format,
                                include_measurements=True,
                                include_grain_lines=True,
                                include_notches=True
                            )
                            
                            pattern_file = export_dir / f"pattern_{i+1}.{format_name}"
                            
                            if format_name == 'json':
                                # Для JSON используем специальный метод для анализа AI
                                analysis_data = self.fashion_exporter.export_pattern_to_dict(pattern, options)
                                with open(pattern_file, 'w', encoding='utf-8') as f:
                                    json.dump(analysis_data, f, indent=2, ensure_ascii=False)
                                exported_files.append(str(pattern_file))
                            else:
                                self.fashion_exporter.export_pattern(pattern, pattern_file, options)
                                exported_files.append(str(pattern_file))
                                
                    except ValueError:
                        # Пропускаем неподдерживаемые форматы
                        continue
            
            # Интеграция с CAD если указана
            cad_result = None
            if cad:
                try:
                    cad_system = CADSystem(cad.lower())
                    
                    # Импорт дизайна в CAD
                    cad_result = self.cad_bridge.import_to_cad(
                        cad_system=cad_system,
                        data=design_data,
                        import_format="json"
                    )
                except ValueError:
                    cad_result = {"error": f"Неподдерживаемая CAD система: {cad}"}
            
            # Создание общей картины если запрошено
            assembly_result = None
            if generate_assembly and patterns:
                try:
                    # Собираем все части в layout
                    assembly_layout = self.pattern_maker.assemble_full_pattern(patterns)
                    
                    # Экспорт assembly в SVG
                    if 'assembly' in assembly_layout:
                        assembly_svg = self.fashion_exporter.export_assembly_svg(assembly_layout)
                        if assembly_svg:
                            assembly_svg_path = export_dir / "assembly.svg"
                            with open(assembly_svg_path, 'w', encoding='utf-8') as f:
                                f.write(assembly_svg)
                            assembly_result = {
                                'assembly_layout': assembly_layout,
                                'assembly_svg': str(assembly_svg_path),
                                'parts_count': assembly_layout['assembly']['metadata']['total_parts'],
                                'layout_size': f"{assembly_layout['assembly']['metadata']['layout_width']:.1f} x {assembly_layout['assembly']['metadata']['layout_height']:.1f} mm"
                            }
                            
                            # 3D предпросмотр если доступен
                            try:
                                preview_3d = self.fashion_exporter.preview_3d_assembly(assembly_layout)
                                if 'error' not in preview_3d:
                                    assembly_result['preview_3d'] = preview_3d
                            except Exception as e:
                                logging.warning(f"Failed to generate 3D preview: {e}")
                    
                except Exception as e:
                    logging.error(f"Failed to generate assembly: {e}")
                    assembly_result = {"error": f"Ошибка при создании общей картины: {str(e)}"}
            
            result = {
                'success': True,
                'design_id': design_id,
                'patterns_count': len(patterns),
                'patterns': patterns,
                'description': f'Создан дизайн одежды: {garment_type} в стиле {style}',
                'exported_files': exported_files,
                'cad_result': cad_result
            }
            
            # Добавляем assembly если создан
            if assembly_result:
                result['assembly'] = assembly_result
            
            return result
            
        except Exception as e:
            logging.error(f"Clothing design error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Ошибка при создании дизайна одежды: {str(e)}'
            }
    
    def generate_design_description(self, 
                                   garment_type: str,
                                   style: str,
                                   additional_requirements: str = "") -> Dict[str, Any]:
        """
        Генерация текстового описания конструкции одежды
        
        Args:
            garment_type: Тип одежды
            style: Стиль
            additional_requirements: Дополнительные требования
            
        Returns:
            Словарь с описанием конструкции
        """
        try:
            garment_enum = GarmentType(garment_type.lower())
            style_enum = DesignStyle(style.lower())
            
            # Генерация описания
            description = self.fashion_designer.generate_description(
                garment_type=garment_enum,
                style=style_enum,
                additional_requirements=additional_requirements
            )
            
            return {
                'success': True,
                'description': description,
                'garment_type': garment_type,
                'style': style,
                'additional_requirements': additional_requirements
            }
            
        except Exception as e:
            logging.error(f"Design description error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при генерации описания: {str(e)}'
            }
    
    def build_sleeve_pattern(self, 
                           measurements: Dict[str, float],
                           armhole_length: float) -> Dict[str, Any]:
        """
        Построение базового втачного рукава
        
        Args:
            measurements: Мерки тела
            armhole_length: Длина проймы (спинка + перед)
            
        Returns:
            Словарь с линиями рукава для экспорта
        """
        try:
            # Строим рукав
            sleeve_result = self.pattern_maker.build_shirt_sleeve(measurements, armhole_length)
            
            # Конвертируем в формат для экспорта
            sleeve_pattern = {
                "points": {},
                "lines": {},
                "curves": {}
            }
            
            # Добавляем линии
            for i, line in enumerate(sleeve_result['lines']):
                line_name = line['name']
                sleeve_pattern['lines'][line_name] = {
                    'start': line['start'],
                    'end': line['end']
                }
            
            return {
                'success': True,
                'sleeve_pattern': sleeve_pattern,
                'sleeve_info': sleeve_result.get('info', {}),
                'lines': sleeve_result['lines'],
                'description': f'Построен базовый втачной рукав с длиной проймы {armhole_length} см'
            }
            
        except Exception as e:
            logging.error(f"Sleeve pattern building error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при построении рукава: {str(e)}'
            }
    
    def grade_pattern(self, 
                     base_pattern: Dict[str, Any], 
                     size_steps: Dict[str, int]) -> Dict[str, Any]:
        """
        Градация базового лекала на разные размеры
        
        Args:
            base_pattern: Базовое лекало (размер M)
            size_steps: Шаги градации для каждого размера
            
        Returns:
            Словарь с отградированными лекалами
        """
        try:
            # Выполняем градацию
            graded_patterns = self.pattern_grader.grade_pattern(base_pattern, size_steps)
            
            return {
                'success': True,
                'graded_patterns': graded_patterns,
                'base_pattern': base_pattern,
                'size_steps': size_steps,
                'sizes_count': len(graded_patterns),
                'description': f'Выполнена градация на {len(graded_patterns)} размеров'
            }
            
        except Exception as e:
            logging.error(f"Pattern grading error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при градации лекала: {str(e)}'
            }
    
    def export_graded_patterns_svg(self, 
                                  graded_patterns: Dict[str, Any], 
                                  output_file: str = "graded_patterns.svg") -> Dict[str, Any]:
        """
        Экспорт всех отградированных размеров в один SVG файл
        
        Args:
            graded_patterns: Отградированные паттерны
            output_file: Имя выходного файла
            
        Returns:
            Результат экспорта
        """
        try:
            # Экспортируем в SVG
            success = self.pattern_grader.export_graded_patterns_svg(graded_patterns, output_file)
            
            if success:
                return {
                    'success': True,
                    'output_file': output_file,
                    'sizes_count': len(graded_patterns),
                    'description': f'Экспортировано {len(graded_patterns)} размеров в {output_file}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Не удалось экспортировать SVG файл'
                }
                
        except Exception as e:
            logging.error(f"Graded patterns export error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при экспорте градации: {str(e)}'
            }
    
    def export_to_seamly(self, 
                          pattern_data: Dict[str, Any], 
                          measurements: Dict[str, float],
                          output_file: str = "pattern.val") -> Dict[str, Any]:
        """
        Экспорт параметрических лекал в формат Seamly (.val)
        
        Args:
            pattern_data: Данные паттерна (линии, точки)
            measurements: Мерки тела
            output_file: Имя выходного файла
            
        Returns:
            Результат экспорта
        """
        try:
            # Экспортируем в Seamly формат
            success = self.seamly_exporter.export_pattern_to_seamly(pattern_data, measurements, output_file)
            
            if success:
                return {
                    'success': True,
                    'output_file': output_file,
                    'measurements': measurements,
                    'description': f'Экспортировано параметрическое лекало в {output_file}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Не удалось экспортировать .val файл'
                }
                
        except Exception as e:
            logging.error(f"Seamly export error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при экспорте в Seamly: {str(e)}'
            }
    
    def check_armhole_vs_sleeve(self, armhole_length: float, sleeve_cap_length: float) -> Dict[str, Any]:
        """
        Проверка соотношения проймы и оката рукава
        
        Args:
            armhole_length: Длина проймы
            sleeve_cap_length: Длина оката рукава
            
        Returns:
            Результат проверки с предупреждениями и рекомендациями
        """
        try:
            result = self.fit_analyzer.check_armhole_vs_sleeve(armhole_length, sleeve_cap_length)
            return {
                'success': True,
                'analysis': result,
                'description': f'Проверено соотношение проймы и оката: {result.get("status", "unknown")}'
            }
            
        except Exception as e:
            logging.error(f"Armhole vs sleeve check error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при проверке проймы и оката: {str(e)}'
            }
    
    def check_balance(self, front_length: float, back_length: float) -> Dict[str, Any]:
        """
        Проверка баланса переда и спинки
        
        Args:
            front_length: Длина переда
            back_length: Длина спинки
            
        Returns:
            Результат проверки баланса
        """
        try:
            result = self.fit_analyzer.check_balance(front_length, back_length)
            return {
                'success': True,
                'analysis': result,
                'description': f'Проверен баланс переда и спинки: {result.get("status", "unknown")}'
            }
            
        except Exception as e:
            logging.error(f"Balance check error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при проверке баланса: {str(e)}'
            }
    
    def check_shoulder_slope(self, height: float, chest: float) -> Dict[str, Any]:
        """
        Проверка наклона плеча
        
        Args:
            height: Рост
            chest: Обхват груди
            
        Returns:
            Результат проверки наклона плеча
        """
        try:
            result = self.fit_analyzer.check_shoulder_slope(height, chest)
            return {
                'success': True,
                'analysis': result,
                'description': f'Проверен наклон плеча: {result.get("status", "unknown")}'
            }
            
        except Exception as e:
            logging.error(f"Shoulder slope check error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при проверке наклона плеча: {str(e)}'
            }
    
    def validate_pattern(self, pieces: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация полного паттерна
        
        Args:
            pieces: Словарь с деталями паттерна
            
        Returns:
            Результат валидации
        """
        try:
            result = self.fit_analyzer.validate_pattern(pieces)
            return {
                'success': True,
                'validation': result,
                'description': f'Выполнена валидация паттерна: {result.get("status", "unknown")}'
            }
            
        except Exception as e:
            logging.error(f"Pattern validation error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при валидации паттерна: {str(e)}'
            }
    
    def add_seam_allowances(self, piece: Dict[str, Any], 
                           allowances: Dict[str, float] = None,
                           garment_type: str = 'shirt') -> Dict[str, Any]:
        """
        Добавление припусков на швы к детали
        
        Args:
            piece: Деталь лекала
            allowances: Припуски по типу шва (опционально)
            garment_type: Тип одежды для стандартных припусков
            
        Returns:
            Деталь с припусками
        """
        try:
            # Если припуски не заданы, используем стандартные
            if allowances is None:
                allowances = self.seam_allowance.create_standard_allowances(garment_type)
            
            # Добавляем припуски
            piece_with_allowances = self.seam_allowance.add_seam_allowances(piece, allowances)
            
            return {
                'success': True,
                'piece': piece_with_allowances,
                'allowances': allowances,
                'original_piece': piece,
                'description': f'Добавлены припуски к детали {piece.get("name", "Unknown")}'
            }
            
        except Exception as e:
            logging.error(f"Seam allowance error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при добавлении припусков: {str(e)}'
            }
    
    def create_standard_allowances(self, garment_type: str = 'shirt') -> Dict[str, Any]:
        """
        Создание стандартных припусков для типа одежды
        
        Args:
            garment_type: Тип одежды
            
        Returns:
            Стандартные припуски
        """
        try:
            allowances = self.seam_allowance.create_standard_allowances(garment_type)
            
            return {
                'success': True,
                'allowances': allowances,
                'garment_type': garment_type,
                'description': f'Созданы стандартные припуски для {garment_type}'
            }
            
        except Exception as e:
            logging.error(f"Standard allowances error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при создании припусков: {str(e)}'
            }
    
    def process_corners(self, piece: Dict[str, Any], 
                      corner_type: str = 'miter') -> Dict[str, Any]:
        """
        Обработка углов в детали
        
        Args:
            piece: Деталь с припусками
            corner_type: Тип обработки углов
            
        Returns:
            Деталь с обработанными углами
        """
        try:
            processed_piece = self.seam_allowance.process_corners(piece, corner_type)
            
            return {
                'success': True,
                'piece': processed_piece,
                'corner_type': corner_type,
                'description': f'Обработаны углы типа {corner_type}'
            }
            
        except Exception as e:
            logging.error(f"Corner processing error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при обработке углов: {str(e)}'
            }
    
    def export_piece_with_allowances_svg(self, piece: Dict[str, Any], 
                                       output_file: str) -> Dict[str, Any]:
        """
        Экспорт детали с припусками в SVG
        
        Args:
            piece: Деталь с припусками
            output_file: Имя выходного файла
            
        Returns:
            Результат экспорта
        """
        try:
            # Подготавливаем данные для экспорта
            export_data = {
                "geometry": {
                    "points": piece.get('points', {}),
                    "lines": piece.get('lines', {}),
                    "curves": {}
                },
                "metadata": {
                    "pattern_type": "piece_with_allowances",
                    "piece_name": piece.get('name', 'Unknown'),
                    "has_allowances": True,
                    "allowances": piece.get('allowances', {}),
                    "corner_processing": piece.get('corner_processing', {})
                }
            }
            
            # Экспортируем в SVG
            options = ExportOptions(
                format=ExportFormat.SVG,
                include_measurements=True,
                include_grain_lines=True,
                include_notches=True
            )
            
            success = self.fashion_exporter.export_pattern(export_data, output_file, options)
            
            if success:
                return {
                    'success': True,
                    'output_file': output_file,
                    'piece_name': piece.get('name', 'Unknown'),
                    'description': f'Экспортирована деталь с припусками в {output_file}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Не удалось экспортировать SVG файл'
                }
                
        except Exception as e:
            logging.error(f"SVG export with allowances error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при экспорте с припусками: {str(e)}'
            }
    
    def export_piece_with_allowances_seamly(self, piece: Dict[str, Any], 
                                           measurements: Dict[str, float],
                                           output_file: str) -> Dict[str, Any]:
        """
        Экспорт детали с припусками в Seamly
        
        Args:
            piece: Деталь с припусками
            measurements: Мерки тела
            output_file: Имя выходного файла
            
        Returns:
            Результат экспорта
        """
        try:
            # Подготавливаем данные для экспорта
            pattern_data = {
                "lines": piece.get('lines', {}),
                "points": piece.get('points', {})
            }
            
            # Экспортируем в Seamly
            success = self.seamly_exporter.export_pattern_to_seamly(
                pattern_data, measurements, output_file
            )
            
            if success:
                return {
                    'success': True,
                    'output_file': output_file,
                    'piece_name': piece.get('name', 'Unknown'),
                    'description': f'Экспортирована деталь с припусками в {output_file}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Не удалось экспортировать .val файл'
                }
                
        except Exception as e:
            logging.error(f"Seamly export with allowances error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при экспорте в Seamly: {str(e)}'
            }
    
    def validate_piece_indices(self, piece: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация индексов точек и линий в детали
        
        Args:
            piece: Деталь для валидации
            
        Returns:
            Результат валидации
        """
        try:
            validation_result = self.seam_allowance.validate_piece_indices(piece)
            
            return {
                'success': True,
                'validation': validation_result,
                'piece_name': piece.get('name', 'Unknown'),
                'description': f'Выполнена валидация детали {piece.get("name", "Unknown")}'
            }
            
        except Exception as e:
            logging.error(f"Piece indices validation error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при валидации индексов: {str(e)}'
            }
    
    def apply_style(self, pattern: Dict[str, Any], style_name: str, 
                    garment_type: str = 'shirt') -> Dict[str, Any]:
        """
        Применение стиля к лекалам
        
        Args:
            pattern: Исходные лекала
            style_name: Название стиля (slim, classic, oversize)
            garment_type: Тип одежды
            
        Returns:
            Стилизованные лекала
        """
        try:
            # Применяем стиль
            styled_pattern = self.style_engine.apply_style(pattern, style_name, garment_type)
            
            # Анализируем посадку с помощью FitAnalyzer
            pieces = styled_pattern.get('pieces', {})
            if pieces:
                fit_analysis = self.fit_analyzer.validate_pattern(pieces)
                styled_pattern['fit_analysis'] = fit_analysis
            
            return {
                'success': True,
                'pattern': styled_pattern,
                'style_applied': style_name,
                'garment_type': garment_type,
                'description': f'Применен стиль {style_name} к лекалам'
            }
            
        except Exception as e:
            logging.error(f"Style application error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при применении стиля: {str(e)}'
            }
    
    def get_style_preview(self, pattern: Dict[str, Any], style_name: str,
                         garment_type: str = 'shirt') -> Dict[str, Any]:
        """
        Предпросмотр изменений стиля
        
        Args:
            pattern: Лекала
            style_name: Название стиля
            garment_type: Тип одежды
            
        Returns:
            Предпросмотр изменений
        """
        try:
            preview = self.style_engine.preview_style_changes(pattern, style_name, garment_type)
            
            return {
                'success': True,
                'preview': preview,
                'description': f'Предпросмотр стиля {style_name}'
            }
            
        except Exception as e:
            logging.error(f"Style preview error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при предпросмотре стиля: {str(e)}'
            }
    
    def get_available_styles(self) -> Dict[str, Any]:
        """
        Получение доступных стилей
        
        Returns:
            Словарь доступных стилей
        """
        try:
            styles = self.style_engine.get_available_styles()
            
            return {
                'success': True,
                'styles': styles,
                'count': len(styles),
                'description': f'Доступно {len(styles)} стилей'
            }
            
        except Exception as e:
            logging.error(f"Get styles error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при получении стилей: {str(e)}'
            }
    
    def combine_styles(self, base_style: str, modifier_style: str, 
                      modifier_strength: float = 0.5) -> Dict[str, Any]:
        """
        Комбинирование стилей
        
        Args:
            base_style: Базовый стиль
            modifier_style: Модифицирующий стиль
            modifier_strength: Сила модификатора (0-1)
            
        Returns:
            Комбинированный стиль
        """
        try:
            combined = self.style_engine.combine_styles(
                base_style, modifier_style, modifier_strength
            )
            
            return {
                'success': True,
                'combined_style': combined,
                'description': f'Создан комбинированный стиль'
            }
            
        except Exception as e:
            logging.error(f"Style combination error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при комбинировании стилей: {str(e)}'
            }
    
    def _get_pattern_types_for_garment(self, garment_type: GarmentType) -> List:
        """Получить необходимые типы лекал для типа одежды"""
        from ..fashion.pattern_maker import PatternType
        
        pattern_map = {
            GarmentType.SHIRT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK],  # Только перед + спинка
            GarmentType.PANTS: [PatternType.PANTS_FRONT, PatternType.PANTS_BACK, PatternType.POCKET],
            GarmentType.SKIRT: [PatternType.SKIRT_FRONT, PatternType.SKIRT_BACK, PatternType.POCKET],
            GarmentType.JACKET: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF, PatternType.POCKET],
            GarmentType.COAT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF, PatternType.POCKET],
            GarmentType.BLOUSE: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF, PatternType.POCKET]
        }
        
        return pattern_map.get(garment_type, [PatternType.BODICE_FRONT])
    
    def text_to_pattern_modifications(self, 
                                   user_prompt: str,
                                   base_measurements: Dict[str, float],
                                   clothing_type: str,
                                   model_name: str = "llama3.2") -> Dict[str, Any]:
        """
        Преобразование текстового запроса в структурированные модификации лекала
        
        Args:
            user_prompt: Текстовый запрос пользователя
            base_measurements: Базовые мерки
            clothing_type: Тип одежды
            model_name: Название модели Ollama
            
        Returns:
            Словарь с модификациями лекала
        """
        try:
            modifications = self.text_design_interface.interpret_design_request(
                user_prompt, base_measurements, clothing_type
            )
            
            return {
                'success': True,
                'modifications': modifications,
                'user_prompt': user_prompt,
                'clothing_type': clothing_type,
                'model_used': model_name,
                'description': f'Проанализирован запрос: "{user_prompt}"'
            }
            
        except Exception as e:
            logging.error(f"Text to pattern modifications error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при анализе текстового запроса: {str(e)}',
                'user_prompt': user_prompt,
                'clothing_type': clothing_type
            }
    
    def apply_text_modifications(self, 
                               base_pattern: Dict[str, Any],
                               modifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применение текстовых модификаций к базовому лекалу
        
        Args:
            base_pattern: Базовое лекало
            modifications: Модификации для применения
            
        Returns:
            Модифицированное лекало
        """
        try:
            modified_pattern = self.text_design_interface.apply_text_modifications(
                base_pattern, modifications
            )
            
            return {
                'success': True,
                'modified_pattern': modified_pattern,
                'applied_modifications': modifications,
                'description': 'Модификации успешно применены к лекалу'
            }
            
        except Exception as e:
            logging.error(f"Apply text modifications error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при применении модификаций: {str(e)}',
                'base_pattern': base_pattern,
                'modifications': modifications
            }
    
    def design_from_text(self, 
                        user_prompt: str,
                        base_measurements: Dict[str, float],
                        clothing_type: str,
                        output_formats: List[str] = None,
                        cad: str = None,
                        model_name: str = "llama3.2",
                        use_dataset_reference: bool = False) -> Dict[str, Any]:
        """
        Полный цикл дизайна одежды из текстового запроса
        
        Args:
            user_prompt: Текстовый запрос пользователя
            base_measurements: Базовые мерки
            clothing_type: Тип одежды (dress, shirt, pants, skirt, jacket)
            output_formats: Список форматов для экспорта
            cad: CAD система для интеграции
            model_name: Название модели Ollama
            use_dataset_reference: Использовать примеры из датасета как референсы
            
        Returns:
            Результат дизайна с модифицированными лекалами
        """
        try:
            logging.info(f"Starting design from text: '{user_prompt}' for {clothing_type}")
            
            # Если запрошены референсы из датасета, получаем их сначала
            reference_patterns = []
            if use_dataset_reference and self.dataset_integration:
                try:
                    reference_patterns = self.dataset_integration.get_reference_examples(
                        clothing_type=clothing_type, 
                        num=3
                    )
                    logging.info(f"Loaded {len(reference_patterns)} reference patterns for {clothing_type}")
                except Exception as e:
                    logging.warning(f"Failed to load reference patterns: {e}")
            
            # Шаг 1: Анализ текстового запроса
            logging.info("Step 1: Analyzing text request...")
            text_result = self.text_to_pattern_modifications(
                user_prompt, base_measurements, clothing_type, model_name
            )
            
            if not text_result['success']:
                logging.error(f"Text analysis failed: {text_result.get('error', 'Unknown error')}")
                return text_result
            
            modifications = text_result['modifications']
            logging.info(f"Text analysis completed. Modifications: {list(modifications.keys())}")
            
            # Шаг 2: Создание базового лекала
            logging.info("Step 2: Creating base pattern...")
            
            # Добавляем референсы в мерки (если доступны)
            enhanced_measurements = base_measurements.copy()
            if reference_patterns:
                enhanced_measurements["reference_patterns"] = reference_patterns
            
            # Маппинг clothing_type в garment_type для design_clothing
            clothing_mapping = {
                "dress": "dress",
                "shirt": "shirt", 
                "pants": "pants",
                "skirt": "skirt",
                "jacket": "jacket",
                "coat": "coat",
                "blouse": "blouse",
                "tshirt": "tshirt"
            }
            
            mapped_garment_type = clothing_mapping.get(clothing_type.lower())
            if not mapped_garment_type:
                error_msg = f"Unsupported clothing type: {clothing_type}. Supported types: {list(clothing_mapping.keys())}"
                logging.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'user_prompt': user_prompt,
                    'clothing_type': clothing_type
                }
            
            logging.info(f"Mapped {clothing_type} -> {mapped_garment_type}")
            
            # Добавляем garment_type в мерки для правильного выбора метода конструирования
            enhanced_measurements = base_measurements.copy()
            enhanced_measurements["garment_type"] = mapped_garment_type
            
            # Вызываем design_clothing с правильными параметрами
            base_pattern_result = self.design_clothing(
                garment_type=mapped_garment_type,  # Правильный параметр
                style="casual",  # Используем доступный стиль
                measurements=enhanced_measurements,  # Передаем мерки с garment_type и референсами
                output_formats=[],  # Пока без экспорта
                cad=None,
                use_dataset_reference=use_dataset_reference  # Передаем флаг использования датасета
            )
            
            if not base_pattern_result['success']:
                logging.error(f"Base pattern creation failed: {base_pattern_result.get('error', 'Unknown error')}")
                return base_pattern_result
            
            logging.info("Base pattern created successfully")
            
            # Шаг 3: Применение модификаций
            logging.info("Step 3: Applying text modifications...")
            
            # Берем первое лекало из списка для модификации
            patterns = base_pattern_result.get('patterns', [])
            if not patterns:
                error_msg = "No patterns created in base pattern result"
                logging.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'base_pattern_result': base_pattern_result
                }
            
            base_pattern = patterns[0]  # Используем первое лекало
            
            apply_result = self.apply_text_modifications(
                base_pattern=base_pattern,
                modifications=modifications
            )
            
            if not apply_result['success']:
                logging.error(f"Modifications application failed: {apply_result.get('error', 'Unknown error')}")
                return apply_result
            
            modified_pattern = apply_result['modified_pattern']
            
            # Шаг 4: Экспорт файлов
            logging.info("Step 4: Exporting patterns...")
            export_results = {}
            if output_formats:
                try:
                    # Обновляем первое лекало в списке модифицированной версией
                    patterns[0] = modified_pattern
                    updated_base_result = base_pattern_result.copy()
                    updated_base_result['patterns'] = patterns
                    
                    # Добавляем параметры экспорта по умолчанию
                    export_format = ExportFormat(output_formats[0] if output_formats else 'json')
                    export_options = ExportOptions(
                        format=export_format,
                        include_seam_allowances=False,
                        include_measurements=True,
                        include_notches=True
                    )
                    
                    # Создаем директорию для экспорта
                    export_dir = Path.cwd() / "fashion_exports" / f"skirt_json_export_{len(os.listdir(Path.cwd() / 'fashion_exports'))}"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Экспортируем каждое лекало
                    for i, pattern in enumerate(patterns):
                        pattern_file = export_dir / f"pattern_{i+1}.{output_formats[0] if output_formats else 'json'}"
                        
                        if output_formats[0] == 'json':
                            # Для JSON используем специальный метод для анализа AI
                            analysis_data = self.fashion_exporter.export_pattern_to_dict(pattern, export_options)
                            with open(pattern_file, 'w', encoding='utf-8') as f:
                                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
                            export_results[f"pattern_{i+1}"] = {
                                'filename': str(pattern_file),
                                'format': 'json',
                                'success': True
                            }
                        else:
                            success = self.fashion_exporter.export_pattern(pattern, pattern_file, export_options)
                            export_results[f"pattern_{i+1}"] = {
                                'filename': str(pattern_file),
                                'format': output_formats[0],
                                'success': success
                            }
                    
                    logging.info(f"Export completed: {list(export_results.keys())}")
                except Exception as e:
                    logging.warning(f"Export error: {str(e)}")
            else:
                logging.info("No export formats specified - skipping export")
            
            # Шаг 5: CAD интеграция (если требуется)
            logging.info("Step 5: CAD integration...")
            cad_results = {}
            if cad:
                try:
                    cad_result = self.cad_bridge.export_to_cad(
                        modified_pattern, cad
                    )
                    if cad_result.get('success'):
                        cad_results = cad_result.get('cad_data', {})
                        logging.info(f"CAD integration completed: {cad}")
                    else:
                        logging.warning(f"CAD integration failed: {cad_result.get('error', 'Unknown error')}")
                except Exception as e:
                    logging.warning(f"CAD integration error: {str(e)}")
            
            logging.info("Design from text completed successfully")
            
            return {
                'success': True,
                'pattern': modified_pattern,
                'text_analysis': text_result,
                'base_pattern': base_pattern_result,
                'modifications': modifications,
                'exports': export_results,
                'cad_data': cad_results,
                'user_prompt': user_prompt,
                'clothing_type': clothing_type,
                'description': f'Создан дизайн {clothing_type} из запроса: "{user_prompt}"'
            }
            
        except Exception as e:
            logging.error(f"Design from text error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при создании дизайна из текста: {str(e)}',
                'user_prompt': user_prompt,
                'clothing_type': clothing_type
            }
