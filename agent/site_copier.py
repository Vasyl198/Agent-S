#!/usr/bin/env python3
"""
Улучшенный копировщик сайтов с поддержкой динамических сайтов (Wix, React, etc.)
"""

import os
import re
import time
import json
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Selenium для рендеринга JavaScript
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    webdriver = None

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SiteCopier:
    """Улучшенный копировщик сайтов с поддержкой динамических контентов"""
    
    def __init__(self, render_js=False, download_external=True, max_depth=3):
        self.render_js = render_js
        self.download_external = download_external
        self.max_depth = max_depth
        self.session = requests.Session()
        self.driver = None
        
        # Настройка retry стратегии
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # User-Agent для лучшей совместимости
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Инициализация Selenium если нужно
        if self.render_js and SELENIUM_AVAILABLE:
            self._setup_selenium()
        elif self.render_js and not SELENIUM_AVAILABLE:
            logger.warning("⚠️ Selenium не установлен. Рендеринг JavaScript отключен.")
            logger.info("💡 Установите Selenium: pip install selenium")
            self.render_js = False
    
    def _setup_selenium(self):
        """Настраивает Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Безголовый режим
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Отключаем ненужные функции для скорости
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-images')  # Не загружаем изображения для скорости
            chrome_options.add_argument('--disable-javascript')  # Включаем только когда нужно
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Selenium WebDriver настроен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки Selenium: {e}")
            logger.info("💡 Убедитесь что ChromeDriver установлен и в PATH")
            self.render_js = False
            self.driver = None
    
    def get_rendered_html(self, url, wait_time=10):
        """Получает HTML с отрендеренным JavaScript"""
        if not self.driver:
            logger.warning("⚠️ Selenium WebDriver не доступен")
            return None
        
        try:
            logger.info(f"🔄 Рендеринг страницы: {url}")
            self.driver.get(url)
            
            # Ожидаем загрузки страницы
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Дополнительное ожидание для рендеринга JS
            time.sleep(3)
            
            # Прокручиваем страницу для загрузки ленивых элементов
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            html = self.driver.page_source
            logger.info("✅ Страница отрендерена")
            return html
            
        except TimeoutException:
            logger.warning(f"⏰ Таймаут ожидания страницы: {url}")
            return self.driver.page_source
        except Exception as e:
            logger.error(f"❌ Ошибка рендеринга страницы: {e}")
            return None
    
    def __del__(self):
        """Очищает ресурсы"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def sanitize_filename(self, filename):
        """Очищает имя файла от недопустимых символов"""
        if not filename:
            return "unknown_file"
        
        # Декодируем URL编码
        filename = unquote(filename)
        
        # Удаляем параметры запроса
        filename = filename.split('?')[0]
        
        # Заменяем недопустимые символы
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, '_', filename)
        
        # Ограничиваем длину
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        # Удаляем точки в начале
        filename = filename.lstrip('.')
        
        return filename or "unnamed_file"
    
    def extract_resource_name(self, url, resource_type):
        """Извлекает имя ресурса из URL"""
        parsed = urlparse(url)
        path = parsed.path
        
        if not path:
            return f"{resource_type}_{int(time.time())}"
        
        filename = path.split('/')[-1]
        
        # Добавляем расширение если отсутствует
        if resource_type == 'css' and not filename.endswith('.css'):
            filename += '.css'
        elif resource_type == 'js' and not filename.endswith('.js'):
            filename += '.js'
        elif resource_type == 'img':
            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']):
                filename += '.jpg'
        
        return self.sanitize_filename(filename)
    
    def download_resource_with_retry(self, url, resource_type, max_retries=2):
        """Скачивает ресурс с retry механизмом"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=20)
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden for {url} (attempt {attempt + 1})")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(2 ** attempt)  # Экспоненциальная задержка
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    return None
            except Exception as e:
                logger.warning(f"Error downloading {url} (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)
        
        return None
    
    def copy_site(self, url, output_dir=None, depth=1):
        """Копирует сайт с улучшенной обработкой ошибок"""
        try:
            logger.info(f"🚀 Starting enhanced site copy: {url}")
            logger.info(f"⚙️ Параметры: render_js={self.render_js}, download_external={self.download_external}, depth={depth}")
            
            # Создаем директорию
            if not output_dir:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                domain = urlparse(url).netloc.replace('www.', '')
                output_dir = f"site_copy_{domain}_{timestamp}"
            
            site_dir = Path(output_dir)
            site_dir.mkdir(exist_ok=True)
            
            # Создаем подпапки
            css_path = site_dir / "css"
            js_path = site_dir / "js"
            images_path = site_dir / "images"
            subpages_path = site_dir / "subpages"
            
            for path in [css_path, js_path, images_path, subpages_path]:
                path.mkdir(exist_ok=True)
            
            # Получаем HTML (с рендерингом или без)
            if self.render_js:
                logger.info(f"🔄 Using Selenium for JavaScript rendering")
                html_content = self.get_rendered_html(url)
                if not html_content:
                    logger.warning("⚠️ Selenium не смог получить HTML, пробую обычный запрос")
                    response = self.download_resource_with_retry(url, 'html')
                    html_content = response.text if response else ""
            else:
                logger.info(f"📄 Downloading main page: {url}")
                response = self.download_resource_with_retry(url, 'html')
                html_content = response.text if response else ""
            
            if not html_content:
                raise Exception(f"Failed to get HTML from: {url}")
            
            # Парсим HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Удаляем base href если есть
            base_tag = soup.find('base')
            if base_tag:
                base_tag.decompose()
                logger.info("🗑️ Removed base href tag")
            
            # Обрабатываем inline CSS и JS
            self._process_inline_content(soup, css_path, js_path, url)
            
            # Обрабатываем внешние файлы
            css_files, js_files, img_files = self._process_external_files(soup, css_path, js_path, images_path, url)
            
            # Анализируем Wix компоненты
            self._analyze_wix_components(soup, images_path, url)
            
            # Сохраняем обновленный HTML
            index_path = site_dir / "index.html"
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            # Рекурсивное копирование подстраниц
            subpages = []
            if depth > 1:
                subpages = self._copy_subpages(soup, url, subpages_path, depth - 1)
            
            # Статистика
            total_files = len(css_files) + len(js_files) + len(img_files) + len(subpages) + 1
            
            result = {
                'success': True,
                'output_dir': output_dir,
                'statistics': {
                    'css_files': len(css_files),
                    'js_files': len(js_files),
                    'img_files': len(img_files),
                    'subpages': len(subpages),
                    'total_files': total_files
                },
                'files': {
                    'css': css_files,
                    'js': js_files,
                    'img': img_files,
                    'subpages': subpages
                }
            }
            
            logger.info(f"🎉 Site copy completed: {total_files} files")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error copying site: {e}")
            return {
                'success': False,
                'error': str(e),
                'output_dir': output_dir
            }
    
    def _process_inline_content(self, soup, css_path, js_path, base_url):
        """Обрабатывает inline CSS и JS"""
        logger.info("🎨 Processing inline CSS...")
        css_files = []
        
        # Обрабатываем inline <style> теги
        style_tags = soup.find_all('style')
        for i, style in enumerate(style_tags):
            css_content = style.get_text()
            if css_content.strip():
                filename = f"inline_{i+1}.css"
                css_file_path = css_path / filename
                
                try:
                    with open(css_file_path, 'w', encoding='utf-8') as f:
                        f.write(css_content)
                    css_files.append(filename)
                    logger.info(f"✅ Extracted inline CSS: {filename}")
                    
                    # Заменяем <style> на <link>
                    new_link = soup.new_tag('link', rel='stylesheet', href=f"css/{filename}")
                    style.replace_with(new_link)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to save inline CSS {filename}: {e}")
        
        logger.info("📜 Processing inline JavaScript...")
        js_files = []
        
        # Обрабатываем inline <script> теги
        script_tags = soup.find_all('script')
        for i, script in enumerate(script_tags):
            if not script.get('src') and script.get_text():
                js_content = script.get_text()
                if js_content.strip():
                    filename = f"inline_{i+1}.js"
                    js_file_path = js_path / filename
                    
                    try:
                        with open(js_file_path, 'w', encoding='utf-8') as f:
                            f.write(js_content)
                        js_files.append(filename)
                        logger.info(f"✅ Extracted inline JS: {filename}")
                        
                        # Заменяем inline script на external
                        new_script = soup.new_tag('script', src=f"js/{filename}")
                        script.replace_with(new_script)
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to save inline JS {filename}: {e}")
    
    def _process_external_files(self, soup, css_path, js_path, images_path, base_url):
        """Обрабатывает внешние файлы с фильтрацией доменов"""
        css_files = []
        js_files = []
        img_files = []
        
        base_domain = urlparse(base_url).netloc
        
        # Обрабатываем CSS файлы
        logger.info("🎨 Processing CSS files...")
        css_links = soup.find_all('link', rel='stylesheet')
        
        for link in css_links:
            href = link.get('href')
            if not href:
                continue
            
            # Создаем полный URL
            if href.startswith('http') or href.startswith('//'):
                css_url = href
                if href.startswith('//'):
                    css_url = f"https:{href}"
            else:
                css_url = urljoin(base_url, href)
            
            # Проверяем домен для внешних файлов
            if not self.download_external:
                parsed_url = urlparse(css_url)
                if parsed_url.netloc != base_domain:
                    logger.info(f"⏭️ Skipping external CSS: {css_url}")
                    continue
            
            # Извлекаем имя файла
            css_filename = self.extract_resource_name(css_url, 'css')
            css_file_path = css_path / css_filename
            
            # Скачиваем CSS
            css_response = self.download_resource_with_retry(css_url, 'css')
            
            if css_response:
                try:
                    with open(css_file_path, 'w', encoding='utf-8') as f:
                        f.write(css_response.text)
                    css_files.append(css_filename)
                    logger.info(f"✅ Downloaded CSS: {css_filename}")
                    
                    # Обновляем путь в HTML
                    link['href'] = f"css/{css_filename}"
                    
                except Exception as e:
                    logger.error(f"❌ Failed to save CSS {css_filename}: {e}")
            else:
                logger.warning(f"❌ Failed to download CSS: {css_url}")
        
        # Обрабатываем JS файлы
        logger.info("📜 Processing JavaScript files...")
        scripts = soup.find_all('script', src=True)
        
        for script in scripts:
            src = script.get('src')
            if not src:
                continue
            
            # Создаем полный URL
            if src.startswith('http') or src.startswith('//'):
                js_url = src
                if src.startswith('//'):
                    js_url = f"https:{src}"
            else:
                js_url = urljoin(base_url, src)
            
            # Проверяем домен для внешних файлов
            if not self.download_external:
                parsed_url = urlparse(js_url)
                if parsed_url.netloc != base_domain:
                    logger.info(f"⏭️ Skipping external JS: {js_url}")
                    continue
            
            # Извлекаем имя файла
            js_filename = self.extract_resource_name(js_url, 'js')
            js_file_path = js_path / js_filename
            
            # Скачиваем JS
            js_response = self.download_resource_with_retry(js_url, 'js')
            
            if js_response:
                try:
                    with open(js_file_path, 'w', encoding='utf-8') as f:
                        f.write(js_response.text)
                    js_files.append(js_filename)
                    logger.info(f"✅ Downloaded JS: {js_filename}")
                    
                    # Обновляем путь в HTML
                    script['src'] = f"js/{js_filename}"
                    
                except Exception as e:
                    logger.error(f"❌ Failed to save JS {js_filename}: {e}")
            else:
                logger.warning(f"❌ Failed to download JS: {js_url}")
        
        # Обрабатываем изображения
        logger.info("🖼️ Processing images...")
        images = soup.find_all('img', src=True)
        
        for img in images:
            src = img.get('src')
            if not src:
                continue
            
            # Пропускаем data URLs и blob URLs
            if src.startswith('data:') or src.startswith('blob:'):
                continue
            
            # Создаем полный URL
            if src.startswith('http') or src.startswith('//'):
                img_url = src
                if src.startswith('//'):
                    img_url = f"https:{src}"
            else:
                img_url = urljoin(base_url, src)
            
            # Проверяем домен для внешних файлов
            if not self.download_external:
                parsed_url = urlparse(img_url)
                if parsed_url.netloc != base_domain:
                    logger.info(f"⏭️ Skipping external image: {img_url}")
                    continue
            
            # Извлекаем имя файла
            img_filename = self.extract_resource_name(img_url, 'img')
            img_file_path = images_path / img_filename
            
            # Скачиваем изображение
            img_response = self.download_resource_with_retry(img_url, 'img')
            
            if img_response:
                try:
                    with open(img_file_path, 'wb') as f:
                        f.write(img_response.content)
                    img_files.append(img_filename)
                    logger.info(f"✅ Downloaded image: {img_filename}")
                    
                    # Обновляем путь в HTML
                    img['src'] = f"images/{img_filename}"
                    
                except Exception as e:
                    logger.error(f"❌ Failed to save image {img_filename}: {e}")
            else:
                logger.warning(f"❌ Failed to download image: {img_url}")
        
        return css_files, js_files, img_files
    
    def _analyze_wix_components(self, soup, images_path, base_url):
        """Анализирует Wix компоненты и извлекает изображения"""
        logger.info("🔍 Analyzing Wix components...")
        
        # Ищем JSON с данными Wix
        site_root_script = soup.find('script', {'id': 'site-root'})
        if site_root_script:
            try:
                # Пробуем извлечь JSON из соседних скриптов
                scripts_with_json = soup.find_all('script', type='application/json')
                for script in scripts_with_json:
                    try:
                        data = json.loads(script.get_text())
                        self._extract_wix_images(data, images_path, base_url)
                    except json.JSONDecodeError:
                        continue
                
                # Ищем Wix данные в других скриптах
                all_scripts = soup.find_all('script')
                for script in all_scripts:
                    script_text = script.get_text()
                    if 'WPhoto' in script_text or 'wix' in script_text.lower():
                        # Пробуем найти JSON в тексте скрипта
                        json_matches = re.findall(r'\{[^{}]*"WPhoto"[^{}]*\}', script_text, re.DOTALL)
                        for match in json_matches:
                            try:
                                data = json.loads(match)
                                self._extract_wix_images(data, images_path, base_url)
                            except json.JSONDecodeError:
                                continue
                
            except Exception as e:
                logger.warning(f"⚠️ Error analyzing Wix components: {e}")
    
    def _extract_wix_images(self, data, images_path, base_url):
        """Извлекает изображения из Wix JSON данных"""
        try:
            if isinstance(data, dict):
                # Рекурсивно ищем изображения
                for key, value in data.items():
                    if key == 'WPhoto' or 'image' in key.lower():
                        if isinstance(value, dict) and 'src' in value:
                            img_src = value['src']
                            if img_src and not img_src.startswith('data:'):
                                self._download_wix_image(img_src, images_path, base_url)
                    elif isinstance(value, (dict, list)):
                        self._extract_wix_images(value, images_path, base_url)
            elif isinstance(data, list):
                for item in data:
                    self._extract_wix_images(item, images_path, base_url)
                    
        except Exception as e:
            logger.warning(f"⚠️ Error extracting Wix images: {e}")
    
    def _download_wix_image(self, img_src, images_path, base_url):
        """Скачивает изображение из Wix"""
        try:
            # Создаем полный URL
            if img_src.startswith('http') or img_src.startswith('//'):
                img_url = img_src
                if img_src.startswith('//'):
                    img_url = f"https:{img_src}"
            else:
                img_url = urljoin(base_url, img_src)
            
            # Извлекаем имя файла
            img_filename = self.extract_resource_name(img_url, 'img')
            img_file_path = images_path / img_filename
            
            # Проверяем, не скачано ли уже
            if not img_file_path.exists():
                img_response = self.download_resource_with_retry(img_url, 'img')
                
                if img_response:
                    with open(img_file_path, 'wb') as f:
                        f.write(img_response.content)
                    logger.info(f"✅ Downloaded Wix image: {img_filename}")
                else:
                    logger.warning(f"❌ Failed to download Wix image: {img_url}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error downloading Wix image {img_src}: {e}")
    
    def _copy_subpages(self, soup, base_url, subpages_path, depth):
        """Рекурсивно копирует подстраницы"""
        logger.info(f"🔄 Copying subpages (depth {depth})...")
        subpages = []
        
        # Находим все внутренние ссылки
        links = soup.find_all('a', href=True)
        base_domain = urlparse(base_url).netloc
        processed_urls = set()
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
            
            # Создаем полный URL
            if href.startswith('http'):
                page_url = href
            elif href.startswith('//'):
                page_url = f"https:{href}"
            else:
                page_url = urljoin(base_url, href)
            
            # Пропускаем внешние и уже обработанные ссылки
            parsed = urlparse(page_url)
            if parsed.netloc != base_domain:
                continue
            
            if page_url in processed_urls or page_url == base_url:
                continue
            
            processed_urls.add(page_url)
            
            # Создаем имя файла для подстраницы
            page_name = parsed.path.strip('/').replace('/', '_') or 'index'
            if not page_name.endswith('.html'):
                page_name += '.html'
            
            # Копируем подстраницу
            try:
                subpage_result = self.copy_site(page_url, 
                                              output_dir=str(subpages_path / page_name.replace('.html', '')),
                                              depth=1)
                
                if subpage_result['success']:
                    subpages.append(page_name)
                    logger.info(f"✅ Copied subpage: {page_name}")
                else:
                    logger.warning(f"❌ Failed to copy subpage: {page_url}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error copying subpage {page_url}: {e}")
        
        return subpages
    
    def copy_site_recursive(self, url, output_dir=None, max_depth=3):
        """Рекурсивное копирование сайта с настройкой глубины"""
        return self.copy_site(url, output_dir, depth=max_depth)

# Функция для использования в агенте
def copy_site_fixed(url, output_dir=None):
    """Исправленное копирование сайта"""
    copier = SiteCopier()
    return copier.copy_site(url, output_dir)

if __name__ == "__main__":
    # Тестирование
    copier = SiteCopier()
    result = copier.copy_site("https://www.aksan.ua/")
    print(result)
