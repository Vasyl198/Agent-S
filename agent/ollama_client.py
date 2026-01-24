"""
Клиент для работы с Ollama API с retry механизмами
"""

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .utils import logger

class OllamaClient:
    """Клиент для взаимодействия с Ollama API"""
    
    def __init__(self, model: str = "llama3.2:3b", timeout: int = 120, retries: int = 5):
        self.base_url = "http://localhost:11434"
        self.default_model = model
        self.timeout = timeout
        self.retry_attempts = retries
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
        before_sleep=lambda retry_state: logger.warning(f"Ollama retry {retry_state.attempt_number}/5...")
    )
    def _call_with_retry(self, prompt: str, model: str) -> str:
        """Вызов Ollama с retry механизмом"""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=self.timeout  # Используем настроенный таймаут
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    
    def generate(self, prompt: str, model: str = None) -> str:
        """Генерирует текст с помощью Ollama"""
        if model is None:
            model = self.default_model
            
        try:
            return self._call_with_retry(prompt, model)
        except Exception as e:
            logger.error(f"Ollama failed after 2 attempts: {e}")
            return None
    
    def is_available(self) -> bool:
        """Проверяет доступность Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> list:
        """Возвращает список доступных моделей"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []
