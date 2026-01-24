"""
Реестр инструментов - централизованное хранилище всех доступных инструментов
"""
from typing import Dict, Any, Callable

from .core_tools import CoreTools
from .fashion_tools import FashionTools


class ToolRegistry:
    """Реестр инструментов"""
    
    def __init__(self):
        """Инициализация реестра"""
        self.core_tools = CoreTools()
        self.fashion_tools = FashionTools()
        self._tools = {}
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Регистрация всех инструментов"""
        # Регистрация core инструментов
        self._register_core_tools()
        
        # Регистрация fashion инструментов
        self._register_fashion_tools()
    
    def _register_core_tools(self):
        """Регистрация core инструментов"""
        core_tools = {
            'analyze_website': self.core_tools.analyze_website,
            'create_site_copy': self.core_tools.create_site_copy,
            'generate_original_site': self.core_tools.generate_original_site,
            'get_weather': self.core_tools.get_weather,
            'tavily_search': self.core_tools.tavily_search,
            'gpu_status': self.core_tools.gpu_status,
            'enable_gpu': self.core_tools.enable_gpu,
            'restart_services': self.core_tools.restart_services,
        }
        
        descriptions = {
            'analyze_website': 'Анализ веб-сайта',
            'create_site_copy': 'Создание копии сайта',
            'generate_original_site': 'Генерация оригинального сайта',
            'get_weather': 'Получить погоду в городе',
            'tavily_search': 'Поиск информации через Tavily',
            'gpu_status': 'Проверка статуса GPU',
            'enable_gpu': 'Включение GPU для агента',
            'restart_services': 'Перезапуск сервисов',
        }
        
        for name, func in core_tools.items():
            self._tools[name] = {
                'function': func,
                'description': descriptions.get(name, ''),
                'category': 'core'
            }
    
    def _register_fashion_tools(self):
        """Регистрация fashion инструментов"""
        fashion_tools = {
            'design_clothing': self.fashion_tools.design_clothing,
            'generate_design_description': self.fashion_tools.generate_design_description,
            'build_sleeve_pattern': self.fashion_tools.build_sleeve_pattern,
            'grade_pattern': self.fashion_tools.grade_pattern,
            'export_graded_patterns_svg': self.fashion_tools.export_graded_patterns_svg,
            'export_to_seamly': self.fashion_tools.export_to_seamly,
            'check_armhole_vs_sleeve': self.fashion_tools.check_armhole_vs_sleeve,
            'check_balance': self.fashion_tools.check_balance,
            'check_shoulder_slope': self.fashion_tools.check_shoulder_slope,
            'validate_pattern': self.fashion_tools.validate_pattern,
            'add_seam_allowances': self.fashion_tools.add_seam_allowances,
            'create_standard_allowances': self.fashion_tools.create_standard_allowances,
            'process_corners': self.fashion_tools.process_corners,
            'export_piece_with_allowances_svg': self.fashion_tools.export_piece_with_allowances_svg,
            'export_piece_with_allowances_seamly': self.fashion_tools.export_piece_with_allowances_seamly,
            'validate_piece_indices': self.fashion_tools.validate_piece_indices,
            'apply_style': self.fashion_tools.apply_style,
            'get_style_preview': self.fashion_tools.get_style_preview,
            'get_available_styles': self.fashion_tools.get_available_styles,
            'combine_styles': self.fashion_tools.combine_styles,
            'text_to_pattern_modifications': self.fashion_tools.text_to_pattern_modifications,
            'apply_text_modifications': self.fashion_tools.apply_text_modifications,
            'design_from_text': self.fashion_tools.design_from_text,
        }
        
        descriptions = {
            'design_clothing': 'Создание дизайна одежды с лекалами и экспортом',
            'generate_design_description': 'Генерация текстового описания конструкции одежды',
            'build_sleeve_pattern': 'Построение базового втачного рукава',
            'grade_pattern': 'Градация лекала на разные размеры',
            'export_graded_patterns_svg': 'Экспорт всех размеров в один SVG файл',
            'export_to_seamly': 'Экспорт параметрических лекал в формат Seamly (.val)',
            'check_armhole_vs_sleeve': 'Проверка соотношения проймы и оката рукава',
            'check_balance': 'Проверка баланса переда и спинки',
            'check_shoulder_slope': 'Проверка наклона плеча',
            'validate_pattern': 'Валидация полного паттерна',
            'add_seam_allowances': 'Добавление припусков на швы к детали',
            'create_standard_allowances': 'Создание стандартных припусков для типа одежды',
            'process_corners': 'Обработка углов в детали',
            'export_piece_with_allowances_svg': 'Экспорт детали с припусками в SVG',
            'export_piece_with_allowances_seamly': 'Экспорт детали с припусками в Seamly',
            'validate_piece_indices': 'Валидация индексов точек и линий в детали',
            'apply_style': 'Применение стиля к лекалам (slim, classic, oversize)',
            'get_style_preview': 'Предпросмотр изменений стиля',
            'get_available_styles': 'Получение доступных стилей',
            'combine_styles': 'Комбинирование стилей',
            'text_to_pattern_modifications': 'Преобразование текстового запроса в структурированные модификации лекала',
            'apply_text_modifications': 'Применение текстовых модификаций к базовому лекалу',
            'design_from_text': 'Полный цикл дизайна одежды из текстового запроса',
        }
        
        for name, func in fashion_tools.items():
            self._tools[name] = {
                'function': func,
                'description': descriptions.get(name, ''),
                'category': 'fashion'
            }
    
    def get_tool(self, name: str) -> Callable:
        """Получить инструмент по имени"""
        if name in self._tools:
            return self._tools[name]['function']
        return None
    
    def get_tools_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Получить инструменты по категории"""
        return {
            name: info for name, info in self._tools.items()
            if info['category'] == category
        }
    
    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """Получить все инструменты"""
        return self._tools.copy()
    
    def list_tools(self) -> Dict[str, str]:
        """Получить список всех инструментов с описаниями"""
        return {
            name: info['description'] 
            for name, info in self._tools.items()
        }


# Создаем глобальный реестр
_registry = ToolRegistry()

# Экспортируем инструменты для обратной совместимости
TOOLS = {
    name: info['function'] 
    for name, info in _registry.get_all_tools().items()
}

# Экспортируем функции для получения инструментов
def get_tool(name: str) -> Callable:
    """Получить инструмент по имени"""
    return _registry.get_tool(name)

def get_tools_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """Получить инструменты по категории"""
    return _registry.get_tools_by_category(category)

def get_all_tools() -> Dict[str, Dict[str, Any]]:
    """Получить все инструменты"""
    return _registry.get_all_tools()

def list_tools() -> Dict[str, str]:
    """Получить список всех инструментов с описаниями"""
    return _registry.list_tools()
