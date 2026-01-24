"""
Website Builder для создания сайтов
"""

import os
import webbrowser
import subprocess
import threading
from typing import Dict, Any
from datetime import datetime

from .utils import logger


class WebsiteBuilder:
    """Создатель веб-сайтов с различными фреймворками"""
    
    def __init__(self, agent):
        self.agent = agent
        self.server_thread = None
        self.server_process = None
        self._original_dir = None
    
    def __del__(self):
        """Автоматически останавливает сервер при удалении объекта"""
        self.stop_server()
    
    def create_full_website(self, theme: str, pages_count: int = 5, framework: str = 'bootstrap', site_type: str = 'simple', **kwargs) -> Dict[str, Any]:
        """Создает полноценный многостраничный сайт с Bootstrap/Tailwind"""
        try:
            logger.info(f"Creating full website: theme={theme}, pages={pages_count}, framework={framework}")
            
            # Создаем директорию для сайта
            import os
            # Создаем папку для проектов если ее нет
            projects_dir = os.path.abspath("agent_projects")
            os.makedirs(projects_dir, exist_ok=True)
            
            # Создаем уникальное имя сайта
            clean_theme = theme.replace(" ", "_").replace("-", "_").lower()
            site_name = f"{clean_theme}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            site_dir = os.path.join(projects_dir, site_name)
            os.makedirs(site_dir, exist_ok=True)
            
            # Создаем структуру сайта
            pages = self._create_site_structure(theme, site_type, pages_count, framework)
            
            # Генерируем файлы
            created_files = []
            
            # Главная страница
            index_html = self._generate_html_content(theme, site_type, pages, framework)
            index_file = os.path.join(site_dir, 'index.html')
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(index_html)
            created_files.append(index_file)
            
            # CSS файл
            css_content = self._generate_css_content(theme, site_type, framework)
            css_file = os.path.join(site_dir, 'styles.css')
            with open(css_file, 'w', encoding='utf-8') as f:
                f.write(css_content)
            created_files.append(css_file)
            
            # JavaScript файл
            js_content = self._generate_js_content(theme, site_type)
            js_file = os.path.join(site_dir, 'script.js')
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write(js_content)
            created_files.append(js_file)
            
            # Дополнительные страницы
            for i, page in enumerate(pages[1:], 1):
                page_html = self._generate_page_content(theme, page, framework)
                page_file = os.path.join(site_dir, f"{page['filename']}.html")
                with open(page_file, 'w', encoding='utf-8') as f:
                    f.write(page_html)
                created_files.append(page_file)
            
            # Запускаем локальный сервер
            server_url = self._start_local_server(site_dir)
            
            # Открываем в браузере
            if server_url:
                webbrowser.open(server_url)
            
            return {
                'success': True,
                'site_name': site_name,
                'site_dir': site_dir,
                'created_files': created_files,
                'pages_count': len(pages),
                'framework': framework,
                'site_type': site_type,
                'server_url': server_url,
                'message': f'Создан сайт "{site_name}" с {len(pages)} страницами'
            }
            
        except Exception as e:
            logger.error(f"Error creating website: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Ошибка при создании сайта'
            }
    
    def _create_site_structure(self, theme: str, site_type: str, pages_count: int, framework: str) -> list:
        """Создает структуру страниц сайта"""
        
        # Базовые страницы
        base_pages = [
            {'name': 'Главная', 'filename': 'index', 'content': f'Добро пожаловать на сайт о {theme}'}
        ]
        
        # Дополнительные страницы в зависимости от типа сайта
        if site_type == 'ecommerce':
            additional_pages = [
                {'name': 'Каталог', 'filename': 'catalog', 'content': 'Наши товары'},
                {'name': 'Корзина', 'filename': 'cart', 'content': 'Ваша корзина'},
                {'name': 'Контакты', 'filename': 'contacts', 'content': 'Свяжитесь с нами'},
                {'name': 'Доставка', 'filename': 'delivery', 'content': 'Информация о доставке'},
                {'name': 'О нас', 'filename': 'about', 'content': 'О нашем магазине'},
                {'name': 'Акции', 'filename': 'promotions', 'content': 'Специальные предложения'},
                {'name': 'Помощь', 'filename': 'help', 'content': 'Центр помощи'}
            ]
        elif site_type == 'portfolio':
            additional_pages = [
                {'name': 'Портфолио', 'filename': 'portfolio', 'content': 'Мои работы'},
                {'name': 'Обо мне', 'filename': 'about', 'content': 'Об авторе'},
                {'name': 'Услуги', 'filename': 'services', 'content': 'Мои услуги'},
                {'name': 'Контакты', 'filename': 'contacts', 'content': 'Свяжитесь со мной'}
            ]
        elif site_type == 'blog':
            additional_pages = [
                {'name': 'Блог', 'filename': 'blog', 'content': 'Статьи и новости'},
                {'name': 'Обо мне', 'filename': 'about', 'content': 'Об авторе блога'},
                {'name': 'Контакты', 'filename': 'contacts', 'content': 'Свяжитесь со мной'}
            ]
        else:  # simple или full
            additional_pages = [
                {'name': 'О нас', 'filename': 'about', 'content': f'О проекте {theme}'},
                {'name': 'Услуги', 'filename': 'services', 'content': 'Наши услуги'},
                {'name': 'Контакты', 'filename': 'contacts', 'content': 'Контактная информация'}
            ]
        
        # Объединяем страницы
        all_pages = base_pages + additional_pages
        
        # Ограничиваем количество страниц
        return all_pages[:pages_count]
    
    def _generate_html_content(self, theme: str, site_type: str, pages: list, framework: str) -> str:
        """Генерирует HTML контент для главной страницы"""
        
        # Навигация
        nav_items = ""
        for page in pages:
            nav_items += f'            <li><a href="{page["filename"]}.html">{page["name"]}</a></li>\n'
        
        # CSS фреймворк
        if framework == 'bootstrap':
            css_link = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">'
            js_link = '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>'
        elif framework == 'tailwind':
            css_link = '<script src="https://cdn.tailwindcss.com"></script>'
            js_link = ''
        else:
            css_link = '<link rel="stylesheet" href="styles.css">'
            js_link = ''
        
        html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{theme.title()} - Сайт создан Agent S</title>
    {css_link}
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header class="bg-primary text-white py-3">
        <div class="container">
            <nav class="navbar navbar-expand-lg navbar-dark">
                <div class="container-fluid">
                    <a class="navbar-brand" href="index.html">{theme.title()}</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav ms-auto">
{nav_items}                        </ul>
                    </div>
                </div>
            </nav>
        </div>
    </header>

    <main class="container my-5">
        <section class="hero-section text-center py-5">
            <h1 class="display-4 fw-bold mb-4">Добро пожаловать на сайт о {theme}</h1>
            <p class="lead mb-4">Этот сайт был автоматически создан Agent S с использованием современных веб-технологий</p>
            <div class="mt-4">
                <a href="#about" class="btn btn-primary btn-lg me-3">Узнать больше</a>
                <a href="#contacts" class="btn btn-outline-light btn-lg">Связаться</a>
            </div>
        </section>

        <section id="about" class="py-5">
            <div class="row">
                <div class="col-lg-6">
                    <h2 class="mb-4">О проекте</h2>
                    <p>Это современный веб-сайт, созданный с помощью Agent S. Сайт использует {framework.title()} фреймворк для адаптивного дизайна.</p>
                    <p>Тип сайта: {site_type}</p>
                    <p>Количество страниц: {len(pages)}</p>
                </div>
                <div class="col-lg-6">
                    <h3 class="mb-3">Особенности</h3>
                    <ul class="list-unstyled">
                        <li>✅ Адаптивный дизайн</li>
                        <li>✅ Современные технологии</li>
                        <li>✅ SEO оптимизация</li>
                        <li>✅ Быстрая загрузка</li>
                    </ul>
                </div>
            </div>
        </section>

        <section id="features" class="py-5 bg-light">
            <div class="text-center mb-5">
                <h2>Возможности</h2>
                <p class="text-muted">Что делает этот сайт особенным</p>
            </div>
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <h5 class="card-title">🚀 Быстрый старт</h5>
                            <p class="card-text">Сайт создан автоматически и готов к использованию</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <h5 class="card-title">📱 Адаптивность</h5>
                            <p class="card-text">Отлично выглядит на всех устройствах</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <h5 class="card-title">🎨 Современный дизайн</h5>
                            <p class="card-text">Используются современные веб-технологии</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="bg-dark text-white py-4 mt-5">
        <div class="container text-center">
            <p>&copy; 2026 {theme.title()}. Создано с помощью Agent S.</p>
            <p class="mb-0">Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        </div>
    </footer>

    {js_link}
    <script src="script.js"></script>
