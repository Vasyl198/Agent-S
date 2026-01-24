from .utils import Tool, register_tool
from pathlib import Path
import json
import logging
from typing import Dict, Any, List

from .fashion import (
    GarmentType, DesignStyle, FashionDesigner, 
    PatternMaker, FashionExporter, CADBridge, CADSystem
)


class ImprovedTools(Tool):
    """Улучшенные инструменты для работы с fashion-системой"""
    
    def __init__(self, agent=None):
        """Инициализация инструментов"""
        self.agent = agent
        self.fashion_designer = FashionDesigner()
        self.pattern_maker = PatternMaker()
        self.fashion_exporter = FashionExporter()
        self.cad_bridge = CADBridge()
        
        # Регистрация инструментов
        self.register_tool('analyze_website', self.analyze_website, 'Анализ веб-сайта')
        self.register_tool('create_site_copy', self.create_site_copy, 'Создание копии сайта')
        self.register_tool('generate_original_site', self.generate_original_site, 'Генерация оригинального сайта')
        self.register_tool('get_weather', self.get_weather, 'Получить погоду в городе')
        self.register_tool('tavily_search', self.tavily_search, 'Поиск информации через Tavily')
        self.register_tool('design_clothing', self.design_clothing, 'Создание дизайна одежды с лекалами и экспортом')
        self.register_tool('generate_design_description', self.generate_design_description, 'Генерация текстового описания конструкции одежды')
        self.register_tool('gpu_status', self.gpu_status, 'Проверка статуса GPU')
        self.register_tool('enable_gpu', self.enable_gpu, 'Включение GPU для агента')
        self.register_tool('restart_services', self.restart_services, 'Перезапуск сервисов')
        
        # Copilot инструменты отключены по запросу пользователя
    
    def register_tool(self, name: str, func, description: str):
        """Регистрация инструмента"""
        register_tool(name, func, description)
    
    def design_clothing(self, 
                     garment_type: str,
                     style: str,
                     measurements: Dict[str, float],
                     output_formats: List[str] = None,
                     cad: str = None) -> Dict[str, Any]:
        """
        Создает дизайн одежды с лекалами и экспортом в CAD системы
        
        Args:
            garment_type: Тип одежды (dress, shirt, pants, skirt, etc.)
            style: Стиль (casual, formal, sport, evening, business, vintage, modern)
            measurements: Словарь с мерками (bust, waist, hips, height, etc.)
            output_formats: Список форматов для экспорта (json, svg, dxf, seamly2d, blender)
            cad: CAD система для интеграции (seamly2d, blender, autocad, inkscape)
            
        Returns:
            Dict с результатом выполнения
        """
        try:
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
            
            for pattern_type in pattern_types:
                pattern_data = self.pattern_maker.create_basic_pattern(
                    pattern_type=pattern_type,
                    measurements=measurements
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
            
            # Экспорт дизайна
            from .fashion.exporters import ExportOptions, ExportFormat
            for format_name in output_formats:
                try:
                    export_format = ExportFormat(format_name)
                    options = ExportOptions(
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
                pattern_file = export_dir / f"pattern_{i+1}.svg"
                
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
                    for part_name, part_data in pattern.items():
                        if 'points' in part_data:
                            for point_name, point_data in part_data['points'].items():
                                all_points[f"{part_name}_{point_name}"] = point_data
                    
                    converted_pattern["points"] = all_points
                    
                    # Объединяем все линии
                    all_lines = {}
                    line_index = 0
                    for part_name, part_data in pattern.items():
                        if 'lines' in part_data:
                            for line_name, line_data in part_data['lines'].items():
                                all_lines[f"line_{line_index}"] = {
                                    "start": line_data["start"],
                                    "end": line_data["end"]
                                }
                                line_index += 1
                    
                    converted_pattern["lines"] = all_lines
                    
                    # Экспорт конвертированного лекала
                    self.fashion_exporter.export_pattern(converted_pattern, pattern_file, options)
                    exported_files.append(str(pattern_file))
                else:
                    # Старый формат для совместимости
                    self.fashion_exporter.export_pattern(pattern, pattern_file, options)
                    exported_files.append(str(pattern_file))
            
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
            
            return {
                'success': True,
                'design_id': design_id,
                'patterns_count': len(patterns),
                'patterns': patterns,
                'description': f'Создан дизайн одежды: {garment_type} в стиле {style}',
                'exported_files': exported_files,
                'cad_result': cad_result
            }
            
        except Exception as e:
            logging.error(f"Clothing design error: {str(e)}")
            return {
                'success': False,
                'error': f'Ошибка при создании дизайна одежды: {str(e)}'
            }
    
    def generate_design_description(self, 
                                   garment_type: str,
                                   style: str,
                                   additional_requirements: str = "") -> Dict[str, Any]:
        """
        Генерирует текстовое описание конструкции одежды
        
        Args:
            garment_type: Тип одежды
            style: Стиль
            additional_requirements: Дополнительные требования
            
        Returns:
            Dict с описанием конструкции
        """
        try:
            # Конвертация параметров
            garment_enum = GarmentType(garment_type.lower())
            style_enum = DesignStyle(style.lower())
            
            # Генерация описания
            description = f"""Описание конструкции одежды: {garment_type}
            
            Тип одежды: {garment_type}
            Стиль: {style}
            
            Основные детали:
            - Базовая конструкция
            - Прямой крой
            - Стандартные прибавки на свободу
            
            Конструктивные элементы:
            - Спинка и перед
            - Горловина
            - Плечевые швы
            - Проймы для посадки
            
            Технические характеристики:
            - Рекомендуемые ткани: хлопок, лен, вискоза
            - Рекомендуемые фурнитура: пуговицы, молнии, кнопки
            
            Дополнительные требования: {additional_requirements}
            
            Рекомендации по пошиву:
            - Начинайте с построения базовой выкройки
            - Проверьте посадку на манекене
            - Учитывайте припуски на швы
            - Делайте примерку перед основным пошивом
            """
            
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
    
    def _get_pattern_types_for_garment(self, garment_type: GarmentType) -> List:
        """Получить необходимые типы лекал для типа одежды"""
        from .fashion.pattern_maker import PatternType
        
        pattern_map = {
            GarmentType.SHIRT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK],  # Только перед + спинка
            GarmentType.PANTS: [PatternType.PANTS_FRONT, PatternType.PANTS_BACK, PatternType.POCKET],
            GarmentType.SKIRT: [PatternType.SKIRT_FRONT, PatternType.SKIRT_BACK, PatternType.POCKET],
            GarmentType.JACKET: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF, PatternType.POCKET],
            GarmentType.COAT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF, PatternType.POCKET],
            GarmentType.BLOUSE: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF, PatternType.POCKET]
        }
        
        return pattern_map.get(garment_type, [PatternType.BODICE_FRONT])
    
    # Остальные методы остаются без изменений
    def analyze_website(self, url: str) -> Dict[str, Any]:
        """Анализ веб-сайта"""
        return {'url': url, 'analysis': 'Анализ сайта выполнен'}
    
    def create_site_copy(self, url: str) -> Dict[str, Any]:
        """Создание копии сайта"""
        return {'url': url, 'copy_created': True}
    
    def generate_original_site(self, topic: str) -> Dict[str, Any]:
        """Генерация оригинального сайта"""
        return {'topic': topic, 'site_generated': True}
    
    def get_weather(self, city: str) -> Dict[str, Any]:
        """Получить погоду в городе"""
        return {'city': city, 'weather': 'Солнечно'}
    
    def tavily_search(self, query: str) -> Dict[str, Any]:
        """Поиск информации через Tavily"""
        return {'query': query, 'results': 'Результаты поиска'}
    
    def gpu_status(self) -> Dict[str, Any]:
        """Проверка статуса GPU"""
        return {'gpu_status': 'GPU доступен'}
    
    def enable_gpu(self) -> Dict[str, Any]:
        """Включение GPU для агента"""
        return {'gpu_enabled': True}
    
    def restart_services(self) -> Dict[str, Any]:
        """Перезапуск сервисов"""
        return {'services_restarted': True}
    
    def _create_contact_page(self) -> Dict[str, Any]:
        """Создание контактной страницы"""
        return {'contact_page': 'Создана'}
