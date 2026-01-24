"""
Grok интеграция для Universal Agent
"""

import webbrowser
from datetime import datetime
from typing import Dict, Any

from .utils import logger


class GrokIntegration:
    """Интеграция с Grok для ручного режима обучения"""
    
    def __init__(self, agent):
        self.agent = agent
        self.grok_url = "https://grok.x.ai/"
    
    def ask_grok(self, question: str, gui_mode: bool = False) -> Dict[str, Any]:
        """Задает вопрос Grok (ручной режим без API ключа)"""
        try:
            if not gui_mode:
                # Консольный режим
                print(f"\n🌐 Открываю Grok для вопроса: {question}")
                print(f"📍 URL: {self.grok_url}")
                print("💡 Скопируйте ответ от Grok и вставьте его в консоль")
                
                # Открываем браузер
                webbrowser.open(self.grok_url)
                
                # Ждем ввода ответа
                print("\n" + "="*50)
                answer = input("🤖 Вставьте ответ от Grok (или Enter для отмены): ").strip()
                
                if not answer:
                    return {
                        'success': False,
                        'question': question,
                        'answer': '',
                        'message': 'Ответ не получен'
                    }
                
                return {
                    'success': True,
                    'question': question,
                    'answer': answer,
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Получен ответ от Grok на вопрос: {question}'
                }
            else:
                # GUI режим - возвращаем URL для открытия
                return {
                    'success': True,
                    'question': question,
                    'grok_url': self.grok_url,
                    'gui_mode': True,
                    'message': f'Откройте {self.grok_url} для вопроса: {question}'
                }
                
        except Exception as e:
            logger.error(f"Error asking Grok: {e}")
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'message': 'Ошибка при получении ответа от Grok'
            }
    
    def save_grok_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """Сохраняет ответ от Grok (для GUI режима)"""
        try:
            if not answer.strip():
                return {
                    'success': False,
                    'question': question,
                    'message': 'Ответ пустой'
                }
            
            # Сохраняем в память агента
            if self.agent.memory:
                plan_data = {
                    'type': 'grok_gui_learning',
                    'topic': question,
                    'timestamp': datetime.now().isoformat(),
                    'answer_length': len(answer)
                }
                
                self.agent.memory.add_task(
                    instruction=f"GUI Grok Question: {question}",
                    result={
                        'success': True,
                        'question': question,
                        'answer': answer,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'grok_gui_answer'
                    },
                    plan=plan_data
                )
            
            return {
                'success': True,
                'question': question,
                'answer': answer,
                'timestamp': datetime.now().isoformat(),
                'message': f'Ответ от Grok сохранен для вопроса: {question}'
            }
            
        except Exception as e:
            logger.error(f"Error saving Grok answer: {e}")
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'message': 'Ошибка при сохранении ответа от Grok'
            }
    
    def learn_from_grok(self, topic: str) -> Dict[str, Any]:
        """Обучается у Grok в ручном режиме с показом и запуском кода"""
        try:
            logger.info(f"Manual Grok learning about: {topic}")
            
            # Шаг 1: Получаем объяснение от Grok
            print(f"\n🎓 Обучение у Grok: {topic}")
            print(f"🌐 Открываю {self.grok_url}")
            
            # Открываем браузер
            webbrowser.open(self.grok_url)
            
            # Ждем ввода объяснения
            print("\n" + "="*50)
            print("🤖 Скопируйте объяснение от Grok и вставьте ниже:")
            grok_explanation = input("📖 Объяснение от Grok: ").strip()
            
            if not grok_explanation:
                return {
                    'success': False,
                    'topic': topic,
                    'message': 'Объяснение не получено'
                }
            
            print(f"\n📖 Получено объяснение от Grok:")
            print("-" * 50)
            print(grok_explanation[:500] + "..." if len(grok_explanation) > 500 else grok_explanation)
            print("-" * 50)
            
            # Шаг 2: Генерируем код на основе объяснения
            print(f"\n💻 Генерация кода на основе объяснения...")
            
            # Создаем промпт для генерации кода
            code_prompt = f"""
            Создай полный рабочий пример кода на основе объяснения от Grok:
            
            Тема: {topic}
            
            Объяснение от Grok:
            {grok_explanation}
            
            Требования к коду:
            1. Полностью функциональный и готовый к запуску
            2. Хорошо прокомментированный на русском
            3. Демонстрирует ключевые концепции из объяснения
            4. Использует лучшие практики из объяснения
            5. Включает все важные элементы, которые упомянул Grok
            
            Стиль кода:
            - Современный Python 3.x
            - Понятные имена переменных и функций
            - Обработка ошибок
            - Информативный вывод
            """
            
            generated_code = None
            if hasattr(self.agent, '_call_ollama') and callable(self.agent._call_ollama):
                generated_code = self.agent._call_ollama(code_prompt)
            
            if not generated_code:
                # Fallback - создаем базовый пример
                generated_code = f'''#!/usr/bin/env python3
"""
Пример на тему: {topic}
Создано на основе обучения у Grok
"""

def main():
    """Основная функция"""
    print(f"🎓 Обучение по теме: {topic}")
    print("📖 Основано на объяснении от Grok")
    print("💻 Это пример кода, сгенерированный на основе обучения")
    
    # Здесь может быть ваш код на основе объяснения Grok
    # Добавьте функциональность согласно объяснению от Grok
    
    print("✅ Код успешно выполнен!")

if __name__ == "__main__":
    main()
'''
            
            # Шаг 3: Сохраняем код в файл
            filename = f"grok_manual_{topic.replace(' ', '_')}.py"
            filepath = f"agent_generated/{filename}"
            
            import os
            os.makedirs("agent_generated", exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(generated_code)
            
            print(f"💾 Код сохранен в: {filepath}")
            
            # Шаг 4: Пробуем запустить код
            print(f"\n🚁 Запуск сгенерированного кода...")
            execution_result = {'success': False, 'output': '', 'error': ''}
            
            try:
                if self.agent.local_env:
                    # Передаем только код, filename не поддерживается
                    execution_result = self.agent.local_env.code_execution(code=generated_code)
            except Exception as e:
                execution_result['error'] = str(e)
            
            # Шаг 5: Сохраняем результат обучения в память
            learning_data = {
                'topic': topic,
                'grok_explanation': grok_explanation,
                'generated_code': generated_code,
                'filename': filename,
                'execution_result': execution_result,
                'timestamp': str(datetime.now()),
                'type': 'grok_manual_learning'
            }
            
            if self.agent.memory:
                plan_data = {
                    'type': 'grok_learning',
                    'topic': topic,
                    'filename': filename,
                    'execution_success': execution_result.get('success', False)
                }
                self.agent.memory.add_task(
                    instruction=f"Manual Grok Learning: {topic}",
                    result={
                        'success': True,
                        'topic': topic,
                        'grok_explanation': grok_explanation,
                        'generated_code': generated_code,
                        'filename': filename,
                        'execution_result': execution_result,
                        'timestamp': str(datetime.now()),
                        'type': 'grok_manual_learning'
                    },
                    plan=plan_data
                )
            
            print("✅ Результат обучения сохранен в памяти!")
            
            # Показываем результаты
            print(f"\n📊 Результаты обучения:")
            print(f"🎓 Тема: {topic}")
            print(f"📁 Файл: {filename}")
            print(f"🚀 Запуск: {'✅ Успешно' if execution_result.get('success') else '❌ Ошибка'}")
            
            if execution_result.get('success') and execution_result.get('output'):
                print(f"📤 Вывод: {execution_result.get('output', '')[:200]}...")
            
            return {
                'success': True,
                'topic': topic,
                'grok_explanation': grok_explanation,
                'generated_code': generated_code,
                'filename': filename,
                'execution_result': execution_result,
                'message': f'Ручное обучение у Grok завершено для темы: {topic}'
            }
            
        except Exception as e:
            logger.error(f"Error in learn_from_grok: {e}")
            return {
                'success': False,
                'topic': topic,
                'error': str(e),
                'message': 'Ошибка при ручном обучении у Grok'
            }
