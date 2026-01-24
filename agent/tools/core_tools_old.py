#!/usr/bin/env python3
"""
Улучшенная версия инструментов с исправленными ошибками
"""
import os
import json
import re
import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Импорт fashion модуля
from .fashion import FashionDesigner, PatternMaker, FashionExporter, CADBridge, GarmentType, DesignStyle, CADSystem

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deg_to_dir(deg: int) -> str:
    """Преобразует градусы ветра в направление"""
    if deg is None:
        return 'н/д'
    
    directions = ['С', 'ССВ', 'СВ', 'ВСВ', 'В', 'ВЮВ', 'ЮВ', 'ЮЮВ', 
                'Ю', 'ЮЮЗ', 'ЮЗ', 'ЗЮЗ', 'З', 'ЗСЗ', 'СЗ', 'ССЗ']
    index = round(deg / 22.5) % 16
    return directions[index]

from .utils import logger, BS4_AVAILABLE

if BS4_AVAILABLE:
    from bs4 import BeautifulSoup

# Импортируем GPU инструменты
try:
    from .gpu_tools import GPUTools
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    GPUTools = None

class ExtendedLocalEnv:
    """Расширенная локальная среда выполнения"""
    
    def __init__(self, agent=None):
        self.agent = agent
        self.tools = {}
        self.tool_descriptions = {}
    
    def register_tool(self, name: str, func, description: str = ""):
        """Регистрирует инструмент"""
        self.tools[name] = func
        self.tool_descriptions[name] = description
        logger.info(f"Registered tool: {name}")
    
    def get_tool(self, name: str):
        """Получает инструмент по имени"""
        return self.tools.get(name)
    
    def list_tools(self):
        """Возвращает список всех инструментов"""
        return list(self.tools.keys())