</body>
</html>'''
        
        return html_content
    
    def _generate_css_content(self, theme: str, site_type: str, framework: str) -> str:
        """Генерирует CSS контент"""
        
        css_content = '''/* Дополнительные стили для сайта */
.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin: -20px -15px 0 -15px;
    padding: 80px 15px !important;
}

.card {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
}

.navbar-brand {
    font-weight: bold;
    font-size: 1.5rem;
}

.btn-lg {
    padding: 12px 30px;
    font-size: 1.1rem;
}

section {
    scroll-margin-top: 70px;
}

/* Анимации */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.hero-section h1,
.hero-section p {
    animation: fadeInUp 1s ease-out;
}

.hero-section p {
    animation-delay: 0.3s;
    animation-fill-mode: both;
}

/* Адаптивность */
@media (max-width: 768px) {
    .hero-section {
        padding: 60px 15px !important;
    }
    
    .display-4 {
        font-size: 2.5rem;
    }
    
    .btn-lg {
        padding: 10px 20px;
        font-size: 1rem;
    }
}

/* Специфичные стили для разных типов сайтов */
'''
        
        if site_type == 'ecommerce':
            css_content += '''
/* Стили для интернет-магазина */
.product-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    transition: all 0.3s ease;
}

.product-card:hover {
    border-color: #007bff;
    box-shadow: 0 4px 15px rgba(0,123,255,0.2);
}

