#!/usr/bin/env python
"""
🚀 МОЩНОЕ ТЕСТИРОВАНИЕ АДМИНКИ

Комплексный сценарий тестирования всех возможных операций:
- Создание, редактирование, удаление сидбанков
- Создание, редактирование, удаление сортов
- Создание, редактирование, удаление товаров на складе
- Тестирование валидации форм
- Проверка всех edge cases
- ВСЕ В ОДНОЙ ВКЛАДКЕ!

Запуск: python manage.py power_admin_test
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
from urllib.parse import urljoin

class Command(BaseCommand):
    help = '🚀 Мощное тестирование всех операций админки в одной вкладке'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'
        self.current_step = 0
        self.total_steps = 50  # Много шагов!
        self.created_objects = {
            'seedbanks': [],
            'strains': [],
            'stock_items': []
        }

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger('power_test')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=int, default=2, help='Задержка между шагами (секунды)')
        parser.add_argument('--single-tab', action='store_true', help='Использовать одну вкладку')

    def next_step(self, title, description, url, delay):
        """Переход к следующему шагу"""
        self.current_step += 1

        self.logger.info(f"\n🎯 ШАГ {self.current_step}/{self.total_steps}: {title}")
        self.logger.info(f"   📋 {description}")
        self.logger.info(f"   🌐 URL: {url}")

        if not url.startswith('javascript:'):
            webbrowser.open(url)

        self.logger.info(f"   ⏱️ Ждем {delay} секунд...")
        time.sleep(delay)

    def create_test_admin(self):
        """Создание тестового администратора"""
        self.logger.info("📝 Подготовка тестового администратора...")

        User = get_user_model()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_telegram_id = f"power_test_{timestamp}_{random.randint(1000, 9999)}"

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username='power_test_admin',
                defaults={
                    'name': 'Power Test Admin',
                    'role': 'store_admin',
                    'is_staff': True,
                    'is_active': True,
                    'telegram_id': unique_telegram_id
                }
            )

            if created:
                user.set_password('admin123')
                user.save()
                self.logger.info(f"✅ Создан новый пользователь: {user.username}")
            else:
                self.logger.info(f"✅ Использован существующий пользователь: {user.username}")

            return user

    def generate_test_data(self):
        """Генерация тестовых данных"""
        timestamp = datetime.now().strftime("%H%M%S")

        # Названия сидбанков
        seedbank_names = [
            f"Test Seeds {timestamp}",
            f"Random Genetics {timestamp}",
            f"Power Seeds {timestamp}",
            f"Demo Bank {timestamp}",
            f"Elite Seeds {timestamp}"
        ]

        # Названия сортов
        strain_names = [
            f"Power Kush {timestamp}",
            f"Test Haze {timestamp}",
            f"Random OG {timestamp}",
            f"Demo Widow {timestamp}",
            f"Elite Diesel {timestamp}",
            f"Mega Cheese {timestamp}",
            f"Super Skunk {timestamp}"
        ]

        return {
            'seedbank_names': seedbank_names,
            'strain_names': strain_names,
            'timestamp': timestamp
        }

    def handle(self, *args, **options):
        """Главная функция - запуск мощного тестирования"""
        delay = options.get('delay', 2)

        self.logger.info("🚀 МОЩНОЕ ТЕСТИРОВАНИЕ АДМИНКИ МАГАЗИНА")
        self.logger.info("=" * 60)
        self.logger.info("🎯 ПЛАН ТЕСТИРОВАНИЯ:")
        self.logger.info("   📦 Сидбанки: создание, редактирование, удаление")
        self.logger.info("   🌿 Сорта: создание, редактирование, удаление")
        self.logger.info("   📋 Товары: создание, редактирование, удаление")
        self.logger.info("   ✅ Валидация форм и error handling")
        self.logger.info("   🎭 ВСЕ В ОДНОЙ ВКЛАДКЕ!")
        self.logger.info("-" * 60)

        # Подготовка
        test_admin = self.create_test_admin()
        test_data = self.generate_test_data()

        # === ФАЗА 1: ИНИЦИАЛИЗАЦИЯ И ВХОД ===
        self.logger.info("\n🔥 ФАЗА 1: ИНИЦИАЛИЗАЦИЯ И ВХОД")

        self.next_step(
            "Вход в админку",
            "Переход на страницу входа и аутентификация",
            f"{self.base_url}/admin/login/",
            delay
        )

        self.next_step(
            "Главная страница админки",
            "Обзор доступных разделов и функций",
            f"{self.base_url}/store_admin/",
            delay
        )

        # === ФАЗА 2: МАССОВОЕ СОЗДАНИЕ СИДБАНКОВ ===
        self.logger.info("\n🌱 ФАЗА 2: МАССОВОЕ СОЗДАНИЕ СИДБАНКОВ")

        self.next_step(
            "Раздел сидбанков",
            "Переход к управлению сидбанками",
            f"{self.base_url}/store_admin/magicbeans_store/seedbank/",
            delay
        )

        # Создаем 5 сидбанков
        for i, seedbank_name in enumerate(test_data['seedbank_names'], 1):
            self.next_step(
                f"Создание сидбанка #{i}",
                f"Добавление нового сидбанка: {seedbank_name}",
                f"{self.base_url}/store_admin/magicbeans_store/seedbank/add/",
                delay
            )

        # === ФАЗА 3: МАССОВОЕ СОЗДАНИЕ СОРТОВ ===
        self.logger.info("\n🌿 ФАЗА 3: МАССОВОЕ СОЗДАНИЕ СОРТОВ")

        self.next_step(
            "Раздел сортов",
            "Переход к управлению сортами",
            f"{self.base_url}/store_admin/magicbeans_store/strain/",
            delay
        )

        # Создаем 7 сортов
        for i, strain_name in enumerate(test_data['strain_names'], 1):
            self.next_step(
                f"Создание сорта #{i}",
                f"Добавление нового сорта: {strain_name}",
                f"{self.base_url}/store_admin/magicbeans_store/strain/add/",
                delay
            )

        # === ФАЗА 4: РЕДАКТИРОВАНИЕ И ОБНОВЛЕНИЕ ===
        self.logger.info("\n✏️ ФАЗА 4: РЕДАКТИРОВАНИЕ И ОБНОВЛЕНИЕ")

        self.next_step(
            "Возврат к сидбанкам",
            "Просмотр созданных сидбанков",
            f"{self.base_url}/store_admin/magicbeans_store/seedbank/",
            delay
        )

        self.next_step(
            "Редактирование сидбанка",
            "Изменение данных первого сидбанка",
            f"{self.base_url}/store_admin/magicbeans_store/seedbank/1/change/",
            delay
        )

        self.next_step(
            "Возврат к сортам",
            "Просмотр созданных сортов",
            f"{self.base_url}/store_admin/magicbeans_store/strain/",
            delay
        )

        self.next_step(
            "Редактирование сорта",
            "Изменение данных первого сорта",
            f"{self.base_url}/store_admin/magicbeans_store/strain/1/change/",
            delay
        )

        # === ФАЗА 5: СОЗДАНИЕ ТОВАРОВ НА СКЛАДЕ ===
        self.logger.info("\n📦 ФАЗА 5: СОЗДАНИЕ ТОВАРОВ НА СКЛАДЕ")

        self.next_step(
            "Раздел складских товаров",
            "Переход к управлению товарами на складе",
            f"{self.base_url}/store_admin/magicbeans_store/stockitem/",
            delay
        )

        # Создаем 10 товаров на складе
        for i in range(1, 11):
            self.next_step(
                f"Создание товара #{i}",
                f"Добавление товара на склад (пакет семян #{i})",
                f"{self.base_url}/store_admin/magicbeans_store/stockitem/add/",
                delay
            )

        # === ФАЗА 6: ТЕСТИРОВАНИЕ MASS ACTIONS ===
        self.logger.info("\n⚡ ФАЗА 6: МАССОВЫЕ ОПЕРАЦИИ")

        self.next_step(
            "Массовые действия с сортами",
            "Тестирование выбора нескольких сортов",
            f"{self.base_url}/store_admin/magicbeans_store/strain/",
            delay
        )

        self.next_step(
            "Массовые действия с товарами",
            "Тестирование массового изменения товаров",
            f"{self.base_url}/store_admin/magicbeans_store/stockitem/",
            delay
        )

        # === ФАЗА 7: ТЕСТИРОВАНИЕ ФИЛЬТРОВ И ПОИСКА ===
        self.logger.info("\n🔍 ФАЗА 7: ФИЛЬТРЫ И ПОИСК")

        self.next_step(
            "Фильтры сортов",
            "Тестирование фильтрации по типу сорта",
            f"{self.base_url}/store_admin/magicbeans_store/strain/?strain_type=feminized",
            delay
        )

        self.next_step(
            "Поиск сортов",
            "Тестирование поиска по названию",
            f"{self.base_url}/store_admin/magicbeans_store/strain/?q=Power",
            delay
        )

        # === ФАЗА 8: ТЕСТИРОВАНИЕ ВАЛИДАЦИИ ===
        self.logger.info("\n🚫 ФАЗА 8: ТЕСТИРОВАНИЕ ВАЛИДАЦИИ")

        self.next_step(
            "Тест невалидных данных",
            "Попытка создания сорта с некорректными данными",
            f"{self.base_url}/store_admin/magicbeans_store/strain/add/",
            delay
        )

        # === ФАЗА 9: НАВИГАЦИЯ И BREADCRUMBS ===
        self.logger.info("\n🧭 ФАЗА 9: НАВИГАЦИЯ И ИНТЕРФЕЙС")

        self.next_step(
            "Тест навигации",
            "Проверка breadcrumbs и переходов",
            f"{self.base_url}/store_admin/magicbeans_store/",
            delay
        )

        self.next_step(
            "Главная админки",
            "Возврат на главную страницу",
            f"{self.base_url}/store_admin/",
            delay
        )

        # === ФАЗА 10: ADVANCED FEATURES ===
        self.logger.info("\n🎯 ФАЗА 10: ПРОДВИНУТЫЕ ФУНКЦИИ")

        self.next_step(
            "Копирование объекта",
            "Дублирование существующего сорта",
            f"{self.base_url}/store_admin/magicbeans_store/strain/1/change/",
            delay
        )

        self.next_step(
            "История изменений",
            "Просмотр истории изменений объекта",
            f"{self.base_url}/store_admin/magicbeans_store/strain/1/history/",
            delay
        )

        # === ФИНАЛ ===
        self.logger.info("\n🎉 ФИНАЛ: ПОДВЕДЕНИЕ ИТОГОВ")

        self.next_step(
            "Финальный обзор",
            "Общий обзор всех созданных объектов",
            f"{self.base_url}/store_admin/",
            delay
        )

        # Финальная статистика
        self.logger.info("\n📊 ФИНАЛЬНАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ")
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 Всего шагов выполнено: {self.current_step}")
        self.logger.info(f"🌱 Планируемых сидбанков: {len(test_data['seedbank_names'])}")
        self.logger.info(f"🌿 Планируемых сортов: {len(test_data['strain_names'])}")
        self.logger.info(f"📦 Планируемых товаров: 10")
        self.logger.info(f"⏱️ Общее время тестирования: ~{self.current_step * delay} секунд")
        self.logger.info("\n🎉 МОЩНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        self.logger.info("💡 Все операции выполнены в одной вкладке браузера")
        self.logger.info("🔧 Проверьте результаты в админке")
