"""
Text Design Interface Module

Модуль для преобразования текстовых запросов пользователя в структурированные модификации лекал
с использованием локальной модели Ollama.

Интеграция с Agent-S Fashion:
- Анализ естественного языка
- Преобразование в структурированные модификации
- Применение изменений к базовым лекалам
- Валидация результатов
"""

from typing import Dict, List, Any, Optional, Union, Literal
from dataclasses import dataclass
from enum import Enum
import json
import re
import logging
from pathlib import Path
from datetime import datetime

# Ollama integration
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama library not found. Text design interface will use fallback mode.")

from .pattern_maker import PatternMaker, PatternType
from .style_engine import StyleEngine
from .seam_allowance import SeamAllowance


class ClothingType(Enum):
    """Поддерживаемые типы одежды"""
    SHIRT = "shirt"
    DRESS = "dress"
    JACKET = "jacket"
    PANTS = "pants"
    SKIRT = "skirt"


class FitType(Enum):
    """Типы посадки"""
    SLIM = "slim"
    FITTED = "fitted"
    STANDARD = "standard"
    LOOSE = "loose"
    OVERSIZE = "oversize"


class SleeveType(Enum):
    """Типы рукавов"""
    NONE = "none"
    SHORT = "short"
    THREE_QUARTER = "three_quarter"
    LONG = "long"
    BELL = "bell"
    RAGLAN = "raglan"


class NecklineType(Enum):
    """Типы горловины"""
    ROUND = "round"
    V_NECK = "v_neck"
    SQUARE = "square"
    BOAT = "boat"
    HIGH = "high"
    OFF_SHOULDER = "off_shoulder"


class CollarType(Enum):
    """Типы воротников"""
    NONE = "none"
    STAND = "stand"
    SHIRT = "shirt"
    PETER_PAN = "peter_pan"
    NOTCH = "notch"


@dataclass
class PatternModification:
    """Структура модификации лекала"""
    fit_type: Optional[FitType] = None
    sleeve_type: Optional[SleeveType] = None
    sleeve_length: Optional[str] = None  # "+2.0 cm", "-1.5 cm"
    neckline_type: Optional[NecklineType] = None
    neckline_depth: Optional[str] = None  # "+3.0 cm", "-2.0 cm"
    collar_type: Optional[CollarType] = None
    ease_chest: Optional[str] = None  # "+5 cm", "-2 cm"
    ease_waist: Optional[str] = None
    ease_hips: Optional[str] = None
    length_modification: Optional[str] = None  # "+5 cm", "-3 cm"
    dart_modification: Optional[str] = None  # "deeper", "shallower", "remove"
    pocket_style: Optional[str] = None
    closure_type: Optional[str] = None  # "zipper", "buttons", "pullover"
    fabric_type: Optional[str] = None  # "stretch", "woven", "knit"
    additional_features: Optional[List[str]] = None
    
    # Новые поля для юбок
    skirt_style: Optional[str] = None  # "straight", "a_line", "flare", "pencil"
    waistband_type: Optional[str] = None  # "wide", "narrow", "elastic"
    closure_position: Optional[str] = None  # "side_zip", "back_zip", "buttons"
    pocket_type: Optional[str] = None  # "inseam", "patch", "none"
    slit_type: Optional[str] = None  # "front", "back", "side", "none"
    
    # Новые поля для пиджаков
    lapel_type: Optional[str] = None  # "notch", "peak", "shawl"
    lapel_width: Optional[str] = None  # "wide", "narrow", "+2 cm"
    button_stance: Optional[str] = None  # "single_breasted", "double_breasted"


