"""
Fashion Designer Module

Класс для создания дизайна одежды, генерации идей и управления проектами.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from datetime import datetime


class GarmentType(Enum):
    """Типы одежды"""
    DRESS = "dress"
    SHIRT = "shirt"
    PANTS = "pants"
    SKIRT = "skirt"
    JACKET = "jacket"
    COAT = "coat"
    BLOUSE = "blouse"
    TSHIRT = "tshirt"


class DesignStyle(Enum):
    """Стили дизайна"""
    CASUAL = "casual"
    FORMAL = "formal"
    SPORT = "sport"
    EVENING = "evening"
    BUSINESS = "business"
    VINTAGE = "vintage"
    MODERN = "modern"


@dataclass
class Material:
    """Материал для одежды"""
    name: str
    composition: str  # Состав
    weight: float  # г/м²
    stretch: bool  # Эластичность
    care_instructions: str


@dataclass
class Color:
    """Цветовая схема"""
    primary: str
    secondary: Optional[str] = None
    accent: Optional[str] = None
    pattern: Optional[str] = None


@dataclass
class Measurement:
    """Мерки"""
    bust: float
    waist: float
    hips: float
    height: float
    shoulder_width: Optional[float] = None
    sleeve_length: Optional[float] = None
    inseam: Optional[float] = None


class FashionDesigner:
    """Основной класс дизайнера одежды"""
    
    def __init__(self):
        self.designs = {}  # Хранилище дизайнов
        self.materials_db = self._init_materials_db()
        self.color_palettes = self._init_color_palettes()
        
    def _init_materials_db(self) -> Dict[str, Material]:
        """Инициализация базы материалов"""
        return {
            "cotton": Material(
                name="Хлопок",
                composition="100% хлопок",
                weight=150.0,
                stretch=False,
                care_instructions="Машинная стирка 30°C"
            ),
            "denim": Material(
                name="Джинса",
                composition="98% хлопок, 2% эластан",
                weight=280.0,
                stretch=True,
                care_instructions="Машинная стирка 40°C"
            ),
            "silk": Material(
                name="Шелк",
                composition="100% шелк",
                weight=80.0,
                stretch=False,
                care_instructions="Ручная стирка"
            ),
            "wool": Material(
                name="Шерсть",
                composition="100% шерсть",
                weight=200.0,
                stretch=False,
                care_instructions="Сухая чистка"
            ),
            "polyester": Material(
                name="Полиэстер",
                composition="100% полиэстер",
                weight=120.0,
                stretch=False,
                care_instructions="Машинная стирка 40°C"
            )
        }
    
    def _init_color_palettes(self) -> Dict[str, List[Color]]:
        """Инициализация цветовых палитр"""
        return {
            "spring": [
                Color("#FF6B6B", "#FFE66D", "#4ECDC4"),
                Color("#95E1D3", "#F38181", "#AA96DA")
            ],
            "summer": [
                Color("#87CEEB", "#98FB98", "#DDA0DD"),
                Color("#F0E68C", "#ADD8E6", "#F08080")
            ],
            "autumn": [
                Color("#D2691E", "#FF8C00", "#8B4513"),
                Color("#CD853F", "#DAA520", "#B22222")
            ],
            "winter": [
                Color("#191970", "#000080", "#4169E1"),
                Color("#6495ED", "#00CED1", "#4682B4")
            ]
        }
    
    def generate_design_description(self, 
                                garment_type: GarmentType, 
                                style: DesignStyle,
                                additional_requirements: str = "") -> str:
        """
        Генерирует текстовое описание конструкции одежды.
        
        Этап "дизайн → лекала" в процессе создания одежды:
        1. **Концептуальный дизайн** - определение силуэта, стиля, назначения
        2. **Техническое описание** - детализация конструктивных элементов
        3. **Конструкторская подготовка** - перевод дизайна в технические спецификации
        4. **Создание лекал** - построение геометрических основ для пошива
        
        Эта функция выполняет этапы 1-2, создавая подробное текстовое описание,
        которое затем используется для автоматического построения лекал.
        
        Args:
            garment_type: Тип одежды (dress, shirt, pants, skirt, jacket, coat, blouse, tshirt)
            style: Стиль (casual, formal, sport, evening, business, vintage, modern)
            additional_requirements: Дополнительные требования от пользователя
            
        Returns:
            Подробное текстовое описание конструкции одежды
        """
        # База знаний по конструкциям для разных типов одежды
        construction_base = {
            GarmentType.DRESS: {
                "silhouette": "приталенный, полуприлегающий или свободный",
                "parts": ["лиф", "юбка", "рукава", "воротник"],
                "closures": ["молния", "пуговицы", "кнопки"],
                "details": ["вытачки", "рельефы", "кокетки", "подрезы"]
            },
            GarmentType.SHIRT: {
                "silhouette": "прямой или слегка приталенный",
                "parts": ["полочка", "спинка", "рукава", "воротник", "манжеты"],
                "closures": ["пуговицы", "застежка"],
                "details": ["кокетка", "вытачки", "пат", "манжеты"]
            },
            GarmentType.PANTS: {
                "silhouette": "прямые, зауженные или расклешенные",
                "parts": ["передняя половинка", "задняя половинка", "пояс"],
                "closures": ["молния", "пуговицы", "резинка"],
                "details": ["шлевки", "карманы", "стрелки", "вытачки"]
            },
            GarmentType.SKIRT: {
                "silhouette": "прямая, расклешенная, годе или плиссированная",
                "parts": ["переднее полотнище", "заднее полотнище", "пояс"],
                "closures": ["молния", "пуговицы", "резинка"],
                "details": ["складки", "вытачки", "кокетки", "карманы"]
            },
            GarmentType.JACKET: {
                "silhouette": "приталенный или полуприлегающий",
                "parts": ["полочка", "спинка", "рукава", "воротник", "подкладка"],
                "closures": ["молния", "пуговицы", "крючки"],
                "details": ["пат", "карманы", "втачные рукава", "подборт"]
            },
            GarmentType.COAT: {
                "silhouette": "прямой или трапециевидный",
                "parts": ["полочка", "спинка", "рукава", "воротник", "подкладка"],
                "closures": ["молния", "пуговицы", "крючки"],
                "details": ["пат", "карманы", "втачные рукава", "манжеты"]
            },
            GarmentType.BLOUSE: {
                "silhouette": "полуприлегающий или свободный",
                "parts": ["полочка", "спинка", "рукава", "воротник"],
                "closures": ["пуговицы", "кнопки", "завязки"],
                "details": ["кокетка", "рюши", "воланы", "сборки"]
            },
            GarmentType.TSHIRT: {
                "silhouette": "прямой или слегка приталенный",
                "parts": ["полочка", "спинка", "рукава"],
                "closures": ["без застежки", "резинка"],
                "details": ["круглая горловина", "V-образная горловина", "манжеты"]
            }
        }
        
        # Стилевые характеристики
        style_characteristics = {
            DesignStyle.CASUAL: {
                "fit": "свободный или полуприлегающий",
                "details": "минималистичные детали, практичные карманы",
                "materials": "хлопок, джинса, трикотаж",
                "construction": "упрощенная конструкция, комфорт"
            },
            DesignStyle.FORMAL: {
                "fit": "приталенный, строгий силуэт",
                "details": "высококачественная фурнитура, точные линии",
                "materials": "шерсть, шелк, вискоза",
                "construction": "сложная конструкция, идеальные пропорции"
            },
            DesignStyle.SPORT: {
                "fit": "свободный или облегающий",
                "details": "эластичные вставки, функциональные карманы",
                "materials": "спортивные ткани, эластан, мембраны",
                "construction": "анатомический крой, технологичные швы"
            },
            DesignStyle.EVENING: {
                "fit": "приталенный, драматичный силуэт",
                "details": "роскошная отделка, вышивка, стразы",
                "materials": "шелк, бархат, органза",
                "construction": "сложная драпировка, многослойность"
            },
            DesignStyle.BUSINESS: {
                "fit": "строгий, умеренно приталенный",
                "details": "сдержанная отделка, функциональные детали",
                "materials": "шерсть, хлопок, вискоза",
                "construction": "классическая конструкция, деловой стиль"
            },
            DesignStyle.VINTAGE: {
                "fit": "ретро силуэт, часто приталенный",
                "details": "классическая фурнитура, ретро элементы",
                "materials": "натуральные ткани традиционных фактур",
                "construction": "традиционные методы конструирования"
            },
            DesignStyle.MODERN: {
                "fit": "асимметричный или минималистичный",
                "details": "геометрические элементы, нестандартные решения",
                "materials": "инновационные ткани, технологичные материалы",
                "construction": "авангардная конструкция, экспериментальный крой"
            }
        }
        
        # Получение базовой информации
        base_info = construction_base.get(garment_type, construction_base[GarmentType.DRESS])
        style_info = style_characteristics.get(style, style_characteristics[DesignStyle.CASUAL])
        
        # Формирование промпта для Ollama
        prompt = f"""
