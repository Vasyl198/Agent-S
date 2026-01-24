"""
Система памяти агента на основе FAISS с обработкой ошибок
"""

from __future__ import annotations

import os
import pickle
import logging
import time
from typing import Dict, Any, List, Optional
import numpy as np

FAISS_AVAILABLE = False
faiss = None

try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except Exception:
    # Любая ошибка импорта FAISS не должна валить импорт проекта
    FAISS_AVAILABLE = False
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from .utils import logger

class AgentMemory:
    """Система памяти агента с FAISS индексом"""
    
    def __init__(self, persist_path: str = "universal_agent_memory", memory_size: int = 1000):
        if not FAISS_AVAILABLE or faiss is None:
            raise ImportError(
                "FAISS is not installed or failed to import. "
                "Install faiss-cpu/faiss-gpu, or disable AgentMemory usage."
            )
        
        self.persist_path = persist_path
        self.memory_size = memory_size
        self.embedding_dim = 384
        
        # Инициализация компонентов
        self.instructions = []
        self.results = []
        self.embeddings = []
        self.index = None
        self.encoder = None
        
        # Простой fallback для случаев без FAISS
        self.memory = []
        
        self._setup_components()
        self.load_memory()
    
    def _setup_components(self):
        """Настраивает компоненты памяти"""
        if FAISS_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.index = faiss.IndexFlatIP(self.embedding_dim)
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("FAISS и SentenceTransformer инициализированы")
            except Exception as e:
                logger.warning(f"Failed to setup FAISS components: {e}")
                self.index = None
                self.encoder = None
        else:
            logger.info("Using fallback memory system (FAISS not available)")
    
    def add_task(self, instruction: str, result: Dict[str, Any], plan: Dict[str, Any]) -> None:
        """Добавляет задачу в память"""
        try:
            if self.index and self.encoder:
                # Используем FAISS
                embedding = self.encoder.encode([instruction])[0]
                embedding = embedding / np.linalg.norm(embedding)  # Нормализация
                
                self.instructions.append(instruction)
                self.results.append(result)
                self.embeddings.append(embedding)
                
                # Добавляем в индекс
                embedding_array = np.array([embedding]).astype('float32')
                self.index.add(embedding_array)
                
                # Очистка старых записей
                if len(self.instructions) > self.memory_size:
                    self._cleanup_old_entries()
                    
            else:
                # Fallback - простой список
                self.memory.append({
                    'instruction': instruction,
                    'result': result,
                    'plan': plan,
                    'timestamp': time.time()  # Используем time.time() вместо len(self.memory)
                })
                if len(self.memory) > self.memory_size:
                    self.memory = self.memory[-self.memory_size:]
                    
            logger.debug(f"Added task to memory: {instruction[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to add task to memory: {e}")
    
    def _cleanup_old_entries(self) -> None:
        """Очищает старые записи из памяти"""
        if len(self.instructions) > self.memory_size:
            logger.info(f"Cleaning up old memories: {len(self.instructions)} -> {self.memory_size}")
            
            # Оставляем последние записи
            self.instructions = self.instructions[-self.memory_size:]
            self.results = self.results[-self.memory_size:]
            self.embeddings = self.embeddings[-self.memory_size:]
            
            # Пересоздаём индекс
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            if self.embeddings:
                embeddings_array = np.array(self.embeddings).astype('float32')
                faiss.normalize_L2(embeddings_array)
                self.index.add(embeddings_array)
    
    def recall_similar(self, query: str, top_k: int = 3) -> List[str]:
        """Возвращает похожие инструкции из памяти"""
        try:
            if self.index and self.encoder:
                # Поиск через FAISS
                query_embedding = self.encoder.encode([query])[0]
                query_embedding = query_embedding / np.linalg.norm(query_embedding)
                
                query_array = np.array([query_embedding]).astype('float32')
                distances, indices = self.index.search(query_array, min(top_k, len(self.instructions)))
                
                similar_tasks = []
                for idx in indices[0]:
                    if 0 <= idx < len(self.instructions):
                        similar_tasks.append(self.instructions[idx])
                
                return similar_tasks
            else:
                # Простой fallback поиск
                query_lower = query.lower()
                similar = []
                for item in self.memory:
                    if any(word in item['instruction'].lower() for word in query_lower.split()[:3]):
                        similar.append(item['instruction'])
                        if len(similar) >= top_k:
                            break
                return similar
                
        except Exception as e:
            logger.error(f"Failed to recall similar tasks: {e}")
            return []
    
    def search_memory(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Поиск по памяти для fallback системы"""
        try:
            if self.index and self.encoder:
                # Используем FAISS если доступен
                similar_instructions = self.recall_similar(query, top_k)
                results = []
                for instruction in similar_instructions:
                    # Находим соответствующие записи в памяти
                    for i, stored_instruction in enumerate(self.instructions):
                        if stored_instruction == instruction and i < len(self.results):
                            results.append({
                                'instruction': instruction,
                                'result': self.results[i],
                                'type': 'faiss_result'
                            })
                            break
                return results[:top_k]
            else:
                # Fallback поиск по списку
                query_lower = query.lower()
                query_words = query_lower.split()[:3]  # Простой fallback поиск
                query_str = str(query) if not isinstance(query, str) else query
                query_lower = query_str.lower()
                similar = []
                for item in self.memory:
                    if isinstance(item, dict) and 'instruction' in item:
                        item_str = str(item['instruction']) if not isinstance(item['instruction'], str) else item['instruction']
                        instruction_lower = item_str.lower()
                        # Проверяем совпадение слов
                        if any(word in instruction_lower for word in query_lower.split()[:3]):
                            similar.append(item['instruction'])
                            if len(similar) >= top_k:
                                break
                
                return similar
                
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []
    
    def save_memory(self) -> None:
        """Сохраняет память в файл"""
        try:
            if self.index and self.encoder:
                # Сохраняем FAISS данные
                faiss.write_index(self.index, f"{self.persist_path}.faiss")
                
                memory_data = {
                    'instructions': self.instructions,
                    'results': self.results,
                    'embeddings': self.embeddings,
                    'memory_size': self.memory_size
                }
                
                with open(f"{self.persist_path}.pkl", 'wb') as f:
                    pickle.dump(memory_data, f)
                    
            else:
                # Сохраняем fallback память
                with open(f"{self.persist_path}.pkl", 'wb') as f:
                    pickle.dump(self.memory, f)
                    
            logger.info(f"Memory saved to {self.persist_path}")
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def load_memory(self) -> None:
        """Загружает память из файла с обработкой ошибок"""
        if self.index and self.encoder:
            # Загрузка FAISS памяти
            try:
                if os.path.exists(f"{self.persist_path}.faiss") and os.path.exists(f"{self.persist_path}.pkl"):
                    self.index = faiss.read_index(f"{self.persist_path}.faiss")
                    
                    with open(f"{self.persist_path}.pkl", 'rb') as f:
                        memory_data = pickle.load(f)
                        
                    # Проверяем тип загруженных данных
                    if isinstance(memory_data, dict):
                        # Новый формат FAISS
                        self.instructions = memory_data.get('instructions', [])
                        self.results = memory_data.get('results', [])
                        self.embeddings = memory_data.get('embeddings', [])
                        self.memory_size = memory_data.get('memory_size', 1000)
                    elif isinstance(memory_data, list):
                        # Старый формат fallback - конвертируем в FAISS
                        logger.warning("Converting old fallback memory to FAISS format")
                        self.instructions = []
                        self.results = []
                        self.embeddings = []
                        
                        for item in memory_data:
                            if isinstance(item, dict) and 'instruction' in item:
                                self.instructions.append(item['instruction'])
                                self.results.append(item.get('result', {}))
                                
                                # Генерируем эмбеддинг для инструкции
                                if self.encoder:
                                    embedding = self.encoder.encode([item['instruction']])[0]
                                    embedding = embedding / np.linalg.norm(embedding)
                                    self.embeddings.append(embedding)
                        
                        self.memory_size = 1000
                        
                        # Пересоздаем индекс с новыми эмбеддингами
                        if self.embeddings:
                            embedding_array = np.array(self.embeddings).astype('float32')
                            faiss.normalize_L2(embedding_array)
                            self.index.add(embedding_array)
                    else:
                        logger.warning("Unknown memory format, starting fresh")
                        self.instructions = []
                        self.results = []
                        self.embeddings = []
                        self.memory_size = 1000
                    
                    # Очистка старых записей если >1000
                    if len(self.instructions) > 1000:
                        self._cleanup_old_entries()
                    
                    logger.info(f"Loaded {len(self.instructions)} memories from file")
                else:
                    logger.info("Memory files not found, starting with empty memory")
                    
            except FileNotFoundError:
                logger.info("Memory files not found, starting with empty memory")
            except (pickle.PickleError, EOFError) as e:
                logger.warning(f"Corrupt memory files, starting fresh: {e}")
                self.instructions = []
                self.results = []
                self.embeddings = []
                self.index = faiss.IndexFlatIP(self.embedding_dim)
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                self.instructions = []
                self.results = []
                self.embeddings = []
                self.index = faiss.IndexFlatIP(self.embedding_dim)
        else:
            # Загрузка fallback памяти
            try:
                if os.path.exists(f"{self.persist_path}.pkl"):
                    with open(f"{self.persist_path}.pkl", 'rb') as f:
                        loaded_data = pickle.load(f)
                    
                    # Убедимся что loaded_data это список
                    if isinstance(loaded_data, list):
                        self.memory = loaded_data
                    else:
                        logger.warning("Loaded data is not a list, converting to list")
                        self.memory = [loaded_data] if loaded_data else []
                    
                    logger.info(f"Loaded {len(self.memory)} memories from file")
            except FileNotFoundError:
                logger.info("Memory file not found, starting with empty memory")
                self.memory = []
            except (pickle.PickleError, EOFError) as e:
                logger.warning(f"Corrupt memory file, starting fresh: {e}")
                self.memory = []
            except Exception as e:
                logger.error(f"Failed to load fallback memory: {e}")
                self.memory = []
    
    def add_feedback(self, feedback: str) -> None:
        """Добавляет обратную связь в память"""
        try:
            if self.index and self.encoder:
                # Для FAISS версии
                feedback_text = f"FEEDBACK: {feedback}"
                embedding = self.encoder.encode([feedback_text])[0]
                
                # Нормализуем embedding
                embedding = embedding / np.linalg.norm(embedding)
                
                # Добавляем в память
                self.instructions.append(feedback_text)
                self.results.append({"type": "feedback", "content": feedback})
                self.embeddings.append(embedding)
                
                # Добавляем в индекс
                self.index.add(np.array([embedding]).astype('float32'))
                
                # Ограничиваем размер памяти
                if len(self.instructions) > self.memory_size:
                    self.instructions = self.instructions[-self.memory_size:]
                    self.results = self.results[-self.memory_size:]
                    self.embeddings = self.embeddings[-self.memory_size:]
                    # Пересоздаем индекс
                    self.index = faiss.IndexFlatIP(self.embedding_dim)
                    if self.embeddings:
                        self.index.add(np.array(self.embeddings).astype('float32'))
                
                logger.info(f"Added feedback to FAISS memory: {feedback}")
            else:
                # Для fallback версии
                self.memory.append({
                    "type": "feedback",
                    "content": feedback,
                    "timestamp": time.time()
                })
                
                # Ограничиваем размер памяти
                if len(self.memory) > self.memory_size:
                    self.memory = self.memory[-self.memory_size:]
                
                logger.info(f"Added feedback to memory: {feedback}")
                
        except Exception as e:
            logger.error(f"Failed to add feedback to memory: {e}")