class ImprovedTools(ExtendedLocalEnv):
    """Улучшенные инструменты с исправлениями"""
    
    def __init__(self, agent=None):
        super().__init__()
        self.agent = agent
        self.gpu_tools = None
        if GPU_AVAILABLE:
            self.gpu_tools = GPUTools(agent)
        
        # Инициализация fashion компонентов
        self.fashion_designer = FashionDesigner()
        self.pattern_maker = PatternMaker()
        self.fashion_exporter = FashionExporter()
        self.cad_bridge = CADBridge()
        
        # Регистрируем основные методы как инструменты
        self.register_tool('analyze_website', self.analyze_website, 'Анализ сайта')
        self.register_tool('create_site_copy', self.create_site_copy, 'Создание копии сайта')
        self.register_tool('generate_original_site', self.generate_original_site, 'Генерация оригинального сайта')
        self.register_tool('get_weather', self.get_weather, 'Получить актуальную погоду в городе')
        self.register_tool('tavily_search', self.tavily_search, 'Поиск информации через Tavily')
        self.register_tool('design_clothing', self.design_clothing, 'Создание дизайна одежды с лекалами и экспортом')
        self.register_tool('generate_design_description', self.generate_design_description, 'Генерация текстового описания конструкции одежды')
        
        # Регистрируем GPU инструменты
        if self.gpu_tools:
            self.register_tool('gpu_status', self.gpu_tools.gpu_status, 'Проверить статус GPU')
            self.register_tool('enable_gpu', self.gpu_tools.enable_gpu, 'Включить GPU')
            self.register_tool('restart_services', self.gpu_tools.restart_services, 'Перезапустить сервисы')
    
    def tavily_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Поиск информации через Tavily API"""
        try:
            from .config import get_env_vars
            env_vars = get_env_vars()
            api_key = env_vars.get("TAVILY_API_KEY", "")
            
            if not api_key:
                return [{'error': 'TAVILY_API_KEY не найден в .env файле'}]
            
            import requests
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "include_raw_content": True,
                "max_results": max_results,
                "include_domains": [],
                "exclude_domains": []
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                return results
            else:
                return [{'error': f'Tavily API error: {response.status_code} - {response.text}'}]
                
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return [{'error': str(e)}]
    
    def get_weather(self, city: str) -> Dict[str, Any]:
        """Получает актуальную погоду через Tavily"""
        try:
            # Улучшенная нормализация города
            city = city.strip().lower().replace(' в ', '').replace('сегодня', '').replace('сейчас', '')
            
            # Расширенный словарь транслитерации для популярных городов
            translit = {
                'киев': 'Kyiv',
                'москва': 'Moscow',
                'вашингтон': 'Washington DC',
                'лондон': 'London',
                'нью-йорк': 'New York',
                'токио': 'Tokyo',
                'одесса': 'Odesa',
                'париж': 'Paris',
                'берлин': 'Berlin',
                'стамбул': 'Istanbul',
                'рим': 'Rome',
                'мадрид': 'Madrid',
                'лиссабон': 'Lisbon',
                'амстердам': 'Amsterdam',
                'прага': 'Prague',
                'варшава': 'Warsaw',
                'будапешт': 'Budapest',
                'вена': 'Vienna',
                'стокгольм': 'Stockholm',
                'осло': 'Oslo',
                'хельсинки': 'Helsinki',
                'копенгаген': 'Copenhagen',
                'брюссель': 'Brussels',
                'дублин': 'Dublin',
                'милан': 'Milan',
                'барселона': 'Barcelona',
                'афина': 'Athens',
                'жанева': 'Geneva',
                'цюрих': 'Zurich',
                'мюнхен': 'Munich',
                'гамбург': 'Hamburg',
                'кёльн': 'Cologne',
                'дюссельдорф': 'Dusseldorf',
                'франкфурт': 'Frankfurt',
                'берн': 'Bern',
                'грац': 'Graz',
                'зальцбург': 'Salzburg',
                'инсбрук': 'Innsbruck',
                'лион': 'Lyon',
                'марсель': 'Marseille',
                'тулуза': 'Toulouse',
                'ницца': 'Nice',
                'бордо': 'Bordeaux',
                'нант': 'Nantes',
                'страсбург': 'Strasbourg',
                'лилль': 'Lille',
                'ренн': 'Rennes',
                'брест': 'Brest',
                'тул': 'Toulon',
                'ле-ман': 'Le Mans',
                'клермон-ферран': 'Clermont-Ferrand',
                'анже': 'Angers',
                'вильнёв-даск': 'Villeneuve-d\'Ascq',
                'сент-этен': 'Saint-Etienne',
                'мулён': 'Mulhouse',
                'руан': 'Rouen',
                'буживаль': 'Boulogne-Billancourt',
                'монпелье': 'Montpellier',
                'лимож': 'Limoges',
                'каен': 'Caen',
                'нанси': 'Nancy',
                'метц': 'Metz',
                'безансон': 'Besançon',
                'тур': 'Tours',
                'амьен': 'Amiens',
                'по': 'Poitiers',
                'ремс': 'Reims',
                'леваллуа-перре': 'Levallois-Perret',
                'дюнкерк': 'Dunkerque',
                'гренобль': 'Grenoble',
                'виктория': 'Victoria',
                'веллингтон': 'Wellington',
                'окленд': 'Auckland',
                'сидней': 'Sydney',
                'мельбурн': 'Melbourne',
                'брисбен': 'Brisbane',
                'перт': 'Perth',
                'аделайда': 'Adelaide',
                'канберра': 'Canberra',
                'хобарт': 'Hobart',
                'дарвин': 'Darwin',
                'каир': 'Cairo',
                'александрия': 'Alexandria',
                'гиза': 'Giza',
                'шарм-эль-шейх': 'Sharm el-Sheikh',
                'хургада': 'Hurghada',
                'люксембург': 'Luxembourg',
                'монако': 'Monaco',
                'андорра-ла-велья': 'Andorra la Vella',
                'ватикан': 'Vatican City',
                'сан-марино': 'San Marino',
                'валлетта': 'Valletta',
                'никосия': 'Nicosia',
                'прая': 'Praia',
                'банжул': 'Banjul',
                'конакри': 'Conakry',
                'бисау': 'Bissau',
                'фритаун': 'Freetown',
                'монровия': 'Monrovia',
                'ямусукро': 'Yamoussoukro',
                'абиджан': 'Abidjan',
                'аккра': 'Accra',
                'ломе': 'Lome',
                'бамако': 'Bamako',
                'уагадугу': 'Ouagadougou',
                'ниамей': 'Niamey',
                'нуакшот': 'Nouakchott',
                'бамако': 'Bamako',
                'конакри': 'Conakry',
                'дакар': 'Dakar',
                'фритаун': 'Freetown',
                'монровия': 'Monrovia',
                'абуджа': 'Abuja',
                'лагос': 'Lagos',
                'кано': 'Kano',
                'ибадан': 'Ibadan',
                'порт-харкорт': 'Port Harcourt',
                'бенин-сити': 'Benin City',
                'маидугури': 'Maiduguri',
                'зария': 'Zaria',
                'аба': 'Aba',
                'джос': 'Jos',
                'илорин': 'Ilorin',
                'ойо': 'Oyo',
                'енугу': 'Enugu',
                'кадуна': 'Kaduna',
                'илеша': 'Ilesha',
                'онича': 'Onitsha',
                'варри': 'Warri',
                'калабар': 'Calabar',
                'сокото': 'Sokoto',
                'ибадан': 'Ibadan',
                'порт-ньюкорт': 'Port Novo',
                'парагвай': 'Asunción',
                'монтевидео': 'Montevideo',
                'буэнос-айрес': 'Buenos Aires',
                'кордова': 'Córdoba',
                'росарио': 'Rosario',
                'мендоса': 'Mendoza',
                'ла-плата': 'La Plata',
                'сальта': 'Salta',
                'мар-дель-плата': 'Mar del Plata',
                'сан-мигель-де-уэлья': 'San Miguel de Tucumán',
                'санта-фе': 'Santa Fe',
                'сан-луис': 'San Luis',
                'неукен': 'Neuquén',
                'бахия-бланка': 'Bahía Blanca',
                'консепсьон': 'Concepción',
                'антофагаста': 'Antofagasta',
                'темуко': 'Temuco',
                'вальпараисо': 'Valparaíso',
                'винья-дель-мар': 'Viña del Mar',
                'такна': 'Tacna',
                'арекипа': 'Arequipa',
                'кузко': 'Cuzco',
                'икита': 'Iquitos',
                'чимботе': 'Chimbote',
                'уанкайо': 'Huancayo',
                'пуно': 'Puno',
                'ика': 'Ica',
                'хульяка': 'Juliaca',
                'кабанас': 'Cabanillas',
                'мольендо': 'Mollendo',
                'писко': 'Pisco',
                'тумбес': 'Tumbes',
                'хайфон': 'Haiphong',
                'дананг': 'Da Nang',
                'хошимин': 'Ho Chi Minh City',
                'нха-транг': 'Nha Trang',
                'далат': 'Da Lat',
                'хюэ': 'Hue',
                'кан-тхо': 'Can Tho',
                'бьен-хоа': 'Bien Hoa',
                'куанг-нгай': 'Quang Ngai',
                'ронг': 'Rong',
                'бен-тре': 'Ben Tre',
                'вин-лонг': 'Vinh Long',
                'кантхо': 'Can Tho',
                'тхай-нгуен': 'Thai Nguyen',
                'бак-зеунг': 'Bac Lieu',
                'ка-мау': 'Ca Mau',
                'дак-лак': 'Dak Lak',
                'дак-нонг': 'Dak Nong',
                'донг-най': 'Dong Nai',
                'донг-тхап': 'Dong Thap',
                'гья-лай': 'Gia Lai',
                'хай-зыонг': 'Hai Duong',
                'ха-джанг': 'Ha Giang',
                'ха-нам': 'Ha Nam',
                'ха-тинь': 'Ha Tinh',
                'хоа-бинь': 'Hoa Binh',
                'хынг-ен': 'Hung Yen',
                'кхань-хоа': 'Khanh Hoa',
                'кьен-зянг': 'Kien Giang',
                'лам-донг': 'Lam Dong',
                'лай-тяу': 'Lai Chau',
                'ланг-шон': 'Lang Son',
                'лао-кай': 'Lao Cai',
                'нам-динь': 'Nam Dinh',
                'нгхе-ан': 'Nghe An',
                'нинь-бинь': 'Ninh Binh',
                'нинь-тхуан': 'Ninh Thuan',
                'фу-йен': 'Phu Yen',
                'куанг-бинь': 'Quang Binh',
                'куанг-нам': 'Quang Nam',
                'куанг-нинь': 'Quang Ninh',
                'куанг-нгай': 'Quang Ngai',
                'куанг-чи': 'Quang Tri',
                'со-чи': 'Sochi',
                'краснодар': 'Krasnodar',
                'ростов-на-дону': 'Rostov-on-Don',
                'новосибирск': 'Novosibirsk',
                'екатеринбург': 'Yekaterinburg',
                'нижний-новгород': 'Nizhny Novgorod',
                'казань': 'Kazan',
                'челябинск': 'Chelyabinsk',
                'омск': 'Omsk',
                'самара': 'Samara',
                'уфа': 'Ufa',
                'красноярск': 'Krasnoyarsk',
                'воронеж': 'Voronezh',
                'пермь': 'Perm',
                'волгоград': 'Volgograd'
            }
            
            # Транслитерация для поиска
            search_city = translit.get(city, city.title())
            
            # Определяем оригинальное название для вывода
            if city in translit:
                original_city = city.title()
            else:
                original_city = search_city.title()
            
            # Динамический запрос на английском для лучшей точности
            query = f"current weather in {search_city} now"
            
            # Прямой вызов Tavily API с правильной загрузкой ключа
            try:
                import os
                from dotenv import load_dotenv
                
                # Загружаем .env явно
                load_dotenv()
                
                api_key = os.getenv("TAVILY_API_KEY", "")
                
                # Логирование для отладки (закомментировано)
                # print(f"DEBUG: API ключ найден: {bool(api_key)}")
                # print(f"DEBUG: Длина ключа: {len(api_key)}")
                # print(f"DEBUG: Текущая директория: {os.getcwd()}")
                
                if not api_key:
                    return {
                        'success': False, 
                        'error': 'TAVILY_API_KEY не найден в .env файле'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Ошибка загрузки API ключа: {str(e)}'
                }
            
            import requests
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "include_raw_content": True,
                "max_results": 5,
                "include_domains": [],
                "exclude_domains": []
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
            else:
                results = [{'error': f'Tavily API error: {response.status_code} - {response.text}'}]
            
            # Логирование результатов Tavily (только для отладки)
            # print(f"DEBUG: Tavily results: {results}")
            
            # Извлекаем и парсим погодные данные
            temp = feels_like = condition = wind_speed = wind_dir = humidity = pressure = None
            relevant_lines = []
            
            # Улучшенные паттерны для парсинга
            temp_pattern = r'(\d+\.?\d*)\s*(?:°[CF]|degrees [CF])?'
            wind_pattern = r'(\d+\.?\d*)\s*(m/s|mph|км/ч|kph)'
            humidity_pattern = r'(\d+)%'
            pressure_pattern = r'(\d+)\s*(mm|мбар|mbar|mb|in)'
            condition_pattern = r'(Overcast|Clear|Cloudy|Rain|Snow|Sunny|Partly cloudy|Fog)'
            
            # Перевод состояний погоды
            condition_translations = {
                'Overcast': 'облачно',
                'Clear': 'ясно',
                'Cloudy': 'облачно',
                'Rain': 'дождь',
                'Snow': 'снег',
                'Sunny': 'солнечно',
                'Partly cloudy': 'малооблачно',
                'Fog': 'туман'
            }
            
            # Перевод направлений ветра
            wind_directions = {
                'N': 'северный', 'S': 'южный', 'E': 'восточный', 'W': 'западный',
                'NE': 'северо-восточный', 'NW': 'северо-западный',
                'SE': 'юго-восточный', 'SW': 'юго-западный',
                'SSE': 'юго-юго-восточный', 'SSW': 'юго-юго-западный',
                'ESE': 'востоко-юго-восточный', 'WSW': 'западо-юго-западный',
                'ENE': 'востоко-северо-восточный', 'WNW': 'западо-северо-западный',
                'north': 'северный', 'south': 'южный', 'east': 'восточный', 'west': 'западный'
            }
            
            for r in results:
                # Пробуем разные поля
                text = ""
                if 'content' in r and r['content']:
                    text = r['content']
                elif 'snippet' in r and r['snippet']:
                    text = r['snippet']
                elif 'title' in r and r['title']:
                    text = r['title']
                
                # Проверяем релевантность результата
                if text:
                    text_lower = text.lower()
                    
                    # Если JSON данные - всегда обрабатываем
                    is_json_data = text and ('temp_c' in text or 'temp_f' in text or 'feelslike_c' in text)
                    
                    if not is_json_data:
                        city_mentioned = search_city.lower() in text_lower
                        if not city_mentioned:
                            continue  # Пропускаем нерелевантные результаты
                
                if text:
                    # Специальная обработка для JSON данных
                    is_json_data = text and ('temp_c' in text or 'temp_f' in text or 'feelslike_c' in text)
                    
                    if is_json_data:
                        try:
                            import json
                            import re
                            # Ищем JSON в строке (может быть в кавычках)
                            json_start = text.find('{')
                            json_end = text.rfind('}') + 1
                            if json_start != -1 and json_end > json_start:
                                json_str = text[json_start:json_end]
                                
                                # Улучшенная обработка кавычек для Python JSON
                                # 1. Убираем escaping
                                json_str = re.sub(r"\'", "'", json_str)
                                # 2. Добавляем двойные кавычки вокруг ключей
                                json_str = re.sub(r"([a-zA-Z_]+):", r'"\1":', json_str)
                                # 3. Заменяем одиночные кавычки на двойные
                                json_str = json_str.replace("'", '"')
                                
                                weather_data = json.loads(json_str)
                                
                                # Извлекаем данные из JSON
                                if 'current' in weather_data:
                                    current = weather_data['current']
                                    
                                    if temp is None and 'temp_c' in current:
                                        temp = float(current['temp_c'])
                                    elif temp is None and 'temp_f' in current:
                                        temp = (float(current['temp_f']) - 32) * 5/9
                                    
                                    if feels_like is None and 'feelslike_c' in current:
                                        feels_like = float(current['feelslike_c'])
                                    elif feels_like is None and 'feelslike_f' in current:
                                        feels_like = (float(current['feelslike_f']) - 32) * 5/9
                                    
                                    if condition is None and 'condition' in current and 'text' in current['condition']:
                                        cond_text = current['condition']['text']
                                        condition = condition_translations.get(cond_text, cond_text.lower())
                                    
                                    if wind_speed is None:
                                        if 'wind_kph' in current:
                                            wind_speed = float(current['wind_kph']) / 3.6  # kph → м/с
                                        elif 'wind_mph' in current:
                                            wind_speed = float(current['wind_mph']) * 0.44704  # mph → м/с
                                    
                                    if wind_dir is None and 'wind_dir' in current:
                                        wind_dir = wind_directions.get(current['wind_dir'], current['wind_dir'])
                                    
                                    if humidity is None and 'humidity' in current:
                                        humidity = float(current['humidity'])
                                    
                                    if pressure is None and 'pressure_mb' in current:
                                        pressure = float(current['pressure_mb']) * 0.75006  # mbar → мм рт. ст.
                                    
                                    relevant_lines.append("JSON данные обработаны")
                                    continue
                        except Exception as e:
                            pass  # Если JSON не удалось распарсить, продолжаем обычную обработку
                    
                    # Расширенный парсинг с улучшенными паттернами
                    import re
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line or len(line) < 3:
                            continue
                        
                        lower_line = line.lower()
                        
                        # Пропускаем мусор
                        skip_keywords = [
                            '©', 'mapbox', 'openstreetmap', 'improve this map', 'перейти к основному',
                            'справка по специальным возможностям', 'почасовой прогноз', 'суточный прогноз',
                            'радар', '##', '#', '00:01 до 06:00', '06:01 до 12:00', '12:01 до 18:',
                            'температура воздуха будет', 'ukraine', 'одесская область', 'ukraine'
                        ]
                        
                        if any(skip in lower_line for skip in skip_keywords):
                            continue
                        
                        # Ищем строки с погодными данными
                        if any(keyword in lower_line for keyword in [
                            '°c', '°с', '°f', 'температура', 'облачно', 'солнечно', 'дождь', 
                            'осадки', 'ясно', 'ветер', 'туман', 'влажность', 'давление',
                            'realfeel', 'ощущается', 'порывы', 'мм рт', 'м/с', 'mph', 'mbar'
                        ]):
                            relevant_lines.append(line)
                            
                            # Расширенные паттерны для температуры
                            if temp is None:
                                temp_match = re.search(temp_pattern, line)
                                if temp_match:
                                    temp_value = float(temp_match.group(1))
                                    if 'F' in line:
                                        # Конвертируем Fahrenheit в Celsius
                                        temp = (temp_value - 32) * 5/9
                                    else:
                                        temp = temp_value
                            
                            # Расширенные паттерны для ощущений
                            elif feels_like is None and ('feels like' in lower_line or 'ощущается' in lower_line or 'realfeel' in lower_line):
                                feel_match = re.search(temp_pattern, line)
                                if feel_match:
                                    feel_value = float(feel_match.group(1))
                                    if 'F' in line:
                                        # Конвертируем Fahrenheit в Celsius
                                        feels_like = (feel_value - 32) * 5/9
                                    else:
                                        feels_like = feel_value
                            
                            # Расширенные паттерны для состояния
                            elif condition is None:
                                condition_match = re.search(condition_pattern, line, re.IGNORECASE)
                                if condition_match:
                                    cond_text = condition_match.group(1)
                                    condition = condition_translations.get(cond_text, cond_text.lower())
                            
                            # Расширенные паттерны для ветра
                            elif wind_speed is None:
                                wind_match = re.search(wind_pattern, line, re.IGNORECASE)
                                if wind_match:
                                    speed_value = float(wind_match.group(1))
                                    unit = wind_match.group(2).lower()
                                    if unit == 'mph':
                                        wind_speed = speed_value * 0.44704  # mph → м/с
                                    elif unit in ['км/ч', 'kph']:
                                        wind_speed = speed_value / 3.6  # km/h → м/с
                                    else:
                                        wind_speed = speed_value
                                
                                # Направление ветра
                                if wind_dir is None:
                                    for dir_key, dir_value in wind_directions.items():
                                        if dir_key.lower() in lower_line:
                                            wind_dir = dir_value
                                            break
                            
                            # Расширенные паттерны для влажности
                            elif humidity is None:
                                humid_match = re.search(humidity_pattern, line)
                                if humid_match:
                                    humidity = float(humid_match.group(1))
                            
                            # Расширенные паттерны для давления
                            elif pressure is None:
                                press_match = re.search(pressure_pattern, line, re.IGNORECASE)
                                if press_match:
                                    press_value = float(press_match.group(1))
                                    unit = press_match.group(2).lower()
                                    if unit == 'mm':
                                        pressure = press_value
                                    elif unit in ['мбар', 'mbar', 'mb']:
                                        pressure = press_value * 0.75006  # mbar → мм рт. ст.
                                    elif unit == 'in':
                                        pressure = press_value * 25.4  # in → мм рт. ст.
            
            # Проверяем количество найденных полей
            found_fields = sum(1 for field in [temp, feels_like, condition, wind_speed, humidity, pressure] if field is not None)
            
            # Fallback к OpenWeather если Tavily не дал достаточно данных
            if found_fields < 3:
                try:
                    # Загружаем API ключ OpenWeather
                    load_dotenv()
                    api_key = os.getenv("OPENWEATHER_API_KEY", "")
                    
                    if api_key:
                        # Запрос к OpenWeather
                        url = f"https://api.openweathermap.org/data/2.5/weather?q={search_city}&appid={api_key}&units=metric&lang=ru"
                        response = requests.get(url, timeout=10)
                        weather_data = response.json()
                        
                        if weather_data.get('cod') == 200:
                            # Извлекаем данные из OpenWeather
                            temp = weather_data['main']['temp']
                            feels_like = weather_data['main']['feels_like']
                            condition = weather_data['weather'][0]['description']
                            wind_speed = weather_data['wind']['speed']
                            wind_dir = deg_to_dir(weather_data['wind'].get('deg'))
                            humidity = weather_data['main']['humidity']
                            pressure = weather_data['main']['pressure'] * 0.75006  # hPa to mmHg
                            
                            weather_text = f"""Сейчас: {temp:.1f}°C
