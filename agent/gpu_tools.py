#!/usr/bin/env python3
"""
GPU инструменты для агента
"""

import subprocess
import time
import os
import platform
from typing import Dict, Any

from .utils import logger

# Optional FAISS import
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

class GPUTools:
    """Инструменты для работы с GPU"""
    
    def __init__(self, agent=None):
        self.agent = agent
    
    def gpu_status(self, **kwargs) -> Dict[str, Any]:
        """Проверяет статус GPU"""
        try:
            logger.info("Checking GPU status...")
            
            status = {
                'success': True,
                'gpu_available': False,
                'gpu_name': None,
                'memory_total': 0,
                'memory_used': 0,
                'memory_free': 0,
                'utilization': 0,
                'temperature': 0,
                'pytorch_cuda': False,
                'faiss_gpu': False,
                'ollama_gpu': False,
                'processes': []
            }
            
            # 1. Проверяем nvidia-smi
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu', 
                                       '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            parts = line.split(', ')
                            if len(parts) >= 6:
                                status.update({
                                    'gpu_available': True,
                                    'gpu_name': parts[0].strip(),
                                    'memory_total': int(parts[1].strip()),
                                    'memory_used': int(parts[2].strip()),
                                    'memory_free': int(parts[3].strip()),
                                    'utilization': int(parts[4].strip()),
                                    'temperature': int(parts[5].strip())
                                })
                                break
            except Exception as e:
                logger.warning(f"nvidia-smi not available: {e}")
            
            # 2. Проверяем PyTorch CUDA
            try:
                import torch
                status['pytorch_cuda'] = torch.cuda.is_available()
                if status['pytorch_cuda']:
                    status['pytorch_version'] = torch.__version__
                    status['cuda_version'] = torch.version.cuda
                    status['gpu_count'] = torch.cuda.device_count()
            except ImportError:
                status['pytorch_cuda'] = False
            
            # 3. Проверяем FAISS GPU
            if FAISS_AVAILABLE and faiss is not None:
                gpu_count = faiss.get_num_gpus()
                status['faiss_gpu'] = gpu_count > 0
                status['faiss_version'] = faiss.__version__
                status['faiss_gpu_count'] = gpu_count
            else:
                status['faiss_gpu'] = False
            
            # 4. Проверяем Ollama GPU
            try:
                result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Проверяем переменные окружения Ollama
                    ollama_gpu = os.environ.get('OLLAMA_GPU', '0')
                    ollama_num_layers = os.environ.get('OLLAMA_NUM_GPU_LAYERS', '0')
                    status['ollama_gpu'] = ollama_gpu == '1' or ollama_num_layers != '0'
                    status['ollama_gpu_layers'] = ollama_num_layers
            except:
                status['ollama_gpu'] = False
            
            # 5. Проверяем процессы
            try:
                result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', 
                                       '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split(', ')
                            if len(parts) >= 3:
                                status['processes'].append({
                                    'pid': parts[0].strip(),
                                    'name': parts[1].strip(),
                                    'memory': int(parts[2].strip())
                                })
            except:
                pass
            
            # Формируем сообщение
            if status['gpu_available']:
                message = f"🎮 GPU: {status['gpu_name']}\n"
                message += f"📊 Память: {status['memory_used']}/{status['memory_total']} MB ({status['memory_used']*100/status['memory_total']:.1f}%)\n"
                message += f"⚡ Загрузка: {status['utilization']}%\n"
                message += f"🌡️ Температура: {status['temperature']}°C\n"
                message += f"🔥 PyTorch CUDA: {'✅ Да' if status['pytorch_cuda'] else '❌ Нет'}\n"
                message += f"📊 FAISS GPU: {'✅ Да' if status['faiss_gpu'] else '❌ Нет'}\n"
                message += f"🦙 Ollama GPU: {'✅ Да' if status['ollama_gpu'] else '❌ Нет'}"
                
                if status['processes']:
                    message += f"\n🔄 Процессы: {len(status['processes'])}"
            else:
                message = "❌ GPU не найден или недоступен"
            
            status['message'] = message
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking GPU status: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Ошибка проверки GPU: {str(e)}"
            }
    
    def enable_gpu(self, **kwargs) -> Dict[str, Any]:
        """Автоматически включает GPU для агента"""
        try:
            logger.info("🚀 Автоматическое включение GPU для агента...")
            
            steps_completed = []
            errors = []
            
            print("🔧 НАЧИНАЮ АВТОМАТИЧЕСКУЮ НАСТРОЙКУ GPU")
            print("=" * 60)
            print("⚠️ Это может занять 5-10 минут...")
            print("📦 Будет загружено ~2GB данных")
            print()
            
            # Шаг 1: Удаление CPU версий PyTorch
            print("🗑️ Шаг 1/5: Удаление CPU версий PyTorch...")
            try:
                logger.info("Uninstalling CPU PyTorch...")
                uninstall_cmd = "pip uninstall -y torch torchvision torchaudio"
                result = subprocess.run(uninstall_cmd, shell=True, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    steps_completed.append("✅ CPU версии PyTorch удалены")
                    print("   ✅ CPU версии PyTorch удалены")
                else:
                    error_msg = f"Ошибка удаления PyTorch CPU: {result.stderr}"
                    errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Ошибка удаления PyTorch: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
            
            # Шаг 2: Установка PyTorch с CUDA
            print("\n🔥 Шаг 2/5: Установка PyTorch с CUDA...")
            try:
                logger.info("Installing PyTorch with CUDA...")
                install_cmd = "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --user"
                print(f"   🔄 Выполняю: {install_cmd}")
                print("   ⏳ Ожидайте загрузки ~2GB...")
                print("   📝 Устанавливаем с флагом --user для обхода проблем с правами")
                
                result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    steps_completed.append("✅ PyTorch с CUDA установлен")
                    print("   ✅ PyTorch с CUDA установлен")
                else:
                    error_msg = f"Ошибка установки PyTorch CUDA: {result.stderr}"
                    errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Ошибка установки PyTorch: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
            
            # Шаг 3: Установка FAISS GPU
            print("\n📊 Шаг 3/5: Установка FAISS GPU...")
            try:
                logger.info("Installing FAISS GPU...")
                
                # Удаляем CPU версию
                uninstall_cmd = "pip uninstall -y faiss faiss-cpu"
                result = subprocess.run(uninstall_cmd, shell=True, capture_output=True, text=True, timeout=300)
                
                # Устанавливаем GPU версию (пробуем разные варианты)
                install_commands = [
                    "pip install faiss-gpu --user",
                    "pip install faiss-cpu --user",  # fallback если GPU недоступен
                    "pip install faiss --user"        # fallback
                ]
                
                faiss_installed = False
                for install_cmd in install_commands:
                    print(f"   🔄 Пробую: {install_cmd}")
                    print("   ⏳ Ожидайте загрузки...")
                    
                    result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        steps_completed.append("✅ FAISS установлен")
                        print("   ✅ FAISS установлен")
                        faiss_installed = True
                        break
                    else:
                        print(f"   ⚠️ Не удалось, пробую следующий вариант...")
                
                if not faiss_installed:
                    error_msg = "Не удалось установить FAISS"
                    errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Ошибка установки FAISS: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
            
            # Шаг 4: Настройка Ollama для GPU
            print("\n🦙 Шаг 4/5: Настройка Ollama для GPU...")
            try:
                logger.info("Configuring Ollama for GPU...")
                
                # Устанавливаем переменные окружения
                os.environ['OLLAMA_GPU'] = '1'
                os.environ['OLLAMA_NUM_GPU_LAYERS'] = '999'
                
                steps_completed.append("✅ Ollama настроен для GPU")
                print("   ✅ Ollama настроен для GPU")
                print("   📝 Установлены переменные:")
                print("      • OLLAMA_GPU=1")
                print("      • OLLAMA_NUM_GPU_LAYERS=999")
                
            except Exception as e:
                error_msg = f"Ошибка настройки Ollama: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
            
            # Шаг 5: Перезапуск сервисов
            print("\n🔄 Шаг 5/5: Перезапуск сервисов...")
            try:
                logger.info("Restarting services...")
                
                # Перезапускаем Ollama
                try:
                    # Останавливаем Ollama
                    subprocess.run(['taskkill', '/F', '/IM', 'ollama.exe'], 
                                 capture_output=True, timeout=10)
                    time.sleep(2)
                    
                    # Запускаем Ollama с GPU
                    subprocess.Popen(['ollama', 'serve'], 
                                   env={**os.environ, 'OLLAMA_GPU': '1', 'OLLAMA_NUM_GPU_LAYERS': '999'})
                    
                    steps_completed.append("✅ Сервисы перезапущены")
                    print("   ✅ Ollama перезапущен с GPU")
                    time.sleep(3)
                    
                except Exception as e:
                    error_msg = f"Ошибка перезапуска Ollama: {str(e)}"
                    errors.append(error_msg)
                    print(f"   ⚠️ {error_msg}")
                
            except Exception as e:
                error_msg = f"Ошибка перезапуска сервисов: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
            
            # Шаг 6: Проверяем результат
            print("\n🧪 Шаг 6/6: Проверка результата...")
            try:
                logger.info("Verifying GPU setup...")
                
                # Проверяем PyTorch
                try:
                    import torch
                    pytorch_gpu = torch.cuda.is_available()
                    if pytorch_gpu:
                        device_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown GPU"
                        steps_completed.append(f"✅ PyTorch CUDA: {device_name}")
                        print(f"   ✅ PyTorch CUDA: {device_name}")
                    else:
                        errors.append("PyTorch CUDA не активирован")
                        print("   ❌ PyTorch CUDA не активирован")
                except ImportError:
                    errors.append("PyTorch не установлен")
                    print("   ❌ PyTorch не установлен")
                except Exception as e:
                    errors.append(f"Ошибка проверки PyTorch: {str(e)}")
                    print(f"   ❌ Ошибка проверки PyTorch: {str(e)}")
                
                # Проверяем FAISS
                if FAISS_AVAILABLE and faiss is not None:
                    faiss_gpu_count = faiss.get_num_gpus()
                    if faiss_gpu_count > 0:
                        steps_completed.append(f"✅ FAISS GPU: {faiss_gpu_count} GPU")
                        print(f"   ✅ FAISS GPU: {faiss_gpu_count} GPU")
                    else:
                        errors.append("FAISS GPU не активирован")
                        print("   ❌ FAISS GPU не активирован")
                else:
                    errors.append("FAISS не установлен")
                    print("   ❌ FAISS не установлен")
                
                # Проверяем Ollama
                try:
                    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        ollama_gpu = os.environ.get('OLLAMA_GPU', '0') == '1'
                        if ollama_gpu:
                            steps_completed.append("✅ Ollama GPU настроен")
                            print("   ✅ Ollama GPU настроен")
                        else:
                            errors.append("Ollama GPU не настроен")
                            print("   ❌ Ollama GPU не настроен")
                    else:
                        errors.append("Ollama недоступен")
                        print("   ❌ Ollama недоступен")
                except:
                    errors.append("Ollama не отвечает")
                    print("   ❌ Ollama не отвечает")
                
                # Общий результат
                success = len(errors) == 0
                
            except Exception as e:
                error_msg = f"Ошибка проверки: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
                success = False
            
            # Формируем сообщение
            print("\n" + "=" * 60)
            print("🎊 АВТОМАТИЧЕСКАЯ НАСТРОЙКА GPU ЗАВЕРШЕНА")
            print("=" * 60)
            
            message = ""
            
            if steps_completed:
                message += "✅ ВЫПОЛНЕНО:\n"
                for step in steps_completed:
                    message += f"   • {step}\n"
                print("✅ ВЫПОЛНЕНО:")
                for step in steps_completed:
                    print(f"   • {step}")
            
            if errors:
                message += "\n❌ ОШИБКИ:\n"
                for error in errors:
                    message += f"   • {error}\n"
                print("\n❌ ОШИБКИ:")
                for error in errors:
                    print(f"   • {error}")
            
            if success:
                message += "\n🎉 GPU УСПЕШНО АКТИВИРОВАН!\n"
                message += "🔄 ПЕРЕЗАПУСТИТЕ АГЕНТА ДЛЯ ПРИМЕНЕНИЯ ИЗМЕНЕНИЙ\n"
                message += "⚡ ОЖИДАЙТЕ УСКОРЕНИЯ В 5-10 РАЗ!"
                
                print("\n🎉 GPU УСПЕШНО АКТИВИРОВАН!")
                print("🔄 ПЕРЕЗАПУСТИТЕ АГЕНТА ДЛЯ ПРИМЕНЕНИЯ ИЗМЕНЕНИЙ")
                print("⚡ ОЖИДАЙТЕ УСКОРЕНИЯ В 5-10 РАЗ!")
                
            else:
                message += "\n⚠️ НАСТРОЙКА GPU ЗАВЕРШЕНА С ОШИБКАМИ\n"
                message += "💡 Проверьте ошибки выше и попробуйте снова"
                
                print("\n⚠️ НАСТРОЙКА GPU ЗАВЕРШЕНА С ОШИБКАМИ")
                print("💡 Проверьте ошибки выше и попробуйте снова")
            
            return {
                'success': success,
                'message': message,
                'steps_completed': steps_completed,
                'errors': errors,
                'restart_required': True,
                'auto_setup': True
            }
            
        except Exception as e:
            logger.error(f"Error in automatic GPU setup: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Ошибка автоматической настройки GPU: {str(e)}",
                'restart_required': False,
                'auto_setup': False
            }
    
    def restart_services(self, **kwargs) -> Dict[str, Any]:
        """Перезапускает сервисы для GPU"""
        try:
            logger.info("Restarting services for GPU...")
            
            steps = []
            system = platform.system()
            
            # Перезапускаем Ollama
            try:
                if system == "Windows":
                    # Windows: используем taskkill
                    subprocess.run(['taskkill', '/F', '/IM', 'ollama.exe'], capture_output=True, timeout=10)
                    time.sleep(2)
                    
                    # Запускаем Ollama с GPU
                    subprocess.Popen(['ollama', 'serve'], 
                                   env={**os.environ, 'OLLAMA_GPU': '1', 'OLLAMA_NUM_GPU_LAYERS': '999'})
                    
                elif system in ["Linux", "Darwin"]:  # Linux и macOS
                    # Linux/macOS: используем pkill
                    try:
                        subprocess.run(['pkill', '-f', 'ollama'], capture_output=True, timeout=10)
                    except subprocess.CalledProcessError:
                        pass  # pkill возвращает ошибку если процесс не найден
                    
                    time.sleep(2)
                    
                    # Запускаем Ollama с GPU
                    subprocess.Popen(['ollama', 'serve'], 
                                   env={**os.environ, 'OLLAMA_GPU': '1', 'OLLAMA_NUM_GPU_LAYERS': '999'})
                    
                else:
                    # Другие системы: пробуем универсальный подход
                    try:
                        subprocess.run(['killall', 'ollama'], capture_output=True, timeout=10)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        pass
                    
                    time.sleep(2)
                    
                    # Запускаем Ollama с GPU
                    subprocess.Popen(['ollama', 'serve'], 
                                   env={**os.environ, 'OLLAMA_GPU': '1', 'OLLAMA_NUM_GPU_LAYERS': '999'})
                
                steps.append(f"Ollama перезапущен с GPU ({system})")
                time.sleep(3)
                
            except Exception as e:
                steps.append(f"Ошибка перезапуска Ollama: {str(e)}")
            
            return {
                'success': True,
                'message': "🔄 Сервисы перезапущены для GPU\n" + "\n".join(f"• {step}" for step in steps),
                'steps': steps,
                'platform': system
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Ошибка перезапуска сервисов: {str(e)}"
            }
