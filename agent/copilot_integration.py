"""
Copilot интеграция для Universal Agent
"""

from typing import Dict, Any

try:
    from copilot_integration import CopilotIntegration as BaseCopilot
    COPILOT_AVAILABLE = True
except ImportError:
    COPILOT_AVAILABLE = False
    BaseCopilot = None

from .utils import logger


class CopilotIntegration:
    """Интеграция с GitHub Copilot"""
    
    def __init__(self, agent):
        self.agent = agent
        self._copilot = None
    
    def _init_copilot(self):
        """Инициализация Copilot интеграции"""
        if COPILOT_AVAILABLE and not hasattr(self, '_copilot'):
            try:
                self._copilot = BaseCopilot()
                logger.info("Copilot initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Copilot: {e}")
                self._copilot = None
        return self._copilot
    
    def copilot_authenticate(self) -> Dict[str, Any]:
        """Аутентификация в GitHub Copilot"""
        if not COPILOT_AVAILABLE:
            return {
                'success': False,
                'error': 'Copilot не доступен',
                'message': 'Установите copilot_integration'
            }
        
        copilot = self._init_copilot()
        if not copilot:
            return {
                'success': False,
                'error': 'Не удалось инициализировать Copilot',
                'message': 'Проверьте установку и настройки'
            }
        
        try:
            result = copilot.authenticate()
            return {
                'success': True,
                'result': result,
                'message': 'Аутентификация в Copilot выполнена'
            }
        except Exception as e:
            logger.error(f"Copilot authentication error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Ошибка при аутентификации в Copilot'
            }
    
    def copilot_suggest(self, code: str, language: str = "python", context: str = "") -> Dict[str, Any]:
        """Получает предложение от Copilot для улучшения кода"""
        if not COPILOT_AVAILABLE:
            return {
                'success': False,
                'error': 'Copilot не доступен',
                'message': 'Установите copilot_integration'
            }
        
        copilot = self._init_copilot()
        if not copilot:
            return {
                'success': False,
                'error': 'Не удалось инициализировать Copilot',
                'message': 'Проверьте установку и настройки'
            }
        
        try:
            result = copilot.get_suggestion(code, language, context)
            return {
                'success': True,
                'suggestion': result,
                'language': language,
                'message': f'Получено предложение для кода на {language}'
            }
        except Exception as e:
            logger.error(f"Copilot suggestion error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Ошибка при получении предложения от Copilot'
            }
    
    def copilot_explain(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Объясняет код с помощью Copilot"""
        if not COPILOT_AVAILABLE:
            return {
                'success': False,
                'error': 'Copilot не доступен',
                'message': 'Установите copilot_integration'
            }
        
        copilot = self._init_copilot()
        if not copilot:
            return {
                'success': False,
                'error': 'Не удалось инициализировать Copilot',
                'message': 'Проверьте установку и настройки'
            }
        
        try:
            result = copilot.explain_code(code, language)
            return {
                'success': True,
                'explanation': result,
                'language': language,
                'message': f'Получено объяснение кода на {language}'
            }
        except Exception as e:
            logger.error(f"Copilot explanation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Ошибка при объяснении кода с помощью Copilot'
            }
    
    def copilot_generate(self, description: str, language: str = "python", context: str = "") -> Dict[str, Any]:
        """Генерирует код с помощью Copilot"""
        if not COPILOT_AVAILABLE:
            return {
                'success': False,
                'error': 'Copilot не доступен',
                'message': 'Установите copilot_integration'
            }
        
        copilot = self._init_copilot()
        if not copilot:
            return {
                'success': False,
                'error': 'Не удалось инициализировать Copilot',
                'message': 'Проверьте установку и настройки'
            }
        
        try:
            result = copilot.generate_code(description, language, context)
            return {
                'success': True,
                'generated_code': result,
                'language': language,
                'message': f'Сгенерирован код на {language}'
            }
        except Exception as e:
            logger.error(f"Copilot generation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Ошибка при генерации кода с помощью Copilot'
            }
    
    def copilot_review(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Проводит code review с помощью Copilot"""
        if not COPILOT_AVAILABLE:
            return {
                'success': False,
                'error': 'Copilot не доступен',
                'message': 'Установите copilot_integration'
            }
        
        copilot = self._init_copilot()
        if not copilot:
            return {
                'success': False,
                'error': 'Не удалось инициализировать Copilot',
                'message': 'Проверьте установку и настройки'
            }
        
        try:
            result = copilot.review_code(code, language)
            return {
                'success': True,
                'review': result,
                'language': language,
                'message': f'Выполнен code review кода на {language}'
            }
        except Exception as e:
            logger.error(f"Copilot review error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Ошибка при code review с помощью Copilot'
            }
    
    def copilot_status(self) -> Dict[str, Any]:
        """Получает статус Copilot"""
        if not COPILOT_AVAILABLE:
            return {
                'success': False,
                'error': 'Copilot не доступен',
                'message': 'Установите copilot_integration'
            }
        
        copilot = self._init_copilot()
        if not copilot:
            return {
                'success': False,
                'error': 'Не удалось инициализировать Copilot',
                'message': 'Проверьте установку и настройки'
            }
        
        try:
            result = copilot.get_status()
            return {
                'success': True,
                'status': result,
                'message': 'Получен статус Copilot'
            }
        except Exception as e:
            logger.error(f"Copilot status error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Ошибка при получении статуса Copilot'
            }
    
    def _register_copilot_tools(self):
        """Регистрирует инструменты Copilot"""
        if COPILOT_AVAILABLE and self.agent.local_env:
            # Регистрируем инструменты Copilot через local_env
            copilot_tools = {
                'copilot_authenticate': self.copilot_authenticate,
                'copilot_suggest': self.copilot_suggest,
                'copilot_explain': self.copilot_explain,
                'copilot_generate': self.copilot_generate,
                'copilot_review': self.copilot_review,
                'copilot_status': self.copilot_status
            }
            
            copilot_descriptions = {
                'copilot_authenticate': 'Аутентификация в GitHub Copilot',
                'copilot_suggest': 'Получить предложение по улучшению кода',
                'copilot_explain': 'Объяснить код',
                'copilot_generate': 'Сгенерировать код',
                'copilot_review': 'Провести code review',
                'copilot_status': 'Получить статус Copilot'
            }
            
            for name, func in copilot_tools.items():
                self.agent.local_env.register_tool(name, func, copilot_descriptions.get(name, ''))
            
            logger.info("Copilot tools registered successfully")
        else:
            logger.warning("Copilot not available, tools not registered")
            # Не блокируем регистрацию других инструментов!