Создай детальное техническое описание конструкции {garment_type.value} в стиле {style.value}.

Исходные данные:
- Тип одежды: {garment_type.value}
- Стиль: {style.value}
- Силуэт: {base_info['silhouette']}
- Основные части: {', '.join(base_info['parts'])}
- Застежки: {', '.join(base_info['closures'])}
- Конструктивные детали: {', '.join(base_info['details'])}
- Характеристики стиля: {style_info['fit']}
- Материалы: {style_info['materials']}
- Особенности конструкции: {style_info['construction']}

Дополнительные требования: {additional_requirements}

Создай подробное описание конструкции, включающее:
1. Общий силуэт и посадку
2. Детальное описание каждой части изделия
3. Конструктивные особенности и детали
4. Рекомендации по материалам и фурнитуре
5. Технологические особенности пошива

Описание должно быть технически точным и подходить для последующего построения лекал.
"""
        
        # Попытка использовать Ollama через UniversalAgent
        try:
            # Импортируем здесь, чтобы избежать циклических зависимостей
            from ..core import UniversalAgent
            
            # Создаем временный агент для доступа к Ollama
            temp_agent = UniversalAgent()
            response = temp_agent.ask_ollama(prompt)
            
            # Проверяем тип ответа
            if isinstance(response, dict):
                # Если вернулся dict, пытаемся получить текст
                response_text = response.get('response', '') or response.get('text', '')
            else:
                response_text = str(response)
            
            if response_text and response_text.strip():
                return response_text.strip()
                
        except Exception as e:
            # Если Ollama недоступен, используем базовый шаблон
            print(f"Ollama unavailable, using template: {e}")
        
        # Базовый шаблон описания
        description = f"""
