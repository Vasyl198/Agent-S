"""
Система самообучения и рефлексии агента
"""

import time
import json
from typing import Dict, Any, List, Optional
from .utils import logger

class SelfImprovementSystem:
    """Система самообучения и рефлексии"""
    
    def __init__(self, persist_path: str = "self_improvement_data"):
        self.persist_path = persist_path
        self.evaluations = []
        self.lessons = []
        self.reflection_history = []
        
    def add_evaluation(self, evaluation: Dict[str, Any]) -> None:
        """Добавляет оценку выполнения в историю"""
        try:
            evaluation['timestamp'] = time.time()
            self.evaluations.append(evaluation)
            
            # Ограничиваем размер истории
            if len(self.evaluations) > 1000:
                self.evaluations = self.evaluations[-1000:]
                
            logger.info(f"Added evaluation: {evaluation.get('feedback', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to add evaluation: {e}")
    
    def add_lesson(self, lesson: str, context: str = "") -> None:
        """Добавляет урок из выполнения"""
        try:
            lesson_entry = {
                'lesson': lesson,
                'context': context,
                'timestamp': time.time()
            }
            self.lessons.append(lesson_entry)
            
            # Ограничиваем размер
            if len(self.lessons) > 500:
                self.lessons = self.lessons[-500:]
                
            logger.info(f"Added lesson: {lesson[:50]}...")
        except Exception as e:
            logger.error(f"Failed to add lesson: {e}")
    
    def get_history(self) -> Dict[str, List]:
        """Возвращает историю самообучения"""
        try:
            return {
                'evaluations': self.evaluations[-20:],  # Последние 20 оценок
                'lessons': self.lessons[-20:],      # Последние 20 уроков
                'reflections': self.reflection_history[-20:]  # Последние 20 рефлексий
            }
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {'evaluations': [], 'lessons': [], 'reflections': []}
    
    def get_success_rate(self) -> float:
        """Вычисляет общий успех"""
        try:
            if not self.evaluations:
                return 0.0
                
            successful = sum(1 for e in self.evaluations if e.get('success_score', 0) > 0.7)
            return successful / len(self.evaluations)
        except Exception as e:
            logger.error(f"Failed to calculate success rate: {e}")
            return 0.0
    
    def get_common_errors(self) -> List[str]:
        """Анализирует частые ошибки"""
        try:
            error_patterns = {}
            
            for evaluation in self.evaluations:
                feedback = evaluation.get('feedback', '').lower()
                if 'error' in feedback or 'ошибка' in feedback:
                    # Извлекаем тип ошибки
                    if 'timeout' in feedback:
                        error_patterns['timeout'] = error_patterns.get('timeout', 0) + 1
                    elif 'network' in feedback or 'сеть' in feedback:
                        error_patterns['network'] = error_patterns.get('network', 0) + 1
                    elif 'permission' in feedback or 'доступ' in feedback:
                        error_patterns['permission'] = error_patterns.get('permission', 0) + 1
                    else:
                        error_patterns['other'] = error_patterns.get('other', 0) + 1
            
            # Сортируем по частоте
            sorted_errors = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
            return [error for error, count in sorted_errors[:5]]
        except Exception as e:
            logger.error(f"Failed to analyze common errors: {e}")
            return []
    
    def save_data(self) -> None:
        """Сохраняет данные самообучения"""
        try:
            data = {
                'evaluations': self.evaluations,
                'lessons': self.lessons,
                'reflections': self.reflection_history
            }
            
            with open(f"{self.persist_path}.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info("Self-improvement data saved")
        except Exception as e:
            logger.error(f"Failed to save self-improvement data: {e}")
    
    def load_data(self) -> None:
        """Загружает данные самообучения"""
        try:
            with open(f"{self.persist_path}.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.evaluations = data.get('evaluations', [])
            self.lessons = data.get('lessons', [])
            self.reflection_history = data.get('reflections', [])
            
            logger.info(f"Loaded self-improvement data: {len(self.evaluations)} evaluations")
        except FileNotFoundError:
            logger.info("Self-improvement data not found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load self-improvement data: {e}")
