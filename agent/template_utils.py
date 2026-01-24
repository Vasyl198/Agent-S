"""
Утилиты для работы с шаблонами сайтов
"""

import os
import jinja2
from typing import Dict, Any, List, Optional
from datetime import datetime

from .utils import logger


class TemplateRenderer:
    """Рендерер шаблонов с использованием Jinja2"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        self.env = self._setup_jinja_env()
    
    def _setup_jinja_env(self) -> jinja2.Environment:
        """Настраивает окружение Jinja2"""
        try:
            # Проверяем существование директории шаблонов
            if not os.path.exists(self.templates_dir):
                os.makedirs(self.templates_dir, exist_ok=True)
                logger.warning(f"Created templates directory: {self.templates_dir}")
            
            # Настраиваем окружение
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(self.templates_dir),
                autoescape=jinja2.select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
            
            # Добавляем кастомные фильтры
            env.filters['datetime'] = self._datetime_filter
            env.filters['format_currency'] = self._format_currency_filter
            env.filters['truncate_words'] = self._truncate_words_filter
            
            return env
            
        except Exception as e:
            logger.error(f"Failed to setup Jinja2 environment: {e}")
            raise
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Рендерит шаблон с контекстом"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except jinja2.TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            return self._fallback_template(template_name, context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return self._fallback_template(template_name, context)
    
    def _fallback_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Запасной шаблон на случай ошибки"""
        return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{context.get('site_name', 'Сайт')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="error">
            <h2>Ошибка загрузки шаблона</h2>
            <p>Не удалось загрузить шаблон: {template_name}</p>
            <p>Используется базовый шаблон. Пожалуйста, проверьте наличие файла шаблона.</p>
        </div>
        <div>
            <h1>{context.get('site_name', 'Сайт')}</h1>
            <p>{context.get('site_description', 'Описание сайта')}</p>
            <div>{context.get('content', '')}</div>
        </div>
    </div>
</body>
</html>
        """
    
    def render_site_copy(self, context: Dict[str, Any]) -> str:
        """Рендерит шаблон для копии сайта"""
        # Добавляем значения по умолчанию
        default_context = {
            'year': datetime.now().year,
            'css_files': [],
            'js_files': [],
            'pages': [],
            'sections': []
        }
        default_context.update(context)
        
        return self.render_template('site_copy.html', default_context)
    
    def render_site_original(self, context: Dict[str, Any]) -> str:
        """Рендерит шаблон для оригинального сайта"""
        # Добавляем значения по умолчанию
        default_context = {
            'year': datetime.now().year,
            'css_files': [],
            'js_files': [],
            'pages': [],
            'sections': [],
            'features': [],
            'gallery': None,
            'contact': None,
            'cta_button': None
        }
        default_context.update(context)
        
        return self.render_template('site_original.html', default_context)
    
    def get_template_list(self) -> List[str]:
        """Возвращает список доступных шаблонов"""
        try:
            templates = []
            for file in os.listdir(self.templates_dir):
                if file.endswith('.html') or file.endswith('.css'):
                    templates.append(file)
            return sorted(templates)
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []
    
    def template_exists(self, template_name: str) -> bool:
        """Проверяет существование шаблона"""
        try:
            template_path = os.path.join(self.templates_dir, template_name)
            return os.path.exists(template_path)
        except Exception:
            return False
    
    # Кастомные фильтры
    def _datetime_filter(self, value: str, format_str: str = '%Y-%m-%d %H:%M') -> str:
        """Фильтр для форматирования даты"""
        try:
            if isinstance(value, str):
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            else:
                dt = value
            return dt.strftime(format_str)
        except Exception:
            return str(value)
    
    def _format_currency_filter(self, value: float, currency: str = '₽') -> str:
        """Фильтр для форматирования валюты"""
        try:
            return f"{value:,.2f} {currency}"
        except Exception:
            return f"{value} {currency}"
    
    def _truncate_words_filter(self, text: str, length: int = 50) -> str:
        """Фильтр для обрезки текста по словам"""
        try:
            words = text.split()
            if len(words) <= length:
                return text
            return ' '.join(words[:length]) + '...'
        except Exception:
            return text


# Глобальный экземпляр рендерера
_template_renderer = None

def get_template_renderer(templates_dir: str = "templates") -> TemplateRenderer:
    """Возвращает экземпляр рендерера шаблонов"""
    global _template_renderer
    if _template_renderer is None:
        _template_renderer = TemplateRenderer(templates_dir)
    return _template_renderer


def render_site_template(template_type: str, context: Dict[str, Any]) -> str:
    """Удобная функция для рендеринга шаблонов сайтов"""
    renderer = get_template_renderer()
    
    if template_type == 'copy':
        return renderer.render_site_copy(context)
    elif template_type == 'original':
        return renderer.render_site_original(context)
    else:
        return renderer.render_template(template_type, context)