ТЕХНИЧЕСКОЕ ОПИСАНИЕ КОНСТРУКЦИИ

Изделие: {garment_type.value.title()}
Стиль: {style.value}
Силуэт: {base_info['silhouette']}

1. ОБЩАЯ ХАРАКТЕРИСТИКА
Посадка: {style_info['fit']}
Конструкция: {style_info['construction']}
Рекомендуемые материалы: {style_info['materials']}

2. ОСНОВНЫЕ ЧАСТИ ИЗДЕЛИЯ
"""
        
        # Добавление описания каждой части
        for part in base_info['parts']:
            description += f"\n- {part.title()}: "
            
            if garment_type == GarmentType.DRESS:
                if "лиф" in part.lower():
                    description += "приталенный лиф с вытачками, круглой горловиной"
                elif "юбка" in part.lower():
                    description += "прямая юбка длиной до колена, со шлицей сзади"
                elif "рукав" in part.lower():
                    description += "длинные втачные рукава, зауженные к низу"
                elif "воротник" in part.lower():
                    description += "круглая горловина с обтачкой"
                    
            elif garment_type == GarmentType.SHIRT:
                if "полочка" in part.lower():
                    description += "полочка с планкой для пуговиц, нагрудной вытачкой"
                elif "спинка" in part.lower():
                    description += "спинка со швом посередине, вытачками"
                elif "рукав" in part.lower():
                    description += "длинные рукава с манжетами на пуговицах"
                elif "воротник" in part.lower():
                    description += "отложной воротник с стойкой"
                elif "манжет" in part.lower():
                    description += "манжеты с обтачкой и пуговицами"
                    
            elif garment_type == GarmentType.PANTS:
                if "передняя" in part.lower():
                    description += "передняя половинка с вытачками, застежкой-молнией"
                elif "задняя" in part.lower():
                    description += "задняя половинка с вытачками, шлицей"
                elif "пояс" in part.lower():
                    description += "пояс с шлевками и loops для ремня"
                    
            else:
                description += f"конструктивная деталь с учетом стиля {style.value}"
        
        description += f"""

