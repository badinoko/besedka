#!/usr/bin/env python
"""
🎯 ТЕСТИРОВАНИЕ В ОДНОЙ ВКЛАДКЕ

Мощный сценарий тестирования который работает в ОДНОЙ вкладке
с пошаговыми инструкциями для пользователя

Запуск: python manage.py single_tab_test
"""

import os
import time
import webbrowser
import logging
import random
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

class Command(BaseCommand):
    help = '🎯 Мощное тестирование админки в одной вкладке'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger('single_tab_test')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=int, default=5, help='Задержка между шагами (секунды)')

    def create_test_guide_html(self):
        """Создание HTML-гида для тестирования"""
        timestamp = datetime.now().strftime("%H%M%S")

        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Гид по тестированию админки Magic Beans</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }}
        h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .subtitle {{
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 30px;
            opacity: 0.9;
        }}
        .phase {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 5px solid #4CAF50;
        }}
        .phase-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        .step {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #2196F3;
        }}
        .step-title {{
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 8px;
        }}
        .step-url {{
            background: rgba(0, 0, 0, 0.3);
            padding: 8px 12px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            margin: 8px 0;
            word-break: break-all;
        }}
        .nav-button {{
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            margin: 5px;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .nav-button:hover {{
            background: linear-gradient(135deg, #45a049, #4CAF50);
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }}
        .nav-button.admin {{
            background: linear-gradient(135deg, #2196F3, #1976D2);
        }}
        .nav-button.admin:hover {{
            background: linear-gradient(135deg, #1976D2, #2196F3);
        }}
        .quick-links {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .warning {{
            background: rgba(255, 193, 7, 0.2);
            border: 1px solid rgba(255, 193, 7, 0.5);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        .success {{
            background: rgba(76, 175, 80, 0.2);
            border: 1px solid rgba(76, 175, 80, 0.5);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        .info {{
            background: rgba(33, 150, 243, 0.2);
            border: 1px solid rgba(33, 150, 243, 0.5);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Гид по тестированию админки Magic Beans</h1>
        <div class="subtitle">Комплексное тестирование всех функций в одной вкладке</div>

        <div class="success">
            <strong>✅ Инструкция:</strong> Следуйте шагам последовательно, переходя по ссылкам в ТОЙ ЖЕ ВКЛАДКЕ (Ctrl+клик для новой вкладки НЕ используйте!)
        </div>

        <div class="quick-links">
            <h3>🎯 Быстрые переходы</h3>
            <a href="{self.base_url}/admin/login/" class="nav-button admin">🔐 Войти в админку</a>
            <a href="{self.base_url}/store_admin/" class="nav-button">🏠 Главная админки</a>
            <a href="{self.base_url}/store_admin/magicbeans_store/" class="nav-button">📦 Управление магазином</a>
        </div>

        <div class="info">
            <strong>📝 Данные для входа:</strong><br>
            👤 Логин: <code>test_store_admin</code><br>
            🔐 Пароль: <code>admin123</code>
        </div>

        <!-- ФАЗА 1: ВХОД И НАВИГАЦИЯ -->
        <div class="phase">
            <div class="phase-title">🔥 ФАЗА 1: Вход и базовая навигация</div>

            <div class="step">
                <div class="step-title">Шаг 1.1: Войдите в админку</div>
                <div>Перейдите на страницу входа и авторизуйтесь</div>
                <div class="step-url">
                    <a href="{self.base_url}/admin/login/" class="nav-button admin">🔐 Войти в систему</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 1.2: Главная страница админки</div>
                <div>Изучите доступные разделы и функции</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/" class="nav-button">🏠 Главная админки</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 1.3: Обзор управления магазином</div>
                <div>Посмотрите на все доступные модели</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/" class="nav-button">📦 Управление магазином</a>
                </div>
            </div>
        </div>

        <!-- ФАЗА 2: СИДБАНКИ -->
        <div class="phase">
            <div class="phase-title">🌱 ФАЗА 2: Работа с сидбанками</div>

            <div class="step">
                <div class="step-title">Шаг 2.1: Список сидбанков</div>
                <div>Просмотрите существующие сидбанки</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/seedbank/" class="nav-button">🌱 Сидбанки</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 2.2: Создайте новый сидбанк</div>
                <div>Добавьте сидбанк "Test Seeds {timestamp}"</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/seedbank/add/" class="nav-button">➕ Добавить сидбанк</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 2.3: Редактируйте сидбанк</div>
                <div>Измените данные первого сидбанка</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/seedbank/1/change/" class="nav-button">✏️ Редактировать первый</a>
                </div>
            </div>
        </div>

        <!-- ФАЗА 3: СОРТА -->
        <div class="phase">
            <div class="phase-title">🌿 ФАЗА 3: Работа с сортами</div>

            <div class="step">
                <div class="step-title">Шаг 3.1: Список сортов</div>
                <div>Просмотрите существующие сорта</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/strain/" class="nav-button">🌿 Сорта</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 3.2: Создайте новый сорт</div>
                <div>Добавьте сорт "Power Kush {timestamp}"</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/strain/add/" class="nav-button">➕ Добавить сорт</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 3.3: Редактируйте сорт</div>
                <div>Измените данные первого сорта</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/strain/1/change/" class="nav-button">✏️ Редактировать первый</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 3.4: Фильтрация сортов</div>
                <div>Протестируйте фильтр по типу сорта</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/strain/?strain_type=feminized" class="nav-button">🔍 Феминизированные</a>
                </div>
            </div>
        </div>

        <!-- ФАЗА 4: СКЛАДСКИЕ ТОВАРЫ -->
        <div class="phase">
            <div class="phase-title">📦 ФАЗА 4: Складские товары</div>

            <div class="step">
                <div class="step-title">Шаг 4.1: Список товаров</div>
                <div>Просмотрите товары на складе</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/stockitem/" class="nav-button">📋 Товары на складе</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 4.2: Добавьте товар</div>
                <div>Создайте новый товар на складе</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/stockitem/add/" class="nav-button">➕ Добавить товар</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 4.3: Редактируйте товар</div>
                <div>Измените данные первого товара</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/stockitem/1/change/" class="nav-button">✏️ Редактировать первый</a>
                </div>
            </div>
        </div>

        <!-- ФАЗА 5: ПРОДВИНУТЫЕ ФУНКЦИИ -->
        <div class="phase">
            <div class="phase-title">🎯 ФАЗА 5: Продвинутые функции</div>

            <div class="step">
                <div class="step-title">Шаг 5.1: История изменений</div>
                <div>Просмотрите историю изменений объекта</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/strain/1/history/" class="nav-button">📜 История сорта #1</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 5.2: Поиск по сортам</div>
                <div>Протестируйте поиск по названию</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/strain/?q=Power" class="nav-button">🔍 Поиск "Power"</a>
                </div>
            </div>

            <div class="step">
                <div class="step-title">Шаг 5.3: Массовые действия</div>
                <div>Выберите несколько сортов и выполните массовое действие</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/magicbeans_store/strain/" class="nav-button">⚡ Массовые действия</a>
                </div>
            </div>
        </div>

        <!-- ФИНАЛ -->
        <div class="phase">
            <div class="phase-title">🎉 ФИНАЛ: Завершение тестирования</div>

            <div class="step">
                <div class="step-title">Шаг 6.1: Финальный обзор</div>
                <div>Вернитесь на главную и оцените результаты</div>
                <div class="step-url">
                    <a href="{self.base_url}/store_admin/" class="nav-button">🏠 Главная админки</a>
                </div>
            </div>
        </div>

        <div class="warning">
            <strong>⚠️ Важно:</strong> Все переходы выполняйте в ЭТОЙ ВКЛАДКЕ! Не открывайте новые вкладки.
        </div>

        <div class="success">
            <strong>🎯 Цель тестирования:</strong> Убедиться что все функции работают корректно, формы сохраняются, навигация работает, и нет ошибок.
        </div>
    </div>
</body>
</html>
        """

        # Сохраняем HTML-файл
        guide_path = os.path.join(os.getcwd(), f'admin_test_guide_{timestamp}.html')
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return guide_path

    def handle(self, *args, **options):
        """Главная функция"""
        delay = options.get('delay', 5)

        self.logger.info("🎯 СОЗДАНИЕ ГИДА ПО ТЕСТИРОВАНИЮ В ОДНОЙ ВКЛАДКЕ")
        self.logger.info("=" * 60)

        # Создаем тестового пользователя
        User = get_user_model()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username='test_store_admin',
                defaults={
                    'name': 'Test Store Admin',
                    'role': 'store_admin',
                    'is_staff': True,
                    'is_active': True,
                    'telegram_id': f"test_{timestamp}"
                }
            )

            if created:
                user.set_password('admin123')
                user.save()
                self.logger.info(f"✅ Создан пользователь: {user.username}")
            else:
                self.logger.info(f"✅ Пользователь уже существует: {user.username}")

        # Создаем HTML-гид
        guide_path = self.create_test_guide_html()
        self.logger.info(f"✅ Создан HTML-гид: {guide_path}")

        # Открываем гид в браузере
        file_url = f"file:///{guide_path.replace(os.path.sep, '/')}"
        webbrowser.open(file_url)

        self.logger.info(f"🌐 Открыт гид в браузере: {file_url}")

        self.logger.info("\n🎯 ИНСТРУКЦИЯ:")
        self.logger.info("1. В открывшемся HTML-гиде следуйте инструкциям")
        self.logger.info("2. Переходите по ссылкам ПОСЛЕДОВАТЕЛЬНО")
        self.logger.info("3. Все переходы выполняйте в ОДНОЙ вкладке")
        self.logger.info("4. Тестируйте создание, редактирование, удаление")
        self.logger.info("5. Проверяйте что формы сохраняются корректно")

        self.logger.info(f"\n🔐 ДАННЫЕ ДЛЯ ВХОДА:")
        self.logger.info(f"   👤 Логин: test_store_admin")
        self.logger.info(f"   🔐 Пароль: admin123")

        self.logger.info(f"\n🎉 ГОТОВО! Следуйте инструкциям в HTML-гиде!")