Ощущается как: {feels_like:.1f}°C
Состояние: {condition}
Ветер: {wind_speed:.1f} м/с, {wind_dir}
Влажность: {humidity:.0f}%
Давление: {pressure:.0f} мм рт. ст."""
                            
                            return {
                                'success': True,
                                'city': original_city,
                                'weather': weather_text,
                                'source': 'OpenWeather'
                            }
                except Exception as e:
                    logger.error(f"OpenWeather fallback error: {e}")
                    pass
            
            if found_fields < 3:
                return {
                    'success': False, 
                    'error': f"Не удалось найти точные данные по {original_city}. Уточните город (например, Washington DC) или проверьте на weather.com"
                }
            
            # Проверяем пустые результаты
            if not results or len(results) == 0:
                return {
                    'success': False,
                    'error': 'Данные временно недоступны. Проверьте на weather.com'
                }
            
            # Формируем красивый текст погоды
            # Устанавливаем значения по умолчанию
            temp = temp if temp is not None else 0
            feels_like = feels_like if feels_like is not None else temp
            condition = condition if condition is not None else 'н/д'
            wind_speed = wind_speed if wind_speed is not None else 0
            wind_dir = wind_dir if wind_dir is not None else 'н/д'
            humidity = humidity if humidity is not None else 0
            pressure = pressure if pressure is not None else 0
            
            weather_text = f"""Сейчас: {temp:.1f}°C