.price {
    font-size: 1.5rem;
    font-weight: bold;
    color: #28a745;
}

.cart-badge {
    background-color: #dc3545;
    color: white;
    border-radius: 50%;
    padding: 2px 6px;
    font-size: 0.8rem;
}
'''
        elif site_type == 'portfolio':
            css_content += '''
/* Стили для портфолио */
.portfolio-item {
    position: relative;
    overflow: hidden;
    border-radius: 8px;
    margin-bottom: 20px;
}

.portfolio-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.portfolio-item:hover .portfolio-overlay {
    opacity: 1;
}

.skill-tag {
    background-color: #6c757d;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    margin: 2px;
}
'''
        elif site_type == 'blog':
            css_content += '''
/* Стили для блога */
.blog-post {
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 20px;
    margin-bottom: 30px;
}

.blog-post:last-child {
    border-bottom: none;
}

.post-meta {
    color: #6c757d;
    font-size: 0.9rem;
    margin-bottom: 10px;
}

.post-excerpt {
    color: #495057;
    line-height: 1.6;
}

.read-more {
    color: #007bff;
    text-decoration: none;
    font-weight: 500;
}

.read-more:hover {
    text-decoration: underline;
}
'''
        
        return css_content
    
    def _generate_js_content(self, theme: str, site_type: str) -> str:
        """Генерирует JavaScript контент"""
        
        js_content = f'''// JavaScript для сайта о {theme}
// Создан Agent S

document.addEventListener('DOMContentLoaded', function() {{
    console.log('Сайт о {theme} загружен успешно!');
    
    // Плавная прокрутка к якорям
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
        anchor.addEventListener('click', function (e) {{
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {{
                target.scrollIntoView({{
                    behavior: 'smooth',
                    block: 'start'
                }});
            }}
        }});
    }});
    
    // Анимация элементов при прокрутке
    const observerOptions = {{
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    }};
    
    const observer = new IntersectionObserver(function(entries) {{
        entries.forEach(entry => {{
            if (entry.isIntersecting) {{
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }}
        }});
    }}, observerOptions);
    
    // Наблюдаем за карточками
    document.querySelectorAll('.card').forEach(card => {{
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    }});
    
    // Дополнительная функциональность для разных типов сайтов