class TextDesignInterface:
    """
    Интерфейс для преобразования текстовых запросов в модификации лекал
    с использованием Ollama AI модели
    """
    
    def __init__(self, model_name: str = "llama3.2", fallback_mode: bool = False):
        """
        Инициализация интерфейса
        
        Args:
            model_name: Название модели Ollama
            fallback_mode: Использовать fallback режим без Ollama
        """
        self.model_name = model_name
        self.fallback_mode = fallback_mode or not OLLAMA_AVAILABLE
        self.pattern_maker = PatternMaker()
        self.style_engine = StyleEngine()
        self.seam_allowance = SeamAllowance()
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Проверка доступности Ollama
        if not self.fallback_mode:
            try:
                # Проверяем доступные модели
                models = ollama.list()
                if self.model_name not in [m['name'] for m in models.get('models', [])]:
                    self.logger.warning(f"Model {self.model_name} not found. Available: {[m['name'] for m in models.get('models', [])]}")
                    self.fallback_mode = True
            except Exception as e:
                self.logger.warning(f"Ollama not available: {e}. Using fallback mode.")
                self.fallback_mode = True
        
        # Словари для fallback режима
        self._init_fallback_patterns()
    
    def _init_fallback_patterns(self):
        """Инициализация паттернов для fallback режима"""
        self.fit_patterns = {
            r'приталенный|slim|fitted|облегающий': FitType.SLIM,
            r'стандартный|standard|обычный|классический': FitType.STANDARD,
            r'свободный|loose|просторный': FitType.LOOSE,
            r'оверсайз|oversize|широкий': FitType.OVERSIZE
        }
        
        # Новые паттерны для юбок
        self.skirt_style_patterns = {
            r'прямая юбка|straight|классическая': 'straight',
            r'юбка карандаш|pencil|узкая': 'pencil',
            r'а-силуэт|a-line|трапеция': 'a_line',
            r'клёш|flare|солнце': 'flare'
        }
        
        self.waistband_patterns = {
            r'широкий пояс|wide пояс': 'wide',
            r'узкий пояс|narrow пояс': 'narrow',
            r'эластичный пояс|elastic пояс|на резинке|резинка': 'elastic'
        }
        
        self.closure_patterns = {
            r'молния сбоку|side_zip|боковая молния': 'side_zip',
            r'молния сзади|back_zip|задняя молния': 'back_zip',
            r'пуговицы|buttons|кнопки': 'buttons'
        }
        
        self.pocket_patterns = {
            r'в шве|inseam|боковые карманы': 'inseam',
            r'накладные|patch|накладные карманы': 'patch',
            r'без карманов|none|без карманов': 'none'
        }
        
        self.slit_patterns = {
            r'разрез спереди|front|передний разрез': 'front',
            r'разрез сзади|back|задний разрез': 'back',
            r'разрез сбоку|side|боковой разрез': 'side',
            r'без разреза|none|без разреза': 'none'
        }
        
        self.sleeve_patterns = {
            r'короткий|short|без рукава': SleeveType.SHORT,
            r'длинный|long': SleeveType.LONG,
            r'три четверти|three quarter|3/4': SleeveType.THREE_QUARTER,
            r'колокольчик|bell': SleeveType.BELL,
            r'реглан|raglan': SleeveType.RAGLAN
        }
        
        self.neckline_patterns = {
            r'круглый|round': NecklineType.ROUND,
            r'v-образный|v-neck|v образный|v-горловина|v-образная': NecklineType.V_NECK,
            r'квадратный|square': NecklineType.SQUARE,
            r'лодочка|boat': NecklineType.BOAT,
            r'высокий|high': NecklineType.HIGH,
            r'без плеч|off shoulder': NecklineType.OFF_SHOULDER
        }
        
        self.collar_patterns = {
            r'стойка|stand': CollarType.STAND,
            r'рубашечный|shirt': CollarType.SHIRT,
            r'питер пэн|peter pan': CollarType.PETER_PAN,
            r'шалевый|notch': CollarType.NOTCH
        }
        
        self.general_pocket_patterns = {
            r'боковой|side|боковые': 'side',
            r'накладной|patch|накладные': 'patch',
            r'в рамку|welt|врезной': 'welt',
            r'карго|cargo': 'cargo'
        }
        
        self.closure_patterns = {
            r'молния|zipper|застежка-молния': 'zipper',
            r'пуговицы|buttons|пуговиц': 'buttons',
            r'накидка|pullover|через голову': 'pullover',
            r'крючки|hooks': 'hooks'
        }
        
        # Новые паттерны для пиджаков
        self.lapel_patterns = {
            r'лацканы|notch lapel|notch': 'notch',
            r'острые|peak lapel|peak': 'peak',
            r'шалевый|shawl lapel|shawl': 'shawl'
        }
        
        self.lapel_width_patterns = {
            r'широкие лацканы|wide lapel|широкий': 'wide',
            r'узкие лацканы|narrow lapel|узкий': 'narrow'
        }
        
        self.button_stance_patterns = {
            r'двубортный|double breasted|double': 'double_breasted',
            r'однобортный|single breasted|single': 'single_breasted'
        }
    
    def interpret_design_request(
        self, 
        user_prompt: str, 
        base_measurements: Dict[str, float], 
        clothing_type: str
    ) -> Dict[str, Any]:
        """
        Анализ текстового запроса и преобразование в модификации лекала
        
        Args:
            user_prompt: Текстовый запрос пользователя
            base_measurements: Базовые мерки
            clothing_type: Тип одежды
            
        Returns:
            Словарь с модификациями лекала
        """
        try:
            if self.fallback_mode:
                return self._fallback_interpretation(user_prompt, clothing_type)
            else:
                return self._ollama_interpretation(user_prompt, base_measurements, clothing_type)
        except Exception as e:
            self.logger.error(f"Error interpreting design request: {e}")
            return self._get_default_modifications(clothing_type)
    
    def _ollama_interpretation(
        self, 
        user_prompt: str, 
        base_measurements: Dict[str, float], 
        clothing_type: str
    ) -> Dict[str, Any]:
        """Интерпретация запроса через Ollama"""
        
        # Формирование промпта для Ollama
        system_prompt = self._create_system_prompt(base_measurements, clothing_type)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': f"Проанализируй этот запрос на дизайн одежды: '{user_prompt}'"
                    }
                ],
                format='json'
            )
            
            # Парсинг JSON ответа
            modifications_json = response['message']['content']
            modifications = json.loads(modifications_json)
            
            # Валидация и нормализация
            return self._validate_and_normalize_modifications(modifications, clothing_type)
            
        except Exception as e:
            self.logger.error(f"Ollama interpretation failed: {e}")
            return self._fallback_interpretation(user_prompt, clothing_type)
    
    def _create_system_prompt(self, measurements: Dict[str, float], clothing_type: str) -> str:
        """Создание системного промпта для Ollama"""
        
        return f"""
Ты - эксперт по дизайну одежды и конструированию лекал. Проанализируй запрос пользователя и верни JSON с модификациями.

Тип одежды: {clothing_type}
Базовые мерки: {json.dumps(measurements, indent=2)}

Поддерживаемые модификации:
- fit_type: "slim", "fitted", "standard", "loose", "oversize"
- sleeve_type: "none", "short", "three_quarter", "long", "bell", "raglan"
- sleeve_length: "+2.0 cm", "-1.5 cm" (относительно базовой длины)
- neckline_type: "round", "v_neck", "square", "boat", "high", "off_shoulder"
- neckline_depth: "+3.0 cm", "-2.0 cm" (относительно базовой глубины)
- collar_type: "none", "stand", "shirt", "peter_pan", "notch"
- ease_chest: "+5 cm", "-2 cm" (прибавка по груди)
- ease_waist: "+3 cm", "-1 cm" (прибавка по талии)
- ease_hips: "+4 cm", "-2 cm" (прибавка по бедрам)
- length_modification: "+5 cm", "-3 cm" (изменение общей длины)
- dart_modification: "deeper", "shallower", "remove" (модификация вытачек)
- pocket_style: "patch", "welt", "side", "cargo"
- closure_type: "zipper", "buttons", "pullover", "hooks"
- fabric_type: "stretch", "woven", "knit", "denim"
- additional_features: ["pleats", "gusset", "lining"] (дополнительные элементы)
- lapel_type: "notch", "peak", "shawl" (тип лацканов для пиджаков)
- lapel_width: "+1 cm", "wide", "narrow" (ширина лацканов)
- button_stance: "single_breasted", "double_breasted" (положение пуговиц)

Правила:
1. Верни ТОЛЬКО JSON без дополнительного текста
2. Используй только поддерживаемые значения
3. Интерпретируй контекст запроса
4. Учитывай тип одежды при анализе
5. Для пиджаков обращай внимание на лацканы и положение пуговиц
6. "лацканы" → lapel_type: "notch", "острые лацканы" → lapel_type: "peak"
7. "двубортный" → button_stance: "double_breasted", "однобортный" → button_stance: "single_breasted"
8. "широкие лацканы" → lapel_width: "wide", "узкие лацканы" → lapel_width: "narrow"

Примеры:
- "Пиджак приталенный, с лацканами, двубортный" -> {{"fit_type": "slim", "lapel_type": "notch", "button_stance": "double_breasted"}}
- "Пиджак оверсайз, с широкими лацканами, однобортный" -> {{"fit_type": "oversize", "lapel_type": "notch", "lapel_width": "wide", "button_stance": "single_breasted"}}
- "Пиджак с шалевым воротником" -> {{"lapel_type": "shawl", "collar_type": "shawl"}}
"""
    
    def _fallback_interpretation(self, user_prompt: str, clothing_type: str) -> Dict[str, Any]:
        """Fallback интерпретация на основе паттернов"""
        
        modifications = {}
        prompt_lower = user_prompt.lower()
        
        # Отладочный вывод
        self.logger.info(f"Fallback interpretation for clothing_type: {clothing_type} (type: {type(clothing_type)})")
        self.logger.info(f"Prompt: {user_prompt}")
        
        # Анализ типа одежды
        if clothing_type == "skirt" or clothing_type == ClothingType.SKIRT:
            self.logger.info("Processing skirt modifications")
            # Анализ стиля юбки
            for pattern, skirt_style in self.skirt_style_patterns.items():
                if re.search(pattern, prompt_lower):
                    modifications['skirt_style'] = skirt_style
                    self.logger.info(f"Found skirt_style: {skirt_style}")
                    break
            
            # Анализ пояса
            for pattern, waistband_type in self.waistband_patterns.items():
                if re.search(pattern, prompt_lower):
                    modifications['waistband_type'] = waistband_type
                    self.logger.info(f"Found waistband_type: {waistband_type}")
                    break
            
            # Анализ застежки
            for pattern, closure_position in self.closure_patterns.items():
                if re.search(pattern, prompt_lower):
                    modifications['closure_position'] = closure_position
                    self.logger.info(f"Found closure_position: {closure_position}")
                    break
            
            # Анализ карманов
            for pattern, pocket_type in self.pocket_patterns.items():
                if re.search(pattern, prompt_lower):
                    modifications['pocket_type'] = pocket_type
                    self.logger.info(f"Found pocket_type: {pocket_type}")
                    break
            
            # Анализ разреза
            for pattern, slit_type in self.slit_patterns.items():
                if re.search(pattern, prompt_lower):
                    modifications['slit_type'] = slit_type
                    self.logger.info(f"Found slit_type: {slit_type}")
                    break
            
            # Если нет стиля юбки, но есть другие модификации, добавляем стандартный стиль
            if not modifications.get('skirt_style') and any(key in modifications for key in ['waistband_type', 'closure_position', 'pocket_type', 'slit_type']):
                modifications['skirt_style'] = 'straight'
                self.logger.info("Added default skirt_style: straight")
        
        # Анализ типа посадки
        for pattern, fit_type in self.fit_patterns.items():
            if re.search(pattern, prompt_lower):
                modifications['fit_type'] = fit_type.value
                break
        
        # Анализ типа рукавов
        for pattern, sleeve_type in self.sleeve_patterns.items():
            if re.search(pattern, prompt_lower):
                modifications['sleeve_type'] = sleeve_type.value
                break
        
        # Анализ горловины
        for pattern, neckline_type in self.neckline_patterns.items():
            if re.search(pattern, prompt_lower):
                modifications['neckline_type'] = neckline_type.value
                break
        
        # Анализ воротника
        for pattern, collar_type in self.collar_patterns.items():
            if re.search(pattern, prompt_lower):
                modifications['collar_type'] = collar_type.value
                break
        
        # Анализ карманов (только для не-юбок)
        if clothing_type != "skirt" and clothing_type != ClothingType.SKIRT:
            for pattern, pocket_style in self.general_pocket_patterns.items():
                if re.search(pattern, prompt_lower):
                    modifications['pocket_style'] = pocket_style
                    break
        
        # Анализ застежки
        for pattern, closure_type in self.closure_patterns.items():
            if re.search(pattern, prompt_lower):
                modifications['closure_type'] = closure_type
                break
        
        # Анализ лацканов (для пиджаков)
        for pattern, lapel_type in self.lapel_patterns.items():
            if re.search(pattern, prompt_lower):
                modifications['lapel_type'] = lapel_type
                break
        
        # Анализ ширины лацканов
        for pattern, lapel_width in self.lapel_width_patterns.items():
            if re.search(pattern, prompt_lower):
                modifications['lapel_width'] = lapel_width
                break
        
        # Анализ положения пуговиц
        for pattern, button_stance in self.button_stance_patterns.items():
            if re.search(pattern, prompt_lower):
                modifications['button_stance'] = button_stance
                break
        
        # Анализ числовых модификаций
        length_match = re.search(r'(длин|корот).*?(\+|-)?(\d+(?:\.\d+)?)\s*см', prompt_lower)
        if length_match:
            sign = length_match.group(2) or '+'
            value = length_match.group(3)
            modifications['length_modification'] = f"{sign}{value} cm"
        
        # Анализ глубины горловины
        neckline_match = re.search(r'(глубок|мелк).*?(\+|-)?(\d+(?:\.\d+)?)\s*см', prompt_lower)
        if neckline_match:
            sign = neckline_match.group(2) or '+'
            value = neckline_match.group(3)
            modifications['neckline_depth'] = f"{sign}{value} cm"
        
        # Анализ длины рукава
        sleeve_length_match = re.search(r'рукав.*?(\+|-)?(\d+(?:\.\d+)?)\s*см', prompt_lower)
        if sleeve_length_match:
            sign = sleeve_length_match.group(1) or '+'
            value = sleeve_length_match.group(2)
            modifications['sleeve_length'] = f"{sign}{value} cm"
        
        return modifications
    
    def _validate_and_normalize_modifications(
        self, 
        modifications: Dict[str, Any], 
        clothing_type: str
    ) -> Dict[str, Any]:
        """Валидация и нормализация модификаций"""
        
        normalized = {}
        
        # Валидация fit_type
        if 'fit_type' in modifications:
            fit_value = modifications['fit_type']
            if fit_value in [ft.value for ft in FitType]:
                normalized['fit_type'] = fit_value
        
        # Валидация sleeve_type
        if 'sleeve_type' in modifications:
            sleeve_value = modifications['sleeve_type']
            if sleeve_value in [st.value for st in SleeveType]:
                normalized['sleeve_type'] = sleeve_value
        
        # Валидация neckline_type
        if 'neckline_type' in modifications:
            neckline_value = modifications['neckline_type']
            if neckline_value in [nt.value for nt in NecklineType]:
                normalized['neckline_type'] = neckline_value
        
        # Валидация collar_type
        if 'collar_type' in modifications:
            collar_value = modifications['collar_type']
            if collar_value in [ct.value for ct in CollarType]:
                normalized['collar_type'] = collar_value
        
        # Копирование остальных полей
        for key, value in modifications.items():
            if key not in normalized:
                normalized[key] = value
        
        return normalized
    
    def _get_default_modifications(self, clothing_type: str) -> Dict[str, Any]:
        """Получение модификаций по умолчанию"""
        return {
            "fit_type": "standard",
            "clothing_type": clothing_type
        }
    
    def apply_text_modifications(
        self, 
        base_pattern: Dict[str, Any], 
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Применение модификаций к базовому лекалу
        
        Args:
            base_pattern: Базовое лекало
            modifications: Модификации для применения
            
        Returns:
            Модифицированное лекало
        """
        try:
            self.logger.info(f"Starting text modifications application: {list(modifications.keys())}")
            modified_pattern = base_pattern.copy()
            
            # Инициализация истории модификаций
            modification_history = base_pattern.get('modification_history', [])
            
            # Маппинг fit_type в стили StyleEngine
            fit_type_mapping = {
                "slim": "slim",
                "fitted": "slim", 
                "standard": "classic",
                "loose": "oversize",
                "oversize": "oversize"
            }
            
            # Применение типа посадки через StyleEngine
            if 'fit_type' in modifications:
                fit_type = modifications['fit_type']
                style_name = fit_type_mapping.get(fit_type, "Classic")
                
                self.logger.info(f"Applying fit type: {fit_type} -> {style_name}")
                
                try:
                    # Проверяем, есть ли у лекала правильная структура для StyleEngine
                    if 'pieces' in modified_pattern:
                        # Используем StyleEngine для лекал с pieces
                        modified_pattern = self.style_engine.apply_style(
                            modified_pattern, 
                            style_name,
                            modified_pattern.get('garment_type', 'shirt')
                        )
                    else:
                        # Для лекал с прямой структурой (points, lines, curves) применяем модификации напрямую
                        garment_type = modified_pattern.get('garment_type', 'shirt')
                        modified_pattern = self._apply_fit_type_directly(
                            modified_pattern, 
                            style_name,
                            garment_type
                        )
                    
                    # Добавляем в историю
                    modification_history.append({
                        'type': 'fit_type',
                        'value': fit_type,
                        'style_name': style_name,
                        'timestamp': self._get_timestamp()
                    })
                    
                    self.logger.info(f"Fit type {style_name} applied successfully")
                    
                except Exception as e:
                    self.logger.error(f"Error applying style {style_name}: {e}")
                    # Продолжаем с другими модификациями даже если стиль не применился
            
            # Применение модификаций лацканов (для пиджаков)
            if 'lapel_type' in modifications or 'lapel_width' in modifications:
                self.logger.info("Applying lapel modifications...")
                modified_pattern = self._apply_lapel_modifications(
                    modified_pattern, 
                    modifications
                )
                
                # Добавляем в историю с детальным описанием
                if 'lapel_type' in modifications:
                    lapel_changes = modified_pattern.get('lapel_modifications', {}).get('applied_changes', [])
                    modification_history.append({
                        'type': 'lapel_type',
                        'value': modifications['lapel_type'],
                        'details': lapel_changes,
                        'timestamp': self._get_timestamp()
                    })
                
                if 'lapel_width' in modifications:
                    width_changes = modified_pattern.get('lapel_modifications', {}).get('applied_changes', [])
                    modification_history.append({
                        'type': 'lapel_width',
                        'value': modifications['lapel_width'],
                        'details': width_changes,
                        'timestamp': self._get_timestamp()
                    })
            
            # Применение модификаций положения пуговиц
            if 'button_stance' in modifications:
                self.logger.info(f"Applying button stance: {modifications['button_stance']}")
                modified_pattern = self._apply_button_stance_modifications(
                    modified_pattern, 
                    modifications
                )
                
                # Добавляем в историю с детальным описанием
                button_changes = modified_pattern.get('button_stance_modifications', {}).get('applied_changes', [])
                modification_history.append({
                    'type': 'button_stance',
                    'value': modifications['button_stance'],
                    'details': button_changes,
                    'timestamp': self._get_timestamp()
                })
            
            # Применение модификаций юбок
            if 'skirt_style' in modifications or 'waistband_type' in modifications or 'closure_position' in modifications or 'pocket_type' in modifications or 'slit_type' in modifications:
                self.logger.info("Applying skirt modifications...")
                modified_pattern = self._apply_skirt_modifications(
                    modified_pattern, 
                    modifications
                )
                
                # Добавляем в историю
                skirt_changes = modified_pattern.get('skirt_modifications', {}).get('applied_changes', [])
                modification_history.append({
                    'type': 'skirt_modifications',
                    'value': modifications,
                    'details': skirt_changes,
                    'timestamp': self._get_timestamp()
                })
            
            # Добавление метаданных о модификациях
            modified_pattern['text_modifications'] = modifications
            modified_pattern['modification_history'] = modification_history
            
            # Логируем финальную статистику
            points_count = len(modified_pattern.get('points', {}))
            lines_count = len(modified_pattern.get('lines', {}))
            curves_count = len(modified_pattern.get('curves', {}))
            
            self.logger.info(f"Modifications completed. Pattern stats: {points_count} points, {lines_count} lines, {curves_count} curves")
            self.logger.info(f"Total modifications in history: {len(modification_history)}")
            
            return modified_pattern
            
        except Exception as e:
            self.logger.error(f"Error applying modifications: {e}")
            return base_pattern
    
    def _get_timestamp(self) -> str:
        """Получение текущей временной метки"""
        return datetime.now().isoformat()
    
    def _apply_fit_type_directly(
        self, 
        pattern: Dict[str, Any], 
        style_name: str,
        garment_type: str = 'shirt'
    ) -> Dict[str, Any]:
        """Применение типа посадки напрямую к лекалам с прямой структурой"""
        try:
            # Получаем параметры стиля
            style_params = {
                'slim': {'chest': -5.0, 'waist': -3.0, 'shoulder': -1.5, 'length': -1.0},
                'classic': {'chest': 0, 'waist': 0, 'shoulder': 0, 'length': 0},
                'oversize': {'chest': 8.0, 'waist': 6.0, 'shoulder': 2.0, 'length': 2.0}
            }.get(style_name, {'chest': 0, 'waist': 0, 'shoulder': 0, 'length': 0})
            
            points = pattern.get('points', {})
            lines = pattern.get('lines', {})
            curves = pattern.get('curves', {})
            
            # Применяем корректировки к точкам
            for point_name, point_data in points.items():
                x = float(point_data.get('x', 0))
                y = float(point_data.get('y', 0))
                
                # Корректировки в зависимости от типа одежды и положения точки
                if garment_type == 'jacket':
                    # Для пиджаков применяем специфичные корректировки
                    if 'shoulder' in point_name.lower() or any(k in point_name.lower() for k in ['b', 'c', 'o', 'p']):
                        x += style_params['shoulder'] * 0.5  # Плечевые точки
                    elif 'waist' in point_name.lower() or any(k in point_name.lower() for k in ['i', 'j', 'o', 'p']):
                        x += style_params['waist'] * 0.3  # Талиевые точки
                    elif 'chest' in point_name.lower() or any(k in point_name.lower() for k in ['d', 'e', 'g', 'h', 'j', 'k']):
                        x += style_params['chest'] * 0.4  # Грудные точки
                    elif 'hem' in point_name.lower() or any(k in point_name.lower() for k in ['f', 'l', 's', 't', 'y', 'z']):
                        y += style_params['length'] * 0.5  # Нижние точки
                else:
                    # Для других типов одежды
                    if 'shoulder' in point_name.lower():
                        x += style_params['shoulder'] * 0.5
                    elif 'waist' in point_name.lower():
                        x += style_params['waist'] * 0.3
                    elif 'chest' in point_name.lower():
                        x += style_params['chest'] * 0.4
                    elif 'hem' in point_name.lower():
                        y += style_params['length'] * 0.5
                
                # Обновляем координаты
                point_data['x'] = x
                point_data['y'] = y
            
            # Обновляем лекало
            pattern['points'] = points
            pattern['fit_type_applied'] = style_name
            
            self.logger.info(f"Direct fit type application completed: {style_name}")
            return pattern
            
        except Exception as e:
            self.logger.error(f"Error in direct fit type application: {e}")
            return pattern
    
    def _apply_skirt_modifications(
        self, 
        pattern: Dict[str, Any], 
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Применение модификаций юбок с реальным изменением геометрии"""
        try:
            skirt_style = modifications.get('skirt_style')
            waistband_type = modifications.get('waistband_type')
            closure_position = modifications.get('closure_position')
            pocket_type = modifications.get('pocket_type')
            slit_type = modifications.get('slit_type')
            
            points = pattern.get('points', {})
            lines = pattern.get('lines', {})
            modification_details = []
            
            # Применение стиля юбки
            if skirt_style:
                if skirt_style == 'pencil':
                    # Карандашная юбка - уменьшаем низ
                    for point_name, point_data in points.items():
                        if 'hem' in point_name.lower() and 'y' in point_data:
                            point_data['y'] -= 2.0  # укорачиваем низ
                            modification_details.append(f"{point_name}: y -2.0 см (карандаш)")
                
                elif skirt_style == 'flare':
                    # Клёш - расширяем низ
                    for point_name, point_data in points.items():
                        if 'hem' in point_name.lower() and 'x' in point_data:
                            point_data['x'] *= 1.3  # расширяем на 30%
                            modification_details.append(f"{point_name}: x *1.3 (клёш)")
                
                elif skirt_style == 'a_line':
                    # А-силуэт - плавное расширение к низу
                    for point_name, point_data in points.items():
                        if 'hem' in point_name.lower() and 'x' in point_data:
                            # Плавное расширение от бедер к низу
                            hem_x = point_data.get('x', 0)
                            hem_y = point_data.get('y', 0)
                            hip_y = 0  # Инициализируем hip_y
                            
                            # Ищем точку бедер с тем же X
                            for hip_point_name, hip_point_data in points.items():
                                if 'hip' in hip_point_name.lower() and abs(hip_point_data['x'] - hem_x) < 1.0:
                                    hip_y = hip_point_data['y']
                                    break
                            
                            if hip_y != 0:
                                # Расчет расширения
                                expansion = (hem_y - hip_y) * 0.5
                                point_data['x'] += expansion
                                modification_details.append(f"{point_name}: x +{expansion:.1f} см (А-силуэт)")
            
            # Применение типа пояса
            if waistband_type:
                if waistband_type == 'wide':
                    # Широкий пояс - увеличиваем талию
                    for point_name, point_data in points.items():
                        if 'waist' in point_name.lower() and 'x' in point_data:
                            point_data['y'] -= 0.5  # опускаем пояс
                            modification_details.append(f"{point_name}: y -0.5 см (широкий пояс)")
                
                elif waistband_type == 'elastic':
                    # Эластичный пояс - добавляем эластичность
                    for point_name, point_data in points.items():
                        if 'waist' in point_name.lower():
                            point_data['elastic'] = True
                            modification_details.append(f"{point_name}: добавлена эластичность")
            
            # Применение застежки
            if closure_position:
                if closure_position == 'side_zip':
                    # Боковая молния - добавляем разрез для молнии
                    for point_name, point_data in points.items():
                        if 'side' in point_name.lower() and 'y' in point_data:
                            if point_data['y'] > 20:  # Разрез только в нижней части
                                point_data['slit'] = True
                                modification_details.append(f"{point_name}: добавлен боковой разрез")
                
                elif closure_position == 'back_zip':
                    # Задняя молния - добавляем разрез в центре спинки
                    for point_name, point_data in points.items():
                        if 'center' in point_name.lower() and 'y' in point_data:
                            point_data['back_zip'] = True
                            modification_details.append(f"{point_name}: добавлена задняя молния")
            
            # Применение карманов
            if pocket_type == 'inseam':
                # Боковые карманы в швах
                for point_name, point_data in points.items():
                    if 'side' in point_name.lower() and 'y' in point_data:
                        if 20 < point_data['y'] < 40:  # Карман на уровне бедер
                            point_data['pocket'] = True
                            point_data['pocket_y'] = point_data['y'] - 2.0  # Глубина кармана
                            modification_details.append(f"{point_name}: добавлен боковой карман")
            
            elif pocket_type == 'patch':
                # Накладные карманы
                for point_name, point_data in points.items():
                    if 'hem' in point_name.lower() and 'x' in point_data:
                        # Добавляем карман на уровне бедер
                        point_data['patch_pocket'] = True
                        point_data['pocket_y'] = point_data['y'] - 1.0
                        modification_details.append(f"{point_name}: добавлен накладной карман")
            
            # Применение разреза
            if slit_type:
                if slit_type == 'front':
                    # Передний разрез
                    for point_name, point_data in points.items():
                        if 'center' in point_name.lower() and 'y' in point_data:
                            if point_data['y'] > 30:  # Разрез только в нижней части
                                point_data['front_slit'] = True
                                modification_details.append(f"{point_name}: добавлен передний разрез")
                
                elif slit_type == 'back':
                    # Задний разрез
                    for point_name, point_data in points.items():
                        if 'center' in point_name.lower() and 'y' in point_data:
                            point_data['back_slit'] = True
                            modification_details.append(f"{point_name}: добавлен задний разрез")
                
                elif slit_type == 'side':
                    # Боковой разрез
                    for point_name, point_data in points.items():
                        if 'side' in point_name.lower() and 'y' in point_data:
                            point_data['side_slit'] = True
                            modification_details.append(f"{point_name}: добавлен боковой разрез")
            
            # Добавляем метки для молний и карманов
            if closure_position in ['side_zip', 'back_zip'] or pocket_type in ['inseam', 'patch']:
                self._add_closure_and_pocket_marks(points, modifications)
            
            # Обновляем лекало
            pattern['points'] = points
            pattern['lines'] = lines
            pattern['skirt_modifications'] = {
                'applied_changes': modification_details
            }
            
            # Детальное логирование
            changes_str = ", ".join(modification_details) if modification_details else "нет изменений"
            self.logger.info(f"Применён skirt_style: {skirt_style} — {changes_str}")
            
            return pattern
            
        except Exception as e:
            self.logger.error(f"Error applying skirt modifications: {e}")
            return pattern
    
    def _add_closure_and_pocket_marks(self, points: Dict[str, Any], modifications: Dict[str, Any]):
        """Добавление меток для молний и карманов"""
        closure_position = modifications.get('closure_position')
        pocket_type = modifications.get('pocket_type')
        
        # Поиск центральной линии талии
        waist_center = None
        for point_name, point_data in points.items():
            if 'waist_center' in point_name.lower():
                waist_center = point_data
                break
        
        if waist_center:
            # Метки для молнии
            if closure_position == 'side_zip':
                # Боковая молния
                points['zipper_start'] = {
                    'x': waist_center['x'] - 2.0,
                    'y': waist_center['y'] + 2.0,
                    'type': 'construction'
                }
                points['zipper_end'] = {
                    'x': waist_center['x'] - 2.0,
                    'y': waist_center['y'] + 8.0,
                    'type': 'construction'
                }
            
            elif closure_position == 'back_zip':
                # Задняя молния
                points['zipper_start'] = {
                    'x': waist_center['x'],
                    'y': waist_center['y'] + 2.0,
                    'type': 'construction'
                }
                points['zipper_end'] = {
                    'x': waist_center['x'],
                    'y': waist_center['y'] + 8.0,
                    'type': 'construction'
                }
            
            # Метки для карманов
            if pocket_type == 'inseam':
                # Боковые карманы в швах
                for point_name, point_data in points.items():
                    if 'hip' in point_name.lower() and 20 < point_data['y'] < 40:
                        point_data['pocket_mark'] = {
                            'x': point_data['x'] - 1.0,
                            'y': point_data['y'] - 2.0,
                            'type': 'construction'
                        }
            
            elif pocket_type == 'patch':
                # Накладные карманы
                for point_name, point_data in points.items():
                    if 'hem' in point_name.lower():
                        point_data['patch_pocket_mark'] = {
                            'x': point_data['x'],
                            'y': point_data['y'] - 1.0,
                            'type': 'construction'
                        }
    
    def _apply_lapel_modifications(
        self, 
        pattern: Dict[str, Any], 
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Применение модификаций лацканов с реальным изменением геометрии"""
        try:
            lapel_type = modifications.get('lapel_type')
            lapel_width = modifications.get('lapel_width')
            
            if not lapel_type and not lapel_width:
                return pattern
            
            points = pattern.get('points', {})
            curves = pattern.get('curves', {})
            modification_details = []
            
            # Ищем ключевые точки для лацканов по именам из pattern_maker.py
            lapel_points = {}
            for point_name, point_data in points.items():
                if any(key in point_name.lower() for key in ['lapel_start_left', 'lapel_start_right', 'lapel_end_left', 'lapel_end_right']):
                    lapel_points[point_name] = point_data
            
            if not lapel_points:
                self.logger.warning("No lapel points found in pattern")
                return pattern
            
            # Применяем модификации типа лацканов
            if lapel_type:
                if lapel_type == 'notch':
                    # Лацканы с вырезом - изменяем точки начала лацканов
                    if 'lapel_start_left' in lapel_points:
                        lapel_points['lapel_start_left']['x'] += 1.0  # смещаем внутрь
                        modification_details.append("lapel_start_left: x +1.0 см")
                    if 'lapel_start_right' in lapel_points:
                        lapel_points['lapel_start_right']['x'] -= 1.0  # смещаем внутрь
                        modification_details.append("lapel_start_right: x -1.0 см")
                    
                    # Обновляем кривые лацканов для notch
                    if 'lapel_left' in curves:
                        curves['lapel_left']['control1']['x'] += 0.5
                        curves['lapel_left']['control2']['x'] += 0.5
                        modification_details.append("lapel_left curve: control points adjusted")
                    if 'lapel_right' in curves:
                        curves['lapel_right']['control1']['x'] -= 0.5
                        curves['lapel_right']['control2']['x'] -= 0.5
                        modification_details.append("lapel_right curve: control points adjusted")
                
                elif lapel_type == 'peak':
                    # Острые лацканы - изменяем точки конца лацканов
                    if 'lapel_end_left' in lapel_points:
                        lapel_points['lapel_end_left']['x'] += 0.8  # расширяем
                        lapel_points['lapel_end_left']['y'] -= 0.3  # поднимаем для остроты
                        modification_details.append("lapel_end_left: x +0.8 см, y -0.3 см")
                    if 'lapel_end_right' in lapel_points:
                        lapel_points['lapel_end_right']['x'] -= 0.8  # расширяем
                        lapel_points['lapel_end_right']['y'] -= 0.3  # поднимаем для остроты
                        modification_details.append("lapel_end_right: x -0.8 см, y -0.3 см")
                    
                    # Обновляем кривые для более острой формы
                    if 'lapel_left' in curves:
                        curves['lapel_left']['control1']['y'] -= 0.5
                        curves['lapel_left']['control2']['y'] -= 0.5
                        modification_details.append("lapel_left curve: sharper angle")
                    if 'lapel_right' in curves:
                        curves['lapel_right']['control1']['y'] -= 0.5
                        curves['lapel_right']['control2']['y'] -= 0.5
                        modification_details.append("lapel_right curve: sharper angle")
                
                elif lapel_type == 'shawl':
                    # Шалевый лацканы - создаем плавную кривую от горловины к борту
                    if 'lapel_start_left' in lapel_points and 'lapel_end_left' in lapel_points:
                        # Создаем новую кривую Безье для шалевого лацкана
                        start_point = lapel_points['lapel_start_left']
                        end_point = lapel_points['lapel_end_left']
                        
                        # Контрольные точки для плавной кривой
                        control1 = {
                            'x': start_point['x'] - 2.0,
                            'y': start_point['y'] + 3.0
                        }
                        control2 = {
                            'x': end_point['x'] - 1.0,
                            'y': end_point['y'] + 2.0
                        }
                        
                        curves['shawl_lapel_left'] = {
                            'start': {'x': start_point['x'], 'y': start_point['y']},
                            'control1': control1,
                            'control2': control2,
                            'end': {'x': end_point['x'], 'y': end_point['y']},
                            'type': 'bezier'
                        }
                        modification_details.append("shawl_lapel_left: bezier curve added")
                    
                    if 'lapel_start_right' in lapel_points and 'lapel_end_right' in lapel_points:
                        # Аналогично для правой стороны
                        start_point = lapel_points['lapel_start_right']
                        end_point = lapel_points['lapel_end_right']
                        
                        control1 = {
                            'x': start_point['x'] + 2.0,
                            'y': start_point['y'] + 3.0
                        }
                        control2 = {
                            'x': end_point['x'] + 1.0,
                            'y': end_point['y'] + 2.0
                        }
                        
                        curves['shawl_lapel_right'] = {
                            'start': {'x': start_point['x'], 'y': start_point['y']},
                            'control1': control1,
                            'control2': control2,
                            'end': {'x': end_point['x'], 'y': end_point['y']},
                            'type': 'bezier'
                        }
                        modification_details.append("shawl_lapel_right: bezier curve added")
            
            # Применяем ширину лацканов
            if lapel_width:
                width_multiplier = 1.0
                width_description = ""
                
                if lapel_width == 'wide':
                    width_multiplier = 1.3
                    width_description = "широкие (+30%)"
                elif lapel_width == 'narrow':
                    width_multiplier = 0.7
                    width_description = "узкие (-30%)"
                elif '+' in lapel_width or '-' in lapel_width:
                    # Парсим числовое значение
                    width_match = re.search(r'([+-]?\d+(?:\.\d+)?)', lapel_width)
                    if width_match:
                        width_change = float(width_match.group(1))
                        width_multiplier = 1.0 + (width_change / 10.0)  # 1 см = 10% изменения
                        width_description = f"изменение на {width_change} см"
                
                # Применяем масштабирование к точкам лацканов
                for point_name, point_data in lapel_points.items():
                    if 'x' in point_data:
                        original_x = point_data['x']
                        point_data['x'] *= width_multiplier
                        modification_details.append(f"{point_name}: x {original_x} → {point_data['x']:.1f} ({width_description})")
            
            # Обновляем лекало
            pattern['points'] = points
            pattern['curves'] = curves
            
            # Добавляем метаданные о лацканах
            pattern['lapel_modifications'] = {
                'type': lapel_type,
                'width': lapel_width,
                'applied_changes': modification_details
            }
            
            # Детальное логирование
            changes_str = ", ".join(modification_details) if modification_details else "нет изменений"
            self.logger.info(f"Применён lapel_type: {lapel_type} — изменены точки: {changes_str}")
            
        except Exception as e:
            self.logger.error(f"Error applying lapel modifications: {e}")
        
        return pattern
    
    def _apply_button_stance_modifications(
        self, 
        pattern: Dict[str, Any], 
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Применение модификаций положения пуговиц с реальным изменением геометрии"""
        try:
            button_stance = modifications.get('button_stance')
            
            if not button_stance:
                return pattern
            
            points = pattern.get('points', {})
            lines = pattern.get('lines', {})
            modification_details = []
            
            # Определяем, является ли это передняя часть пиджака
            is_front_pattern = pattern.get('pattern_half') == 'front' or 'front' in str(pattern.get('pattern_type', '')).lower()
            
            if not is_front_pattern:
                self.logger.warning("Button stance modifications only apply to front patterns")
                return pattern
            
            # Собираем все точки передней части
            front_points = []
            for point_name, point_data in points.items():
                # Исключаем точки лацканов из смещения при двубортном крое
                is_lapel_point = any(key in point_name.lower() for key in ['lapel'])
                if not is_lapel_point:
                    front_points.append(point_name)
            
            if button_stance == 'double_breasted':
                # Двубортный пиджак - смещаем центральную линию переда
                shift_amount = 2.0  # см
                
                for point_name in front_points:
                    if point_name in points and 'x' in points[point_name]:
                        original_x = points[point_name]['x']
                        points[point_name]['x'] += shift_amount
                        modification_details.append(f"{point_name}: x {original_x} → {points[point_name]['x']:.1f} (+{shift_amount} см)")
                
                # Обновляем линии, которые зависят от смещенных точек
                for line_name, line_data in lines.items():
                    if 'start' in line_data:
                        # Ищем точку по координатам
                        start_coords = line_data['start']
                        for pn in front_points:
                            if (abs(start_coords['x'] - points[pn]['x']) < 0.1 and 
                                abs(start_coords['y'] - points[pn]['y']) < 0.1):
                                line_data['start']['x'] = points[pn]['x']
                                break
                    
                    if 'end' in line_data:
                        # Ищем точку по координатам
                        end_coords = line_data['end']
                        for pn in front_points:
                            if (abs(end_coords['x'] - points[pn]['x']) < 0.1 and 
                                abs(end_coords['y'] - points[pn]['y']) < 0.1):
                                line_data['end']['x'] = points[pn]['x']
                                break
                
                # Добавляем метки пуговиц для двубортного кроя
                button_marks = self._create_double_breasted_button_marks(points)
                pattern['button_marks'] = button_marks
                modification_details.append(f"добавлены метки {len(button_marks)} пуговиц")
                
                # Метаданные о двубортном крое
                pattern['button_stance'] = {
                    'type': 'double_breasted',
                    'button_rows': 2,
                    'row_spacing': 3.0,  # см между рядами
                    'front_shift': shift_amount,
                    'button_count': len(button_marks)
                }
                
            elif button_stance == 'single_breasted':
                # Однобортный пиджак - стандартное положение
                button_marks = self._create_single_breasted_button_marks(points)
                pattern['button_marks'] = button_marks
                modification_details.append(f"добавлены метки {len(button_marks)} пуговиц")
                
                # Метаданные об однобортном крое
                pattern['button_stance'] = {
                    'type': 'single_breasted',
                    'button_rows': 1,
                    'button_count': len(button_marks),
                    'front_shift': 0.0
                }
            
            # Обновляем лекало
            pattern['points'] = points
            pattern['lines'] = lines
            
            # Добавляем метаданные об изменениях
            pattern['button_stance_modifications'] = {
                'type': button_stance,
                'applied_changes': modification_details
            }
            
            # Детальное логирование
            changes_str = ", ".join(modification_details) if modification_details else "нет изменений"
            self.logger.info(f"Применён button_stance: {button_stance} — {changes_str}")
            
        except Exception as e:
            self.logger.error(f"Error applying button stance modifications: {e}")
        
        return pattern
    
    def _create_double_breasted_button_marks(self, points: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Создание меток пуговиц для двубортного пиджака"""
        button_marks = []
        
        # Ищем центральную линию переда и линию талии
        center_front = None
        waist_line_y = None
        
        for point_name, point_data in points.items():
            if 'center_front' in point_name.lower() or 'g' in point_name.lower():
                center_front = point_data
            elif 'waist' in point_name.lower() or any(k in point_name.lower() for k in ['o', 'p']):
                waist_line_y = point_data['y']
        
        if center_front and waist_line_y is not None:
            # Первый ряд пуговиц (основной)
            button_spacing = 8.0  # см между пуговицами
            start_y = waist_line_y - 10.0  # Начинаем выше талии
            
            for i in range(4):  # 4 пуговицы в основном ряду
                button_y = start_y + (i * button_spacing)
                button_marks.append({
                    'x': center_front['x'],
                    'y': button_y,
                    'row': 'main',
                    'diameter': 1.5  # см
                })
            
            # Второй ряд пуговиц (внутренний)
            inner_x = center_front['x'] - 3.0  # смещаем внутрь
            
            for i in range(3):  # 3 пуговицы во внутреннем ряду
                button_y = start_y + 5.0 + (i * button_spacing)
                button_marks.append({
                    'x': inner_x,
                    'y': button_y,
                    'row': 'inner',
                    'diameter': 1.2  # см
                })
        
        return button_marks
    
    def _create_single_breasted_button_marks(self, points: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Создание меток пуговиц для однобортного пиджака"""
        button_marks = []
        
        # Ищем центральную линию переда и линию талии
        center_front = None
        waist_line_y = None
        
        for point_name, point_data in points.items():
            if 'center_front' in point_name.lower() or 'g' in point_name.lower():
                center_front = point_data
            elif 'waist' in point_name.lower() or any(k in point_name.lower() for k in ['o', 'p']):
                waist_line_y = point_data['y']
        
        if center_front and waist_line_y is not None:
            # Однорядные пуговицы
            button_spacing = 10.0  # см между пуговицами
            start_y = waist_line_y - 5.0  # Начинаем у талии
            
            for i in range(3):  # 3 пуговицы
                button_y = start_y + (i * button_spacing)
                button_marks.append({
                    'x': center_front['x'],
                    'y': button_y,
                    'row': 'main',
                    'diameter': 1.5  # см
                })
        
        return button_marks


# Удобные функции для быстрого доступа
def interpret_design_request(
    user_prompt: str, 
    base_measurements: Dict[str, float], 
    clothing_type: str,
    model_name: str = "llama3.2"
) -> Dict[str, Any]:
    """
    Удобная функция для интерпретации текстового запроса
    
    Args:
        user_prompt: Текстовый запрос пользователя
        base_measurements: Базовые мерки
        clothing_type: Тип одежды
        model_name: Название модели Ollama
        
    Returns:
        Словарь с модификациями лекала
    """
    interface = TextDesignInterface(model_name)
    return interface.interpret_design_request(user_prompt, base_measurements, clothing_type)


def apply_text_modifications(
    base_pattern: Dict[str, Any], 
    modifications: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Удобная функция для применения модификаций к лекалу
    
    Args:
        base_pattern: Базовое лекало
        modifications: Модификации для применения
        
    Returns:
        Модифицированное лекало
    """
    interface = TextDesignInterface()
    return interface.apply_text_modifications(base_pattern, modifications)