Ощущается как: {feels_like:.1f}°C
Состояние: {condition}
Ветер: {wind_speed:.1f} м/с, {wind_dir}
Влажность: {humidity:.0f}%
Давление: {pressure:.0f} мм рт. ст."""
            
            return {
                'success': True,
                'city': original_city,
                'weather': weather_text,
                'source': 'Tavily Search'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Ошибка Tavily: {str(e)}"
            }
    
    def analyze_website(self, url: str, depth: int = 5, **kwargs) -> Dict[str, Any]:
        """Анализирует структуру сайта с рекурсией"""
        import json
        from urllib.parse import urljoin, urlparse
        import time
        
        try:
            logger.info(f"Analyzing website: {url} with depth {depth}")
            
            if not BS4_AVAILABLE:
                return {'success': False, 'error': 'BeautifulSoup not available'}
            
            # Инициализируем структуру анализа
            analysis = {
                'url': url,
                'layout': 'unknown',
                'sections': {},
                'colors': [],
                'fonts': [],
                'css_classes': [],
                'navigation': [],
                'links_count': 0,
                'images_count': 0,
                'pages_analyzed': 0,
                'subpages': [],
                'meta_tags': [],
                'technologies': []
            }
            
            # Анализируем главную страницу
            main_analysis = self._analyze_single_page(url, analysis)
            analysis.update(main_analysis)
            analysis['pages_analyzed'] = 1
            
            # Рекурсивный анализ подстраниц
            if depth > 1:
                subpages_to_analyze = []
                for link in analysis.get('navigation', [])[:depth-1]:
                    link_url = link.get('url', '')
                    if link_url and link_url.startswith('http'):
                        subpages_to_analyze.append(link_url)
                
                # Анализируем подстраницы
                for subpage_url in subpages_to_analyze[:depth-1]:
                    try:
                        logger.info(f"Analyzing subpage: {subpage_url}")
                        subpage_analysis = self._analyze_single_page(subpage_url, {})
                        analysis['subpages'].append({
                            'url': subpage_url,
                            'sections': subpage_analysis.get('sections', {}),
                            'layout': subpage_analysis.get('layout', 'unknown')
                        })
                        analysis['pages_analyzed'] += 1
                        
                        # Объединяем уникальные данные
                        analysis['css_classes'].extend(subpage_analysis.get('css_classes', []))
                        analysis['colors'].extend(subpage_analysis.get('colors', []))
                        analysis['fonts'].extend(subpage_analysis.get('fonts', []))
                        
                        # Небольшая задержка между запросами
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.warning(f"Failed to analyze subpage {subpage_url}: {e}")
            
            # Удаляем дубликаты и сортируем
            analysis['css_classes'] = sorted(list(set(analysis['css_classes'])))[:100]
            analysis['colors'] = list(set(analysis['colors']))[:20]
            analysis['fonts'] = list(set(analysis['fonts']))[:10]
            
            # Определяем основной лейаут
            analysis['layout'] = self._determine_layout_type(analysis)
            
            logger.info(f"Website analysis completed: {analysis['pages_analyzed']} pages, {len(analysis['css_classes'])} classes")
            
            return {
                'success': True,
                'analysis': analysis,
                'message': f"Анализ завершен. Страниц: {analysis['pages_analyzed']}, Секций: {len(analysis['sections'])}, CSS классов: {len(analysis['css_classes'])}"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing website: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_single_page(self, url: str, base_analysis: dict) -> Dict[str, Any]:
        """Анализирует отдельную страницу"""
        from urllib.parse import urljoin
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            page_analysis = base_analysis.copy()
            
            # Анализируем основные разделы
            sections = {}
            for section_name in ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']:
                elements = soup.find_all(section_name)
                if elements:
                    sections[section_name] = []
                    for elem in elements[:3]:
                        sections[section_name].append({
                            'tag': elem.name,
                            'classes': elem.get('class', []),
                            'id': elem.get('id', ''),
                            'text_preview': elem.get_text(strip=True)[:100] + '...' if len(elem.get_text(strip=True)) > 100 else elem.get_text(strip=True)
                        })
            
            page_analysis['sections'] = sections
            
            # Анализируем навигацию
            nav_links = []
            nav_elements = soup.find_all(['nav', 'header'])
            for nav in nav_elements:
                for link in nav.find_all('a', href=True):
                    nav_links.append({
                        'text': link.get_text(strip=True),
                        'url': urljoin(url, link['href']),
                        'classes': link.get('class', [])
                    })
            page_analysis['navigation'] = nav_links[:10]
            
            # Анализируем ссылки и изображения
            all_links = soup.find_all('a', href=True)
            all_images = soup.find_all('img', src=True)
            
            page_analysis['links_count'] = len(all_links)
            page_analysis['images_count'] = len(all_images)
            
            # Извлекаем CSS классы
            all_classes = set()
            for elem in soup.find_all(class_=True):
                all_classes.update(elem['class'])
            page_analysis['css_classes'] = list(all_classes)
            
            # Извлекаем цвета из CSS и inline стилей
            colors = set()
            # Анализ inline стилей
            for elem in soup.find_all(style=True):
                style = elem['style']
                color_matches = re.findall(r'#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)', style)
                colors.update(color_matches)
            
            # Анализ CSS файлов
            css_links = soup.find_all('link', rel='stylesheet')
            for css_link in css_links:
                css_url = urljoin(url, css_link.get('href', ''))
                try:
                    css_response = requests.get(css_url, timeout=10)
                    if css_response.status_code == 200:
                        css_content = css_response.text
                        # Извлекаем цвета из CSS
                        color_matches = re.findall(r'#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)', css_content)
                        colors.update(color_matches)
                        # Проверяем на Bootstrap
                        if 'bootstrap' in css_content.lower():
                            page_analysis.setdefault('technologies', []).append('Bootstrap')
                        # Проверяем на адаптивность
                        if '@media' in css_content:
                            page_analysis['adaptive'] = True
                except:
                    pass
            
            page_analysis['colors'] = list(colors)[:20]
            
            # Извлекаем шрифты
            fonts = set()
            # Из inline стилей
            for elem in soup.find_all(style=True):
                style = elem['style']
                font_matches = re.findall(r'font-family:\s*([^;]+)', style, re.IGNORECASE)
                fonts.update([match.strip() for match in font_matches])
            
            # Из CSS файлов
            for css_link in soup.find_all('link', rel='stylesheet'):
                css_url = urljoin(url, css_link.get('href', ''))
                try:
                    css_response = requests.get(css_url, timeout=10)
                    if css_response.status_code == 200:
                        css_content = css_response.text
                        font_matches = re.findall(r'font-family:\s*([^;]+)', css_content, re.IGNORECASE)
                        fonts.update([match.strip() for match in font_matches])
                except:
                    pass
            
            # Из @font-face
            font_face_elements = soup.find_all('style')
            for style_elem in font_face_elements:
                font_matches = re.findall(r'font-family:\s*["\']([^"\']+)["\']', style_elem.get_text(), re.IGNORECASE)
                fonts.update(font_matches)
            
            page_analysis['fonts'] = list(fonts)[:10]
            
            # Проверяем технологии
            technologies = []
            
            # Bootstrap
            if soup.find(class_=re.compile(r'bootstrap|col-|row|container')):
                technologies.append('Bootstrap')
            
            # jQuery
            if soup.find('script', src=re.compile(r'jquery')):
                technologies.append('jQuery')
            
            # React
            if soup.find('script', src=re.compile(r'react')) or soup.find(id=re.compile(r'react')):
                technologies.append('React')
            
            # Vue.js
            if soup.find('script', src=re.compile(r'vue')) or soup.find(id=re.compile(r'vue')):
                technologies.append('Vue.js')
            
            # Angular
            if soup.find('script', src=re.compile(r'angular')) or soup.find('ng-'):
                technologies.append('Angular')
            
            # Font Awesome
            if soup.find(class_=re.compile(r'fa-|fas|far|fab')):
                technologies.append('Font Awesome')
            
            page_analysis['technologies'] = technologies
            
            # Проверяем адаптивность
            if 'viewport' in str(soup.find('meta', attrs={'name': 'viewport'})):
                page_analysis['adaptive'] = True
            
            # Извлекаем meta теги
            meta_tags = []
            for meta in soup.find_all('meta'):
                meta_tags.append({
                    'name': meta.get('name', meta.get('property', '')),
                    'content': meta.get('content', '')
                })
            page_analysis['meta_tags'] = meta_tags[:10]
            
            return page_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing page {url}: {e}")
            return base_analysis
    
    def _determine_layout_type(self, analysis: dict) -> str:
        """Определяет тип лейаута"""
        sections = analysis.get('sections', {})
        
        if 'aside' in sections and 'main' in sections:
            return 'sidebar'
        elif 'section' in sections and len(sections['section']) > 1:
            return 'grid'
        elif 'main' in sections:
            return 'single'
        else:
            return 'unknown'
    
    def create_site_copy(self, structure_json: str, folder: str = 'site_copy', only_main: bool = False, **kwargs) -> Dict[str, Any]:
        """Создает копию сайта на основе JSON структуры"""
        import json
        import os
        import webbrowser
        import time
        from pathlib import Path
        
        try:
            logger.info(f"Creating site copy in folder: {folder}")
            
            # Парсим JSON структуру
            try:
                structure = json.loads(structure_json) if isinstance(structure_json, str) else structure_json
            except json.JSONDecodeError:
                return {'success': False, 'error': 'Invalid JSON structure'}
            
            # Создаем папки
            base_path = Path(folder)
            css_path = base_path / 'css'
            js_path = base_path / 'js'
            images_path = base_path / 'images'
            
            for path in [base_path, css_path, js_path, images_path]:
                path.mkdir(parents=True, exist_ok=True)
            
            # Создаем базовую HTML структуру
            html_content = self._generate_copy_html(structure)
            
            # Сохраняем файлы
            with open(base_path / 'index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Создаем CSS файл
            css_content = self._generate_copy_css(structure)
            with open(css_path / 'style.css', 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            # Запускаем сервер
            server_url = self._start_server(base_path)
            
            return {
                'success': True,
                'site_name': base_path.name,
                'site_dir': str(base_path),
                'server_url': server_url,
                'message': f"Создана копия сайта в папке '{base_path.name}'"
            }
            
        except Exception as e:
            logger.error(f"Error creating site copy: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_copy_html(self, structure: dict) -> str:
        """Генерирует HTML для копии сайта"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Копия сайта</title>
    <link href="css/style.css" rel="stylesheet">
