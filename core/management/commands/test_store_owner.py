#!/usr/bin/env python
"""
🏪 ТЕСТИРОВАНИЕ ВЛАДЕЛЬЦА МАГАЗИНА

Создает владельца магазина и тестирует его доступ
к обеим админкам: своей и администратора

Запуск: python manage.py test_store_owner
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
    help = '🏪 Создание и тестирование владельца магазина'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger('store_owner_test')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=int, default=3, help='Задержка между шагами (секунды)')

    def create_store_owner_guide_html(self):
        """Создание HTML-гида для тестирования владельца магазина"""
        timestamp = datetime.now().strftime("%H%M%S")

        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏪 Тестирование владельца магазина Magic Beans</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #ff7b7b 0%, #667eea 100%);
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
        .role-info {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 5px solid #ff6b6b;
            text-align: center;
        }}
        .dual-access {{
            display: flex;
            gap: 20px;
            margin: 30px 0;
        }}
        .admin-panel {{
            flex: 1;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        .admin-panel.strategic {{
            border-left: 5px solid #4CAF50;
        }}
        .admin-panel.operational {{
            border-left: 5px solid #2196F3;
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
        .nav-button.strategic {{
            background: linear-gradient(135deg, #ff6b6b, #ee5a52);
        }}
        .nav-button.strategic:hover {{
            background: linear-gradient(135deg, #ee5a52, #ff6b6b);
        }}
        .nav-button.operational {{
            background: linear-gradient(135deg, #2196F3, #1976D2);
        }}
        .nav-button.operational:hover {{
            background: linear-gradient(135deg, #1976D2, #2196F3);
        }}
        .test-scenario {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 5px solid #ff9800;
        }}
        .scenario-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .step {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #ffc107;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🏪 Тестирование владельца магазина</h1>
        <div class="subtitle">Проверка доступа к стратегической и операционной панелям</div>

        <div class="role-info">
            <h2>👑 Владелец магазина Magic Beans</h2>
            <p><strong>Уникальная роль:</strong> Доступ к ДВУМ админкам одновременно!</p>
            <p>🔐 <strong>Логин:</strong> <code>test_store_owner</code></p>
            <p>🔑 <strong>Пароль:</strong> <code>owner123</code></p>
        </div>

        <div class="dual-access">
            <div class="admin-panel strategic">
                <h3>🎯 Стратегическая панель</h3>
                <p><strong>Роль:</strong> Владелец магазина</p>
                <p><strong>Функции:</strong> Управление персоналом, настройки, отчеты</p>
                <a href="{self.base_url}/store_owner/" class="nav-button strategic">🏪 Панель владельца</a>
            </div>

            <div class="admin-panel operational">
                <h3>⚙️ Операционная панель</h3>
                <p><strong>Роль:</strong> Администратор магазина</p>
                <p><strong>Функции:</strong> Каталог, товары, заказы</p>
                <a href="{self.base_url}/store_admin/" class="nav-button operational">👨‍💼 Панель администратора</a>
            </div>
        </div>

        <div class="success">
            <strong>✅ Новая логика:</strong> Владелец магазина может переключаться между двумя панелями для полного контроля над бизнесом!
        </div>

        <div class="test-scenario">
            <div class="scenario-title">🎯 Сценарий тестирования</div>

            <div class="step">
                <strong>Шаг 1:</strong> Войдите в систему как владелец магазина
                <div style="margin-top: 10px;">
                    <a href="{self.base_url}/admin/login/" class="nav-button">🔐 Войти в систему</a>
                </div>
            </div>

            <div class="step">
                <strong>Шаг 2:</strong> Проверьте стратегическую панель (управление персоналом)
                <div style="margin-top: 10px;">
                    <a href="{self.base_url}/store_owner/" class="nav-button strategic">🎯 Стратегическая панель</a>
                </div>
            </div>

            <div class="step">
                <strong>Шаг 3:</strong> Переключитесь на операционную панель (управление каталогом)
                <div style="margin-top: 10px;">
                    <a href="{self.base_url}/store_admin/" class="nav-button operational">⚙️ Операционная панель</a>
                </div>
            </div>

            <div class="step">
                <strong>Шаг 4:</strong> Протестируйте создание сорта в операционной панели
                <div style="margin-top: 10px;">
                    <a href="{self.base_url}/store_admin/magicbeans_store/strain/add/" class="nav-button operational">🌿 Добавить сорт</a>
                </div>
            </div>

            <div class="step">
                <strong>Шаг 5:</strong> Вернитесь в стратегическую панель и проверьте настройки
                <div style="margin-top: 10px;">
                    <a href="{self.base_url}/store_owner/" class="nav-button strategic">🎯 Вернуться к стратегии</a>
                </div>
            </div>
        </div>

        <div class="warning">
            <strong>⚠️ Важно:</strong> Владелец магазина должен легко переключаться между панелями без ошибок доступа!
        </div>
    </div>
</body>
</html>
        """

        # Сохраняем HTML-файл
        guide_path = os.path.join(os.getcwd(), f'store_owner_test_{timestamp}.html')
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return guide_path

    def handle(self, *args, **options):
        """Главная функция"""
        delay = options.get('delay', 3)

        self.logger.info("🏪 СОЗДАНИЕ И ТЕСТИРОВАНИЕ ВЛАДЕЛЬЦА МАГАЗИНА")
        self.logger.info("=" * 60)

        # Создаем владельца магазина
        User = get_user_model()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username='test_store_owner',
                defaults={
                    'name': 'Test Store Owner',
                    'role': 'store_owner',
                    'is_staff': True,
                    'is_active': True,
                    'telegram_id': f"owner_{timestamp}"
                }
            )

            if created:
                user.set_password('owner123')
                user.save()
                self.logger.info(f"✅ Создан владелец: {user.username}")
            else:
                user.set_password('owner123')
                user.save()
                self.logger.info(f"✅ Обновлен владелец: {user.username}")

        # Создаем HTML-гид
        guide_path = self.create_store_owner_guide_html()
        self.logger.info(f"✅ Создан HTML-гид: {guide_path}")

        # Открываем гид в браузере
        file_url = f"file:///{guide_path.replace(os.path.sep, '/')}"
        webbrowser.open(file_url)

        self.logger.info(f"🌐 Открыт гид в браузере: {file_url}")

        self.logger.info("\n🎯 УНИКАЛЬНЫЕ ВОЗМОЖНОСТИ ВЛАДЕЛЬЦА:")
        self.logger.info("1. 🎯 Доступ к стратегической панели (/store_owner/)")
        self.logger.info("2. ⚙️ Доступ к операционной панели (/store_admin/)")
        self.logger.info("3. 🔄 Свободное переключение между панелями")
        self.logger.info("4. 👥 Управление администраторами магазина")
        self.logger.info("5. 🌿 Прямое управление каталогом и товарами")

        self.logger.info(f"\n🔐 ДАННЫЕ ДЛЯ ВХОДА:")
        self.logger.info(f"   👤 Логин: test_store_owner")
        self.logger.info(f"   🔐 Пароль: owner123")

        self.logger.info(f"\n🎉 ГОТОВО! Тестируйте обе панели!")
        self.logger.info(f"📋 Цель: убедиться что владелец имеет доступ к обеим админкам")