'''
        
        if site_type == 'ecommerce':
            js_content += '''
    // Функциональность для интернет-магазина
    let cart = [];
    
    function addToCart(productId, productName, price) {
        cart.push({
            id: productId,
            name: productName,
            price: price,
            quantity: 1
        });
        updateCartDisplay();
        showNotification('Товар добавлен в корзину!');
    }
    
    function updateCartDisplay() {
        const cartCount = document.querySelector('.cart-count');
        if (cartCount) {
            const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.textContent = totalItems;
        }
    }
    
    function showNotification(message) {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = 'alert alert-success position-fixed top-0 end-0 m-3';
        notification.style.zIndex = '9999';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Удаляем через 3 секунды
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
'''
        elif site_type == 'portfolio':
            js_content += '''
    // Функциональность для портфолио
    function filterPortfolio(category) {
        const items = document.querySelectorAll('.portfolio-item');
        items.forEach(item => {
            if (category === 'all' || item.dataset.category === category) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    // Лайтбокс для изображений
    document.querySelectorAll('.portfolio-item img').forEach(img => {
        img.addEventListener('click', function() {
            const lightbox = document.createElement('div');
            lightbox.className = 'lightbox';
            lightbox.innerHTML = `
                <div class="lightbox-content">
                    <img src="${this.src}" alt="${this.alt}">
                    <button class="lightbox-close">&times;</button>
                </div>
            `;
            document.body.appendChild(lightbox);
            
            lightbox.querySelector('.lightbox-close').addEventListener('click', () => {
                lightbox.remove();
            });
            
            lightbox.addEventListener('click', (e) => {
                if (e.target === lightbox) {
                    lightbox.remove();
                }
            });
        });
    });
'''
        elif site_type == 'blog':
            js_content += '''
    // Функциональность для блога
    function searchBlogPosts(query) {
        const posts = document.querySelectorAll('.blog-post');
        posts.forEach(post => {
            const title = post.querySelector('h3').textContent.toLowerCase();
            const content = post.querySelector('.post-excerpt').textContent.toLowerCase();
            const searchTerm = query.toLowerCase();
            
            if (title.includes(searchTerm) || content.includes(searchTerm)) {
                post.style.display = 'block';
            } else {
                post.style.display = 'none';
            }
        });
    }
    
    // Поиск по блогу
    const searchInput = document.querySelector('#blog-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchBlogPosts(e.target.value);
        });
    }
'''
        
        js_content += '''
});
'''
        
        return js_content
    
    def _generate_page_content(self, theme: str, page: dict, framework: str) -> str:
        """Генерирует контент для дополнительной страницы"""
        
        # CSS фреймворк
        if framework == 'bootstrap':
            css_link = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">'
        elif framework == 'tailwind':
            css_link = '<script src="https://cdn.tailwindcss.com"></script>'
        else:
            css_link = '<link rel="stylesheet" href="styles.css">'
        
        html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page['name']} - {theme.title()}</title>
    {css_link}
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header class="bg-primary text-white py-3">
        <div class="container">
            <nav class="navbar navbar-expand-lg navbar-dark">
                <div class="container-fluid">
                    <a class="navbar-brand" href="index.html">{theme.title()}</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                </div>
            </nav>
        </div>
    </header>

    <main class="container my-5">
        <section class="py-5">
            <h1 class="display-4 fw-bold mb-4">{page['name']}</h1>
            <div class="row">
                <div class="col-lg-8">
                    <p class="lead">{page['content']}</p>
                    <p>Это страница {page['name'].lower()} сайта о {theme}. Здесь размещается соответствующая информация.</p>
                    
                    <div class="mt-4">
                        <h3>Дополнительная информация</h3>
                        <p>Здесь может быть более подробная информация о {page['name'].lower()}.</p>
                        <ul>
                            <li>Особенность 1</li>
                            <li>Особенность 2</li>
                            <li>Особенность 3</li>
                        </ul>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Навигация</h5>
                        </div>
                        <div class="card-body">
                            <a href="index.html" class="btn btn-outline-primary d-block mb-2">Главная</a>
                            <button class="btn btn-secondary d-block" onclick="history.back()">Назад</button>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="bg-dark text-white py-4 mt-5">
        <div class="container text-center">
            <p>&copy; 2026 {theme.title()}. Создано с помощью Agent S.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''
        
        return html_content
    
    def _start_local_server(self, directory: str) -> str:
        """Запускает локальный HTTP сервер"""
        try:
            import http.server
            import socketserver
            import random
            import os
            import threading
            
            # Выбираем случайный порт
            port = random.randint(8000, 9000)
            
            # Сохраняем оригинальную директорию
            original_dir = os.getcwd()
            self._original_dir = original_dir
            
            # Проверяем существование директории
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Переходим в директорию сайта
            os.chdir(directory)
            
            # Создаем сервер с правильной директорией
            handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("", port), handler)
            
            # Запускаем в отдельном потоке
            def run_server():
                try:
                    print(f"🌐 Сервер запущен: http://localhost:{port}")
                    print(f"📁 Директория: {os.getcwd()}")
                    httpd.serve_forever()
                except Exception as e:
                    print(f"Ошибка сервера: {e}")
                finally:
                    # Возвращаемся в исходную директорию
                    if hasattr(self, '_original_dir') and self._original_dir:
                        os.chdir(self._original_dir)
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            self.server_thread = server_thread
            self.server_process = httpd
            
            return f"http://localhost:{port}"
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            # Возвращаемся в исходную директорию при ошибке
            if hasattr(self, '_original_dir') and self._original_dir:
                os.chdir(self._original_dir)
            return None
    
    def stop_server(self):
        """Останавливает локальный сервер"""
        if self.server_process:
            try:
                # Останавливаем сервер
                self.server_process.shutdown()
                self.server_process.server_close()
                print("🛑 Сервер остановлен")
                
                # Возвращаемся в исходную директорию
                import os
                if hasattr(self, '_original_dir') and self._original_dir:
                    os.chdir(self._original_dir)
                    self._original_dir = None
                
                # Очищаем ссылки
                self.server_process = None
                self.server_thread = None
                
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
                # Принудительно возвращаемся в исходную директорию
                import os
                if hasattr(self, '_original_dir') and self._original_dir:
                    try:
                        os.chdir(self._original_dir)
                    except:
                        pass
                    self._original_dir = None