</head>
<body>
    <header>
        <h1>Копия сайта</h1>
        <nav>
            <ul>
                <li><a href="index.html">Главная</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section>
            <h2>Добро пожаловать!</h2>
            <p>Это копия сайта, созданная Agent S.</p>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 Agent S. Все права защищены.</p>
    </footer>
</body>
</html>"""
    
    def _generate_copy_css(self, structure: dict) -> str:
        """Генерирует CSS для копии сайта"""
        return """/* Стили для копии сайта */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
}

header {
    background: #333;
    color: white;
    padding: 1rem 0;
    text-align: center;
}

header h1 {
    margin: 0;
}

nav ul {
    list-style: none;
    padding: 0;
}

nav ul li {
    display: inline;
    margin: 0 1rem;
}

nav ul li a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    background: #555;
}

nav ul li a:hover {
    background: #777;
}

main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1rem;
}

section {
    background: #f9f9f9;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}

footer {
    background: #333;
    color: white;
    text-align: center;
    padding: 1rem 0;
    margin-top: 2rem;
}

@media (max-width: 768px) {
    main {
        padding: 0 0.5rem;
    }
    
    nav ul li {
        display: block;
        margin: 0.5rem 0;
    }
}"""
    
    def _start_server(self, base_path: Path) -> str:
        """Запускает локальный сервер"""
        import http.server
        import socketserver
        import threading
        import webbrowser
        import random
        
        # Находим свободный порт
        port = random.randint(8000, 9000)
        
        def start_server():
            os.chdir(base_path)
            handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", port), handler) as httpd:
                logger.info(f"Server started at http://localhost:{port}")
                httpd.serve_forever()
        
        # Запускаем сервер в отдельном потоке
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Открываем браузер
        webbrowser.open(f'http://localhost:{port}')
        
        return f'http://localhost:{port}'
    
    def design_clothing(self, 
                     garment_type: str,
                     style: str,
                     measurements: Dict[str, float],
                     output_formats: List[str] = None,
                     cad: str = None) -> Dict[str, Any]:
        """
        Создает дизайн одежды с лекалами и экспортом в CAD системы
        
        Args:
            garment_type: Тип одежды (dress, shirt, pants, skirt, etc.)
            style: Стиль (casual, formal, sport, evening, business, vintage, modern)
            measurements: Словарь с мерками (bust, waist, hips, height, etc.)
            output_formats: Список форматов для экспорта (json, svg, dxf, seamly2d, blender)
            cad: CAD система для интеграции (seamly2d, blender, autocad, inkscape)
            
        Returns:
            Dict с success, files, description
        """
        try:
            # Конвертация параметров в enum типы
            garment_enum = GarmentType(garment_type.lower())
            style_enum = DesignStyle(style.lower())
            
            # Создание дизайна
            design_id = self.fashion_designer.create_design(
                garment_type=garment_enum,
                style=style_enum,
                measurements=measurements
            )
            
            design_data = self.fashion_designer.get_design(design_id)
            if not design_data:
                return {
                    'success': False,
                    'error': 'Не удалось создать дизайн'
                }
            
            # Создание лекал
            patterns = []
            pattern_types = self._get_pattern_types_for_garment(garment_enum)
            
            for pattern_type in pattern_types:
                pattern_data = self.pattern_maker.create_basic_pattern(
                    pattern_type=pattern_type,
                    measurements=measurements
                )
                if pattern_data:
                    patterns.append(pattern_data)
            
            # Настройка форматов экспорта
            if output_formats is None:
                output_formats = ['json', 'svg']
            
            # Экспорт файлов
            exported_files = []
            export_dir = Path.cwd() / 'fashion_exports' / design_id
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Экспорт дизайна
            from .fashion.exporters import ExportOptions, ExportFormat
            for format_name in output_formats:
                try:
                    export_format = ExportFormat(format_name)
                    options = ExportOptions(
                        format=export_format,
                        include_measurements=True,
                        include_grain_lines=True,
                        include_notches=True
                    )
                    
                    # Экспорт дизайна
                    design_file = export_dir / f"design.{format_name}"
                    self.fashion_exporter.export_design(design_data, design_file, options)
                    exported_files.append(str(design_file))
                    
                    # Экспорт лекал
                    for i, pattern in enumerate(patterns):
                        pattern_file = export_dir / f"pattern_{i+1}.{format_name}"
                        self.fashion_exporter.export_pattern(pattern, pattern_file, options)
                        exported_files.append(str(pattern_file))
                        
                except ValueError:
                    # Пропускаем неподдерживаемые форматы
                    continue
            
            # Интеграция с CAD если указана
            cad_result = None
            if cad:
                try:
                    cad_system = CADSystem(cad.lower())
                    
                    # Импорт дизайна в CAD
                    cad_result = self.cad_bridge.import_to_cad(
                        cad_system=cad_system,
                        data=design_data,
                        import_format="json"
                    )
                    
                    # Импорт лекал в CAD
                    for pattern in patterns:
                        pattern_result = self.cad_bridge.import_to_cad(
                            cad_system=cad_system,
                            data=pattern,
                            import_format="json"
                        )
                        
                except ValueError:
                    cad_result = {"error": f"Неподдерживаемая CAD система: {cad}"}
            
            # Формирование описания
            description = f"""Создан дизайн одежды: {garment_type} в стиле {style}

Детали дизайна:
- ID: {design_id}
- Материалы: {', '.join([m['name'] for m in design_data['materials']])}
- Цветовая схема: {design_data['colors'][0]['primary']}

Созданные лекала:
- Количество: {len(patterns)}
- Типы: {', '.join([p['type'] for p in patterns])}

Экспортированные файлы:
- Форматы: {', '.join(output_formats)}
- Количество файлов: {len(exported_files)}

CAD интеграция: {cad if cad else 'Не выполнена'}
"""
            
            return {
                'success': True,
                'files': exported_files,
                'description': description,
                'design_id': design_id,
                'patterns_count': len(patterns),
                'cad_result': cad_result
            }
            
        except Exception as e:
            logger.error(f"Clothing design error: {e}")
            return {
                'success': False,
                'error': f'Ошибка при создании дизайна одежды: {str(e)}'
            }
    
    def _get_pattern_types_for_garment(self, garment_type: GarmentType) -> List:
        """Получить необходимые типы лекал для типа одежды"""
        from .fashion.pattern_maker import PatternType
        
        pattern_map = {
            GarmentType.DRESS: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.SKIRT_FRONT],
            GarmentType.SHIRT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK],  # Только перед + спинка
            GarmentType.PANTS: [PatternType.PANTS_FRONT, PatternType.PANTS_BACK, PatternType.POCKET],
            GarmentType.SKIRT: [PatternType.SKIRT_FRONT, PatternType.SKIRT_BACK, PatternType.POCKET],
            GarmentType.JACKET: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF, PatternType.POCKET],
            GarmentType.COAT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.POCKET],
            GarmentType.BLOUSE: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF],
            GarmentType.TSHIRT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE]
        }
        
        return pattern_map.get(garment_type, [PatternType.BODICE_FRONT])
    
    def generate_design_description(self, 
                                   garment_type: str,
                                   style: str,
                                   additional_requirements: str = "") -> Dict[str, Any]:
        """
        Генерирует текстовое описание конструкции одежды через Ollama
        
        Args:
            garment_type: Тип одежды (dress, shirt, pants, skirt, jacket, coat, blouse, tshirt)
            style: Стиль (casual, formal, sport, evening, business, vintage, modern)
            additional_requirements: Дополнительные требования от пользователя
            
        Returns:
            Dict с success и description
        """
        try:
            # Конвертация параметров в enum типы
            garment_enum = GarmentType(garment_type.lower())
            style_enum = DesignStyle(style.lower())
            
            # Генерация описания через fashion дизайнер
            description = self.fashion_designer.generate_design_description(
                garment_type=garment_enum,
                style=style_enum,
                additional_requirements=additional_requirements
            )
            
            return {
                'success': True,
                'description': description,
                'garment_type': garment_type,
                'style': style,
                'additional_requirements': additional_requirements
            }
            
        except Exception as e:
            logger.error(f"Design description generation error: {e}")
            return {
                'success': False,
                'error': f'Ошибка при генерации описания дизайна: {str(e)}'
            }
    """Улучшенные инструменты с исправлениями"""
    
    def generate_original_site(self, analysis_json: str, content_theme: str = 'my_theme', 
                           folder: str = 'original_site', num_pages: int = 10, 
                           with_sidebar: bool = True, adaptive: bool = True, **kwargs) -> Dict[str, Any]:
        """Генерирует оригинальный многостраничный сайт на основе анализа"""
        import json
        import os
        import webbrowser
        import time
        from pathlib import Path
        
        start_time = time.time()
        
        try:
            logger.info(f"Generating original multi-page site with theme '{content_theme}' in folder: {folder}")
            
            # Парсим анализ
            try:
                analysis = json.loads(analysis_json) if isinstance(analysis_json, str) else analysis_json
            except json.JSONDecodeError:
                return {'success': False, 'error': 'Invalid JSON analysis'}
            
            # Создаем папки
            base_path = Path(folder)
            css_path = base_path / 'css'
            js_path = base_path / 'js'
            pages_path = base_path / 'pages'
            images_path = base_path / 'images'
            
            for path in [base_path, css_path, js_path, pages_path, images_path]:
                path.mkdir(parents=True, exist_ok=True)
            
            # Генерируем многостраничный сайт через Ollama
            if hasattr(self, 'agent') and hasattr(self.agent, 'ollama_client') and self.agent.ollama_client:
                try:
                    # Загружаем хорошие примеры для обучения
                    from .utils import load_good_examples, format_examples_for_prompt
                    good_examples = load_good_examples("website_original", limit=3)
                    examples_text = format_examples_for_prompt(good_examples)
                    
                    prompt = f"""Действуй как Grok - думай шаг за шагом с Chain of Thought. Создай оригинальный многостраничный сайт на основе анализа.

Анализ: {json.dumps(analysis, ensure_ascii=False, indent=2)}
Тема: {content_theme}
Количество страниц: {num_pages}
С сайдбаром: {with_sidebar}
Адаптивный дизайн: {adaptive}
Используй хорошие примеры: {examples_text}

Chain of Thought (CoT):
Шаг 1: Проанализируй структуру сайта
- Определи лейаут: {analysis.get('layout', 'grid')}
- Выдели ключевые секции: {list(analysis.get('sections', {}).keys())}
- Найди цвета: {analysis.get('colors', [])[:3]}
- Определи навигацию: {len(analysis.get('navigation', []))} пунктов

Шаг 2: Создай структуру сайта
- Главная страница (index.html): hero секция, о компании, услуги
- О нас (about.html): история, команда, миссия
- Услуги (services.html): каталог услуг, цены
- Портфолио (portfolio.html): проекты, галерея
- Блог (blog.html): статьи, категории
- Контакты (contact.html): форма, карта, информация
- Дополнительно: создай еще {num_pages - 6} страниц по теме

Шаг 3: Используй Bootstrap 5 CDN
- Подключи Bootstrap CSS и JS
- Используй Bootstrap компоненты: navbar, cards, carousel
- Добавь Font Awesome для иконок

Шаг 4: Создай адаптивный дизайн
- Используй Bootstrap grid систему
- Добавь @media запросы для мобильных устройств
- Сделай навигацию collapsible на мобильных

Шаг 5: Добавь сайдбар
- Размести дополнительную информацию
- Добавь виджеты: поиск, категории, последние новости
- Сделай сайдбар адаптивным

Создай HTML для каждой страницы с:
- Bootstrap навигацией
- Сайдбаром (если включен)
- Адаптивным дизайном
- Оригинальным контентом по теме {content_theme}

Верни результат в формате JSON:
{{
    "pages": [
        {{
            "filename": "index.html",
            "title": "Главная",
            "content": "HTML код страницы"
        }}
    ],
    "css": "CSS стили",
    "js": "JavaScript код"
}}"""

                    response = self.agent.ollama_client.generate(prompt)
                    
                    if response:
                        try:
                            # Пытаемся извлечь JSON из ответа
                            json_match = re.search(r'\\{.*\\}', response, re.DOTALL)
                            if json_match:
                                site_data = json.loads(json_match.group())
                                
                                # Создаем файлы
                                pages_created = []
                                for page in site_data.get('pages', []):
                                    filename = page.get('filename', 'index.html')
                                    content = page.get('content', '')
                                    
                                    page_path = base_path / filename
                                    with open(page_path, 'w', encoding='utf-8') as f:
                                        f.write(content)
                                    pages_created.append(filename)
                                
                                # Создаем CSS файл
                                css_content = site_data.get('css', '')
                                if css_content:
                                    css_file = css_path / 'style.css'
                                    with open(css_file, 'w', encoding='utf-8') as f:
                                        f.write(css_content)
                                
                                # Создаем JS файл
                                js_content = site_data.get('js', '')
                                if js_content:
                                    js_file = js_path / 'script.js'
                                    with open(js_file, 'w', encoding='utf-8') as f:
                                        f.write(js_content)
                                
                                # Запускаем сервер
                                server_url = self._start_server(base_path)
                                
                                execution_time = time.time() - start_time
                                
                                return {
                                    'success': True,
                                    'site_name': base_path.name,
                                    'site_dir': str(base_path),
                                    'pages_created': pages_created,
                                    'server_url': server_url,
                                    'execution_time': execution_time,
                                    'message': f"Создан оригинальный сайт '{base_path.name}' с {len(pages_created)} страницами"
                                }
                            else:
                                # Если JSON не найден, создаем базовый сайт
                                return self._create_basic_site(analysis, content_theme, base_path, num_pages, start_time)
                                
                        except json.JSONDecodeError:
                            # Если парсинг JSON не удался, создаем базовый сайт
                            return self._create_basic_site(analysis, content_theme, base_path, num_pages, start_time)
                    else:
                        return {'success': False, 'error': 'No response from Ollama'}
                        
                except Exception as e:
                    logger.error(f"Error generating with Ollama: {e}")
                    return {'success': False, 'error': str(e)}
            else:
                return {'success': False, 'error': 'Ollama client not available'}
                
        except Exception as e:
            logger.error(f"Error generating original site: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_basic_site(self, analysis: Dict[str, Any], theme: str, base_path: Path, 
                         num_pages: int, start_time: float) -> Dict[str, Any]:
        """Создает базовый сайт если Ollama недоступен"""
        
        # Определяем основные цвета
        colors = analysis.get('colors', ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d'])
        primary_color = colors[0] if colors else '#007bff'
        
        # Создаем главную страницу
        index_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{theme.title()} - Главный сайт</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .hero-section {{
            background: linear-gradient(135deg, {primary_color} 0%, #667eea 100%);
            color: white;
            padding: 100px 0;
            text-align: center;
        }}
        .feature-card {{
            transition: transform 0.3s ease;
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .feature-card:hover {{
            transform: translateY(-5px);
        }}
        .sidebar {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        @media (max-width: 768px) {{
            .sidebar {{
                margin-bottom: 30px;
            }}
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="#">{theme.title()}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="index.html">Главная</a></li>
                    <li class="nav-item"><a class="nav-link" href="about.html">О нас</a></li>
                    <li class="nav-item"><a class="nav-link" href="services.html">Услуги</a></li>
                    <li class="nav-item"><a class="nav-link" href="portfolio.html">Портфолио</a></li>
                    <li class="nav-item"><a class="nav-link" href="contact.html">Контакты</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="hero-section">
        <div class="container">
            <h1 class="display-4 mb-4">Добро пожаловать в {theme.title()}</h1>
            <p class="lead mb-4">Профессиональные решения для вашего бизнеса</p>
            <a href="#services" class="btn btn-light btn-lg">Узнать больше</a>
        </div>
    </div>

    <div class="container mt-5">
        <div class="row">
            <div class="col-lg-8">
                <section id="services" class="mb-5">
                    <h2 class="text-center mb-4">Наши услуги</h2>
                    <div class="row">
                        <div class="col-md-4 mb-4">
                            <div class="card feature-card h-100">
                                <div class="card-body text-center">
                                    <i class="fas fa-rocket fa-3x mb-3 text-primary"></i>
                                    <h5 class="card-title">Быстрый старт</h5>
                                    <p class="card-text">Запускаем проекты в кратчайшие сроки с гарантией качества.</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="card feature-card h-100">
                                <div class="card-body text-center">
                                    <i class="fas fa-shield-alt fa-3x mb-3 text-success"></i>
                                    <h5 class="card-title">Надежность</h5>
                                    <p class="card-text">Используем лучшие практики и технологии для стабильной работы.</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="card feature-card h-100">
                                <div class="card-body text-center">
                                    <i class="fas fa-chart-line fa-3x mb-3 text-warning"></i>
                                    <h5 class="card-title">Рост</h5>
                                    <p class="card-text">Помогаем вашему бизнесу расти и развиваться.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
            
            <div class="col-lg-4">
                <div class="sidebar">
                    <h5 class="mb-3">Последние новости</h5>
                    <div class="list-group">
                        <a href="#" class="list-group-item list-group-item-action">
                            <h6 class="mb-1">Новый проект запущен</h6>
                            <small>3 дня назад</small>
                        </a>
                        <a href="#" class="list-group-item list-group-item-action">
                            <h6 class="mb-1">Обновление услуг</h6>
                            <small>1 неделю назад</small>
                        </a>
                    </div>
                </div>
                
                <div class="sidebar">
                    <h5 class="mb-3">Контакты</h5>
                    <p><i class="fas fa-phone"></i> +7 (999) 123-45-67</p>
                    <p><i class="fas fa-envelope"></i> info@example.com</p>
                    <p><i class="fas fa-map-marker-alt"></i> Москва, Россия</p>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p>&copy; 2024 {theme.title()}. Все права защищены.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        
        # Создаем дополнительные страницы
        pages = {
            'about.html': self._create_about_page(theme, primary_color),
            'services.html': self._create_services_page(theme, primary_color),
            'portfolio.html': self._create_portfolio_page(theme, primary_color),
            'contact.html': self._create_contact_page(theme, primary_color)
        }
        
        # Создаем файлы
        pages_created = []
        
        # Главная страница
        index_path = base_path / 'index.html'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        pages_created.append('index.html')
        
        # Дополнительные страницы
        for filename, content in pages.items():
            page_path = base_path / filename
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(content)
            pages_created.append(filename)
        
        # Запускаем сервер
        server_url = self._start_server(base_path)
        
        execution_time = time.time() - start_time
        
        return {
            'success': True,
            'site_name': base_path.name,
            'site_dir': str(base_path),
            'pages_created': pages_created,
            'server_url': server_url,
            'execution_time': execution_time,
            'message': f"Создан оригинальный сайт '{base_path.name}' с {len(pages_created)} страницами"
        }
    
    def _create_about_page(self, theme: str, primary_color: str) -> str:
        """Создает страницу О нас"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>О нас - {theme.title()}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .hero-section {{
            background: {primary_color};
            color: white;
            padding: 60px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.html">{theme.title()}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="index.html">Главная</a></li>
                    <li class="nav-item"><a class="nav-link active" href="about.html">О нас</a></li>
                    <li class="nav-item"><a class="nav-link" href="services.html">Услуги</a></li>
                    <li class="nav-item"><a class="nav-link" href="portfolio.html">Портфолио</a></li>
                    <li class="nav-item"><a class="nav-link" href="contact.html">Контакты</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="hero-section">
        <div class="container">
            <h1 class="display-4">О нашей компании</h1>
            <p class="lead">Мы - команда профессионалов, увлеченных своим делом</p>
        </div>
    </div>

    <div class="container mt-5">
        <div class="row">
            <div class="col-lg-8">
                <h2>Наша история</h2>
                <p>Компания {theme.title()} была основана в 2020 году с целью предоставления инновационных решений в сфере цифровых технологий.</p>
                
                <h3 class="mt-4">Наша миссия</h3>
                <p>Мы стремимся помогать бизнесу трансформироваться в цифровую эпоху, используя передовые технологии и подходы.</p>
                
                <h3 class="mt-4">Наши ценности</h3>
                <ul>
                    <li>Качество во всем</li>
                    <li>Инновационный подход</li>
                    <li>Клиентоориентированность</li>
                    <li>Постоянное развитие</li>
                </ul>
            </div>
            
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Ключевые факты</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Год основания:</strong> 2020</p>
                        <p><strong>Проектов завершено:</strong> 150+</p>
                        <p><strong>Клиентов:</strong> 50+</p>
                        <p><strong>Сотрудников:</strong> 25</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p>&copy; 2024 {theme.title()}. Все права защищены.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
    
    def _create_services_page(self, theme: str, primary_color: str) -> str:
        """Создает страницу Услуги"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Услуги - {theme.title()}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .service-card {{
            transition: transform 0.3s ease;
            height: 100%;
        }}
        .service-card:hover {{
            transform: translateY(-5px);
        }}
        .price {{
            font-size: 1.5rem;
            color: {primary_color};
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.html">{theme.title()}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="index.html">Главная</a></li>
                    <li class="nav-item"><a class="nav-link" href="about.html">О нас</a></li>
                    <li class="nav-item"><a class="nav-link active" href="services.html">Услуги</a></li>
                    <li class="nav-item"><a class="nav-link" href="portfolio.html">Портфолио</a></li>
                    <li class="nav-item"><a class="nav-link" href="contact.html">Контакты</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <h1 class="text-center mb-5">Наши услуги</h1>
        
        <div class="row">
            <div class="col-md-4 mb-4">
                <div class="card service-card">
                    <div class="card-body text-center">
                        <i class="fas fa-code fa-3x mb-3 text-primary"></i>
                        <h5 class="card-title">Веб-разработка</h5>
                        <p class="card-text">Создание современных веб-приложений с использованием передовых технологий.</p>
                        <p class="price">от 50 000 руб.</p>
                        <a href="contact.html" class="btn btn-primary">Заказать</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4 mb-4">
                <div class="card service-card">
                    <div class="card-body text-center">
                        <i class="fas fa-mobile-alt fa-3x mb-3 text-success"></i>
                        <h5 class="card-title">Мобильные приложения</h5>
                        <p class="card-text">Разработка нативных и кроссплатформенных мобильных приложений.</p>
                        <p class="price">от 100 000 руб.</p>
                        <a href="contact.html" class="btn btn-success">Заказать</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4 mb-4">
                <div class="card service-card">
                    <div class="card-body text-center">
                        <i class="fas fa-palette fa-3x mb-3 text-warning"></i>
                        <h5 class="card-title">Дизайн</h5>
                        <p class="card-text">UI/UX дизайн, брендинг и создание фирменного стиля.</p>
                        <p class="price">от 30 000 руб.</p>
                        <a href="contact.html" class="btn btn-warning">Заказать</a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p>&copy; 2024 {theme.title()}. Все права защищены.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
    
    def _create_portfolio_page(self, theme: str, primary_color: str) -> str:
        """Создает страницу Портфолио"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Портфолио - {theme.title()}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .portfolio-item {{
            transition: transform 0.3s ease;
            overflow: hidden;
        }}
        .portfolio-item:hover {{
            transform: scale(1.05);
        }}
        .portfolio-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        .portfolio-item:hover .portfolio-overlay {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.html">{theme.title()}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="index.html">Главная</a></li>
                    <li class="nav-item"><a class="nav-link" href="about.html">О нас</a></li>
                    <li class="nav-item"><a class="nav-link" href="services.html">Услуги</a></li>
                    <li class="nav-item"><a class="nav-link active" href="portfolio.html">Портфолио</a></li>
                    <li class="nav-item"><a class="nav-link" href="contact.html">Контакты</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <h1 class="text-center mb-5">Наши проекты</h1>
        
        <div class="row">
            <div class="col-md-4 mb-4">
                <div class="portfolio-item position-relative">
                    <img src="https://via.placeholder.com/400x300/007bff/ffffff?text=Проект+1" class="img-fluid" alt="Проект 1">
                    <div class="portfolio-overlay">
                        <div class="text-center">
                            <h5>Корпоративный сайт</h5>
                            <p>Веб-сайт для компании ABC</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4 mb-4">
                <div class="portfolio-item position-relative">
                    <img src="https://via.placeholder.com/400x300/28a745/ffffff?text=Проект+2" class="img-fluid" alt="Проект 2">
                    <div class="portfolio-overlay">
                        <div class="text-center">
                            <h5>Мобильное приложение</h5>
                            <p>Приложение для доставки еды</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4 mb-4">
                <div class="portfolio-item position-relative">
                    <img src="https://via.placeholder.com/400x300/ffc107/000000?text=Проект+3" class="img-fluid" alt="Проект 3">
                    <div class="portfolio-overlay">
                        <div class="text-center">
                            <h5>Интернет-магазин</h5>
                            <p>Платформа электронной коммерции</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p>&copy; 2024 {theme.title()}. Все права защищены.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
    
    def _create_contact_page(self, theme: str, primary_color: str) -> str:
        """Создает страницу Контакты"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Контакты - {theme.title()}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .contact-form {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .contact-info {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            height: 100%;
        }}
        .btn-primary {{
            background-color: {primary_color};
            border-color: {primary_color};
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="index.html">{theme.title()}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="index.html">Главная</a></li>
                    <li class="nav-item"><a class="nav-link" href="about.html">О нас</a></li>
                    <li class="nav-item"><a class="nav-link" href="services.html">Услуги</a></li>
                    <li class="nav-item"><a class="nav-link" href="portfolio.html">Портфолио</a></li>
                    <li class="nav-item"><a class="nav-link active" href="contact.html">Контакты</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <h1 class="text-center mb-5">Свяжитесь с нами</h1>
        
        <div class="row">
            <div class="col-lg-8">
                <div class="contact-form">
                    <h3 class="mb-4">Отправить сообщение</h3>
                    <form>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="name" class="form-label">Имя</label>
                                <input type="text" class="form-control" id="name" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" required>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="subject" class="form-label">Тема</label>
                            <input type="text" class="form-control" id="subject" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="message" class="form-label">Сообщение</label>
                            <textarea class="form-control" id="message" rows="5" required></textarea>
                        </div>
                        
                        <button type="submit" class="btn btn-primary btn-lg">Отправить сообщение</button>
                    </form>
                </div>
            </div>
            
            <div class="col-lg-4">
                <div class="contact-info">
                    <h3 class="mb-4">Контактная информация</h3>
                    
                    <div class="mb-3">
                        <h5><i class="fas fa-map-marker-alt me-2"></i>Адрес</h5>
                        <p>г. Москва, ул. Примерная, д. 123</p>
                    </div>
                    
                    <div class="mb-3">
                        <h5><i class="fas fa-phone me-2"></i>Телефон</h5>
                        <p>+7 (999) 123-45-67</p>
                    </div>
                    
                    <div class="mb-3">
                        <h5><i class="fas fa-envelope me-2"></i>Email</h5>
                        <p>info@example.com</p>
                    </div>
                    
                    <div class="mb-3">
                        <h5><i class="fas fa-clock me-2"></i>Время работы</h5>
                        <p>Пн-Пт: 9:00 - 18:00<br>Сб-Вс: выходной</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p>&copy; 2024 {theme.title()}. Все права защищены.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
    
    def _start_server(self, base_path: Path) -> str:
        """Запускает локальный сервер"""
        import http.server
        import socketserver
        import threading
        import webbrowser
        import random
        
        # Находим свободный порт
        port = random.randint(8000, 9000)
        
        def start_server():
            os.chdir(base_path)
            handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", port), handler) as httpd:
                logger.info(f"Server started at http://localhost:{port}")
                httpd.serve_forever()
        
        # Запускаем сервер в отдельном потоке
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Открываем браузер
        webbrowser.open(f'http://localhost:{port}')
        
        return f'http://localhost:{port}'
    
    def design_clothing(self, 
                     garment_type: str,
                     style: str,
                     measurements: Dict[str, float],
                     output_formats: List[str] = None,
                     cad: str = None) -> Dict[str, Any]:
        """
        Создает дизайн одежды с лекалами и экспортом в CAD системы
        
        Args:
            garment_type: Тип одежды (dress, shirt, pants, skirt, etc.)
            style: Стиль (casual, formal, sport, evening, business, vintage, modern)
            measurements: Словарь с мерками (bust, waist, hips, height, etc.)
            output_formats: Список форматов для экспорта (json, svg, dxf, seamly2d, blender)
            cad: CAD система для интеграции (seamly2d, blender, autocad, inkscape)
            
        Returns:
            Dict с success, files, description
        """
        try:
            # Конвертация параметров в enum типы
            garment_enum = GarmentType(garment_type.lower())
            style_enum = DesignStyle(style.lower())
            
            # Создание дизайна
            design_id = self.fashion_designer.create_design(
                garment_type=garment_enum,
                style=style_enum,
                measurements=measurements
            )
            
            design_data = self.fashion_designer.get_design(design_id)
            if not design_data:
                return {
                    'success': False,
                    'error': 'Не удалось создать дизайн'
                }
            
            # Создание лекал
            patterns = []
            pattern_types = self._get_pattern_types_for_garment(garment_enum)
            
            for pattern_type in pattern_types:
                pattern_data = self.pattern_maker.create_basic_pattern(
                    pattern_type=pattern_type,
                    measurements=measurements
                )
                if pattern_data:
                    patterns.append(pattern_data)
            
            # Настройка форматов экспорта
            if output_formats is None:
                output_formats = ['json', 'svg']
            
            # Экспорт файлов
            exported_files = []
            export_dir = Path.cwd() / 'fashion_exports' / design_id
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Экспорт дизайна
            from .fashion.exporters import ExportOptions, ExportFormat
            for format_name in output_formats:
                try:
                    export_format = ExportFormat(format_name)
                    options = ExportOptions(
                        format=export_format,
                        include_measurements=True,
                        include_grain_lines=True,
                        include_notches=True
                    )
                    
                    # Экспорт дизайна
                    design_file = export_dir / f"design.{format_name}"
                    self.fashion_exporter.export_design(design_data, design_file, options)
                    exported_files.append(str(design_file))
                    
                    # Экспорт лекал
                    for i, pattern in enumerate(patterns):
                        pattern_file = export_dir / f"pattern_{i+1}.{format_name}"
                        self.fashion_exporter.export_pattern(pattern, pattern_file, options)
                        exported_files.append(str(pattern_file))
                        
                except ValueError:
                    # Пропускаем неподдерживаемые форматы
                    continue
            
            # Интеграция с CAD если указана
            cad_result = None
            if cad:
                try:
                    cad_system = CADSystem(cad.lower())
                    
                    # Импорт дизайна в CAD
                    cad_result = self.cad_bridge.import_to_cad(
                        cad_system=cad_system,
                        data=design_data,
                        import_format="json"
                    )
                    
                    # Импорт лекал в CAD
                    for pattern in patterns:
                        pattern_result = self.cad_bridge.import_to_cad(
                            cad_system=cad_system,
                            data=pattern,
                            import_format="json"
                        )
                        
                except ValueError:
                    cad_result = {"error": f"Неподдерживаемая CAD система: {cad}"}
            
            # Формирование описания
            description = f"""Создан дизайн одежды: {garment_type} в стиле {style}

Детали дизайна:
- ID: {design_id}
- Материалы: {', '.join([m['name'] for m in design_data['materials']])}
- Цветовая схема: {design_data['colors'][0]['primary']}

Созданные лекала:
- Количество: {len(patterns)}
- Типы: {', '.join([p['type'] for p in patterns])}

Экспортированные файлы:
- Форматы: {', '.join(output_formats)}
- Количество файлов: {len(exported_files)}

CAD интеграция: {cad if cad else 'Не выполнена'}
"""
            
            return {
                'success': True,
                'files': exported_files,
                'description': description,
                'design_id': design_id,
                'patterns_count': len(patterns),
                'cad_result': cad_result
            }
            
        except Exception as e:
            logger.error(f"Clothing design error: {e}")
            return {
                'success': False,
                'error': f'Ошибка при создании дизайна одежды: {str(e)}'
            }
    
    def _get_pattern_types_for_garment(self, garment_type: GarmentType) -> List:
        """Получить необходимые типы лекал для типа одежды"""
        from .fashion.pattern_maker import PatternType
        
        pattern_map = {
            GarmentType.DRESS: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.SKIRT_FRONT],
            GarmentType.SHIRT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK],  # Только перед + спинка
            GarmentType.PANTS: [PatternType.PANTS_FRONT, PatternType.PANTS_BACK, PatternType.POCKET],
            GarmentType.SKIRT: [PatternType.SKIRT_FRONT, PatternType.SKIRT_BACK, PatternType.POCKET],
            GarmentType.JACKET: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF, PatternType.POCKET],
            GarmentType.COAT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.POCKET],
            GarmentType.BLOUSE: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE, PatternType.COLLAR, PatternType.CUFF],
            GarmentType.TSHIRT: [PatternType.BODICE_FRONT, PatternType.BODICE_BACK, PatternType.SLEEVE]
        }
        
        return pattern_map.get(garment_type, [PatternType.BODICE_FRONT])