3. КОНСТРУКТИВНЫЕ ДЕТАЛИ
"""
        
        for detail in base_info['details']:
            description += f"\n- {detail.title()}: расположены с учетом эргономики и стиля"
        
        description += f"""

4. ЗАСТЕЖКИ И ФУРНИТУРА
"""
        
        for closure in base_info['closures']:
            description += f"\n- {closure.title()}: функциональная и декоративная"
        
        description += f"""

5. ТЕХНОЛОГИЧЕСКИЕ ОСОБЕННОСТИ
- Швы: обработка оверлоком, закрытые швы в видимых местах
- Припуски: 1.5 см на основных швах, 3 см на подоле
- Дополнительно: {additional_requirements if additional_requirements else 'стандартная технология пошива'}

Описание подготовлено для автоматического построения лекал.
"""
        
        return description.strip()
    
    def create_design(self, 
                     garment_type: GarmentType,
                     style: DesignStyle,
                     measurements: Dict[str, float] = None,
                     measurement_obj: Measurement = None,
                     description: str = "",
                     season: str = "all") -> str:
        """
        Создать новый дизайн
        
        Args:
            garment_type: Тип одежды
            style: Стиль дизайна
            measurements: Словарь с мерками
            measurement_obj: Объект Measurement
            description: Описание дизайна
            season: Сезон
            
        Returns:
            ID созданного дизайна
        """
        design_id = str(uuid.uuid4())
        
        # Конвертация мерок
        if measurement_obj is None and measurements:
            measurement_obj = Measurement(
                bust=measurements.get('bust', 0),
                waist=measurements.get('waist', 0),
                hips=measurements.get('hips', 0),
                height=measurements.get('height', 0),
                shoulder_width=measurements.get('shoulder_width'),
                sleeve_length=measurements.get('sleeve_length'),
                inseam=measurements.get('inseam')
            )
        elif measurement_obj is None:
            measurement_obj = Measurement(0, 0, 0, 0)  # Default
        
        # Выбор материалов
        materials = self._select_materials(garment_type, season)
        
        # Выбор цветовой схемы
        colors = self._select_colors(style, season)
        
        # Генерация спецификации
        specification = self._generate_specification(
            garment_type, style, measurement_obj, materials, colors
        )
        
        design = {
            "id": design_id,
            "type": garment_type.value,
            "style": style.value,
            "description": description,
            "season": season,
            "measurements": measurement_obj.__dict__,
            "materials": [m.__dict__ for m in materials],
            "colors": [c.__dict__ for c in colors],
            "specification": specification,
            "created_at": datetime.now().isoformat(),
            "status": "draft"
        }
        
        self.designs[design_id] = design
        return design_id
    
    def _select_materials(self, garment_type: GarmentType, season: str) -> List[Material]:
        """Выбор подходящих материалов"""
        material_map = {
            GarmentType.DRESS: ["cotton", "silk", "polyester"],
            GarmentType.SHIRT: ["cotton", "polyester"],
            GarmentType.PANTS: ["denim", "cotton", "polyester"],
            GarmentType.SKIRT: ["cotton", "polyester", "wool"],
            GarmentType.JACKET: ["wool", "polyester"],
            GarmentType.COAT: ["wool", "polyester"],
            GarmentType.BLOUSE: ["silk", "cotton", "polyester"],
            GarmentType.TSHIRT: ["cotton", "polyester"]
        }
        
        material_names = material_map.get(garment_type, ["cotton"])
        return [self.materials_db[name] for name in material_names[:2]]
    
    def _select_colors(self, style: DesignStyle, season: str) -> List[Color]:
        """Выбор цветовой схемы"""
        if season in self.color_palettes:
            return self.color_palettes[season][0]
        
        # Базовая палитра по стилю
        style_colors = {
            DesignStyle.CASUAL: [Color("#4A90E2", "#7ED321", "#F5A623")],
            DesignStyle.FORMAL: [Color("#000000", "#FFFFFF", "#808080")],
            DesignStyle.SPORT: [Color("#FF0000", "#0000FF", "#FFFFFF")],
            DesignStyle.EVENING: [Color("#800080", "#FFD700", "#000000")],
            DesignStyle.BUSINESS: [Color("#2C3E50", "#34495E", "#ECF0F1")],
            DesignStyle.VINTAGE: [Color("#8B4513", "#D2691E", "#F4A460")],
            DesignStyle.MODERN: [Color("#E74C3C", "#3498DB", "#2ECC71")]
        }
        
        return style_colors.get(style, [Color("#000000", "#FFFFFF")])
    
    def _generate_specification(self, 
                               garment_type: GarmentType,
                               style: DesignStyle,
                               measurements: Measurement,
                               materials: List[Material],
                               colors: List[Color]) -> Dict[str, Any]:
        """Генерация технической спецификации"""
        return {
            "construction": self._get_construction_details(garment_type),
            "features": self._get_features(style, garment_type),
            "sizing": self._calculate_sizing(measurements),
            "material_requirements": self._estimate_materials(materials, measurements),
            "color_scheme": {
                "primary": colors[0].primary,
                "secondary": colors[0].secondary,
                "accent": colors[0].accent
            }
        }
    
    def _get_construction_details(self, garment_type: GarmentType) -> Dict[str, Any]:
        """Получить детали конструкции"""
        constructions = {
            GarmentType.DRESS: {
                "parts": ["bodice", "skirt", "sleeves"],
                "closures": ["zipper", "buttons"],
                "reinforcement": ["interfacing", "stay_tape"]
            },
            GarmentType.SHIRT: {
                "parts": ["front", "back", "sleeves", "collar", "cuffs"],
                "closures": ["buttons"],
                "reinforcement": ["collar_interfacing", "cuff_interfacing"]
            },
            GarmentType.PANTS: {
                "parts": ["front_leg", "back_leg", "waistband"],
                "closures": ["zipper", "button"],
                "reinforcement": ["waistband_interfacing"]
            }
        }
        
        return constructions.get(garment_type, {"parts": [], "closures": [], "reinforcement": []})
    
    def _get_features(self, style: DesignStyle, garment_type: GarmentType) -> List[str]:
        """Получить характеристики по стилю"""
        base_features = {
            DesignStyle.CASUAL: ["comfortable_fit", "easy_care"],
            DesignStyle.FORMAL: ["tailored_fit", "premium_finish"],
            DesignStyle.SPORT: ["stretch_fabric", "moisture_wicking"],
            DesignStyle.EVENING: ["elegant_draping", "luxury_materials"],
            DesignStyle.BUSINESS: ["professional_look", "wrinkle_resistant"],
            DesignStyle.VINTAGE: ["classic_details", "traditional_construction"],
            DesignStyle.MODERN: ["minimalist_design", "innovative_materials"]
        }
        
        return base_features.get(style, [])
    
    def _calculate_sizing(self, measurements: Measurement) -> Dict[str, float]:
        """Расчет размеров для лекал"""
        return {
            "bust_ease": measurements.bust * 0.05,  # 5% прибавка
            "waist_ease": measurements.waist * 0.03,  # 3% прибавка
            "hip_ease": measurements.hips * 0.05,     # 5% прибавка
            "length_adjustment": measurements.height * 0.4  # 40% от роста
        }
    
    def _estimate_materials(self, materials: List[Material], measurements: Measurement) -> Dict[str, float]:
        """Оценка расхода материалов"""
        # Упрощенный расчет
        total_area = (measurements.bust + measurements.hips) * measurements.height * 0.001
        
        return {
            material.name: total_area * 1.2  # 20% запас
            for material in materials
        }
    
    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Получить дизайн по ID"""
        return self.designs.get(design_id)
    
    def list_designs(self) -> List[Dict[str, Any]]:
        """Получить список всех дизайнов"""
        return [
            {
                "id": design_id,
                "type": design["type"],
                "style": design["style"],
                "status": design["status"],
                "created_at": design["created_at"]
            }
            for design_id, design in self.designs.items()
        ]
    
    def update_design(self, design_id: str, updates: Dict[str, Any]) -> bool:
        """Обновить дизайн"""
        if design_id in self.designs:
            self.designs[design_id].update(updates)
            self.designs[design_id]["updated_at"] = datetime.now().isoformat()
            return True
        return False
    
    def delete_design(self, design_id: str) -> bool:
        """Удалить дизайн"""
        if design_id in self.designs:
            del self.designs[design_id]
            return True
        return False
