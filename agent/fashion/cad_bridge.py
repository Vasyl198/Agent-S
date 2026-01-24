"""
CAD Bridge Module

Класс для интеграции с различными CAD системами.
Поддерживает Seamly2D, Valentina, Inkscape, FreeCAD.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json
import subprocess
import platform
import os
from dataclasses import dataclass
from enum import Enum


class CADSystem(Enum):
    """Поддерживаемые CAD системы"""
    SEAMLY2D = "seamly2d"
    VALENTINA = "valentina"
    INKSCAPE = "inkscape"
    FREECAD = "freecad"


@dataclass
class CADConfig:
    """Конфигурация CAD системы"""
    system: CADSystem
    executable_path: Optional[str] = None
    version: Optional[str] = None
    available: bool = False
    supported_formats: List[str] = None
    api_endpoint: Optional[str] = None
    api_port: Optional[int] = None


@dataclass
class ImportResult:
    """Результат импорта в CAD"""
    success: bool
    message: str
    file_path: Optional[str] = None
    cad_system: Optional[str] = None
    processing_time: Optional[float] = None
    error_details: Optional[str] = None


@dataclass
class ExportResult:
    """Результат экспорта из CAD"""
    success: bool
    message: str
    output_files: List[str]
    cad_system: Optional[str] = None
    processing_time: Optional[float] = None
    error_details: Optional[str] = None


class CADBridge:
    """
    Основной класс для интеграции с CAD системами.
    
    Поддерживаемые системы:
    - Seamly2D: профессиональная программа для лекал
    - Valentina: open-source CAD для одежды
    - Inkscape: векторный редактор
    - FreeCAD: параметрический 3D CAD
    """
    
    def __init__(self):
        self.configurations = {}
        self._initialize_configurations()
        self._detect_available_systems()
    
    def _initialize_configurations(self):
        """Инициализация конфигураций CAD систем"""
        
        # Seamly2D конфигурация
        self.configurations[CADSystem.SEAMLY2D] = CADConfig(
            system=CADSystem.SEAMLY2D,
            executable_path=self._find_executable("Seamly2D"),
            supported_formats=["val", "svg", "dxf", "json"],
            api_endpoint="http://localhost:8080",
            api_port=8080
        )
        
        # Valentina конфигурация
        self.configurations[CADSystem.VALENTINA] = CADConfig(
            system=CADSystem.VALENTINA,
            executable_path=self._find_executable("valentina"),
            supported_formats=["val", "vit", "svg", "dxf", "json"],
            api_endpoint="http://localhost:8081",
            api_port=8081
        )
        
        # Inkscape конфигурация
        self.configurations[CADSystem.INKSCAPE] = CADConfig(
            system=CADSystem.INKSCAPE,
            executable_path=self._find_executable("inkscape"),
            supported_formats=["svg", "pdf", "png", "dxf", "eps"],
            api_endpoint=None  # Inkscape не имеет API
        )
        
        # FreeCAD конфигурация
        self.configurations[CADSystem.FREECAD] = CADConfig(
            system=CADSystem.FREECAD,
            executable_path=self._find_executable("freecad"),
            supported_formats=["fcstd", "step", "iges", "dxf", "svg"],
            api_endpoint="http://localhost:8082",
            api_port=8082
        )
    
    def _find_executable(self, program_name: str) -> Optional[str]:
        """Поиск исполняемого файла программы"""
        system = platform.system().lower()
        
        if system == "windows":
            # Поиск в Program Files
            program_files = [
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), program_name),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), program_name),
                os.path.join(os.environ.get("ProgramW6432", "C:\\Program Files"), program_name)
            ]
            
            for path in program_files:
                if os.path.exists(path):
                    # Поиск .exe файла
                    for file in os.listdir(path):
                        if file.endswith(".exe") and program_name.lower() in file.lower():
                            return os.path.join(path, file)
            
            # Поиск через PATH
            try:
                result = subprocess.run(["where", program_name], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            except:
                pass
                
        elif system in ["linux", "darwin"]:
            # Поиск через which/whereis
            try:
                result = subprocess.run(["which", program_name], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
            
            # Поиск в типичных местах для Linux/macOS
            common_paths = [
                f"/usr/bin/{program_name}",
                f"/usr/local/bin/{program_name}",
                f"/opt/{program_name}/bin/{program_name}",
                f"/Applications/{program_name.title()}.app/Contents/MacOS/{program_name}"
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    def _detect_available_systems(self):
        """Обнаружение доступных CAD систем"""
        for cad_system, config in self.configurations.items():
            if config.executable_path and os.path.exists(config.executable_path):
                config.available = True
                self._get_version(cad_system)
            else:
                config.available = False
    
    def _get_version(self, cad_system: CADSystem) -> Optional[str]:
        """Получение версии CAD системы"""
        config = self.configurations[cad_system]
        if not config.executable_path:
            return None
        
        try:
            if cad_system == CADSystem.INKSCAPE:
                result = subprocess.run([config.executable_path, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip().split()[-1]
                    
            elif cad_system == CADSystem.FREECAD:
                result = subprocess.run([config.executable_path, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
                    
            elif cad_system in [CADSystem.SEAMLY2D, CADSystem.VALENTINA]:
                result = subprocess.run([config.executable_path, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
                    
        except Exception:
            pass
        
        return None
    
    def validate_cad(self, cad_name: str) -> Dict[str, Any]:
        """
        Валидация CAD системы
        
        Args:
            cad_name: Название CAD системы
            
        Returns:
            Словарь с результатом валидации
        """
        try:
            # Нормализация имени системы
            cad_name_lower = cad_name.lower()
            
            # Поиск соответствующей CAD системы
            cad_system = None
            for system in CADSystem:
                if system.value.lower() == cad_name_lower:
                    cad_system = system
                    break
            
            if not cad_system:
                return {
                    "valid": False,
                    "error": f"Неподдерживаемая CAD система: {cad_name}",
                    "supported_systems": [s.value for s in CADSystem]
                }
            
            config = self.configurations[cad_system]
            
            # Проверка доступности
            if not config.available:
                return {
                    "valid": False,
                    "error": f"CAD система {cad_name} не найдена",
                    "suggestions": self._get_installation_suggestions(cad_system)
                }
            
            # Проверка форматов
            validation_result = {
                "valid": True,
                "system": cad_system.value,
                "version": config.version,
                "executable_path": config.executable_path,
                "supported_formats": config.supported_formats,
                "api_available": config.api_endpoint is not None
            }
            
            # Дополнительная проверка для систем с API
            if config.api_endpoint:
                api_status = self._check_api_status(cad_system)
                validation_result["api_status"] = api_status
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Ошибка валидации CAD: {str(e)}"
            }
    
    def _get_installation_suggestions(self, cad_system: CADSystem) -> List[str]:
        """Получить предложения по установке CAD системы"""
        suggestions = []
        
        if cad_system == CADSystem.SEAMLY2D:
            suggestions = [
                "Скачать с официального сайта: https://seamly2d.org/",
                "Установить через Chocolatey: choco install seamly2d",
                "Установить через Snap: snap install seamly2d"
            ]
        elif cad_system == CADSystem.VALENTINA:
            suggestions = [
                "Скачать с официального сайта: https://valentinaproject.org/",
                "Установить через Chocolatey: choco install valentina",
                "Установить через Snap: snap install valentina"
            ]
        elif cad_system == CADSystem.INKSCAPE:
            suggestions = [
                "Скачать с официального сайта: https://inkscape.org/",
                "Установить через Chocolatey: choco install inkscape",
                "Установить через Snap: snap install inkscape",
                "Установить через Homebrew: brew install inkscape"
            ]
        elif cad_system == CADSystem.FREECAD:
            suggestions = [
                "Скачать с официального сайта: https://www.freecadweb.org/",
                "Установить через Chocolatey: choco install freecad",
                "Установить через Snap: snap install freecad",
                "Установить через Homebrew: brew install freecad"
            ]
        
        return suggestions
    
    def _check_api_status(self, cad_system: CADSystem) -> Dict[str, Any]:
        """Проверить статус API CAD системы"""
        config = self.configurations[cad_system]
        
        if not config.api_endpoint:
            return {"available": False, "reason": "API не поддерживается"}
        
        try:
            import requests
            response = requests.get(f"{config.api_endpoint}/status", timeout=5)
            
            if response.status_code == 200:
                return {
                    "available": True,
                    "status": "running",
                    "version": response.json().get("version", "unknown")
                }
            else:
                return {
                    "available": False,
                    "status": "error",
                    "http_status": response.status_code
                }
                
        except Exception as e:
            return {
                "available": False,
                "status": "unreachable",
                "error": str(e)
            }
    
    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить поддерживаемые форматы для всех CAD систем
        
        Returns:
            Словарь с информацией о форматах
        """
        formats_info = {}
        
        for cad_system, config in self.configurations.items():
            formats_info[cad_system.value] = {
                "available": config.available,
                "version": config.version,
                "supported_formats": config.supported_formats,
                "api_available": config.api_endpoint is not None,
                "executable_path": config.executable_path
            }
        
        return formats_info
    
    def import_to_cad(self, 
                      cad_system: CADSystem,
                      data: Dict[str, Any],
                      import_format: str = "json",
                      file_path: Optional[str] = None) -> ImportResult:
        """
        Импорт данных в CAD систему
        
        Args:
            cad_system: CAD система
            data: Данные для импорта
            import_format: Формат импорта
            file_path: Путь к файлу (если None, создается временный файл)
            
        Returns:
            Результат импорта
        """
        import time
        start_time = time.time()
        
        try:
            config = self.configurations[cad_system]
            
            if not config.available:
                return ImportResult(
                    success=False,
                    message=f"CAD система {cad_system.value} не доступна",
                    cad_system=cad_system.value,
                    error_details="Система не установлена или не найдена"
                )
            
            if import_format not in config.supported_formats:
                return ImportResult(
                    success=False,
                    message=f"Формат {import_format} не поддерживается {cad_system.value}",
                    cad_system=cad_system.value,
                    error_details=f"Поддерживаемые форматы: {', '.join(config.supported_formats)}"
                )
            
            # Создание временного файла если не указан
            if file_path is None:
                temp_dir = Path.cwd() / "temp" / "cad_import"
                temp_dir.mkdir(parents=True, exist_ok=True)
                file_path = temp_dir / f"import_{int(time.time())}.{import_format}"
            
            # Подготовка данных для импорта
            if import_format == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                # Для других форматов нужна конвертация
                return ImportResult(
                    success=False,
                    message=f"Импорт формата {import_format} еще не реализован",
                    cad_system=cad_system.value,
                    error_details="Требуется дополнительная реализация"
                )
            
            # Запуск CAD системы с файлом
            if cad_system in [CADSystem.INKSCAPE]:
                # Inkscape - просто открывает файл
                subprocess.Popen([config.executable_path, str(file_path)])
                
            elif cad_system in [CADSystem.SEAMLY2D, CADSystem.VALENTINA]:
                # Seamly2D/Valentina - открывает файл через командную строку
                subprocess.Popen([config.executable_path, str(file_path)])
                
            elif cad_system == CADSystem.FREECAD:
                # FreeCAD - открывает файл через командную строку
                subprocess.Popen([config.executable_path, str(file_path)])
            
            processing_time = time.time() - start_time
            
            return ImportResult(
                success=True,
                message=f"Файл успешно импортирован в {cad_system.value}",
                file_path=str(file_path),
                cad_system=cad_system.value,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ImportResult(
                success=False,
                message=f"Ошибка импорта в {cad_system.value}",
                cad_system=cad_system.value,
                processing_time=processing_time,
                error_details=str(e)
            )
