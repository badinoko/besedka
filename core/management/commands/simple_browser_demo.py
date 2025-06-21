#!/usr/bin/env python
"""
🎭 ПРОСТАЯ ДЕМОНСТРАЦИЯ БРАУЗЕРА

Создает временный автологин и показывает реальную работу админки

Запуск: python manage.py simple_browser_demo
"""

import os
import time
import webbrowser
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
import random

class Command(BaseCommand):
    help = '🎭 Простая демонстрация браузера с автологином'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger('browser_demo')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=int, default=5, help='Задержка между действиями')

    def handle(self, *args, **options):
        """Главная функция"""
        self.delay = options.get('delay', 5)

        self.logger.info("🎭 ПРОСТАЯ ДЕМОНСТРАЦИЯ БРАУЗЕРА")
        self.logger.info("=" * 50)

        try:
            # Включаем режим тестирования
            self.enable_test_mode()

            # Создаем администратора
            admin = self.create_test_admin()

            # Показываем последовательность страниц
            self.demo_admin_workflow(admin)

            # Выключаем режим тестирования
            self.disable_test_mode()

        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")

    def enable_test_mode(self):
        """Включение режима тестирования"""
        self.logger.info("🔧 Включаем режим тестирования...")

        # Создаем специальный файл-флаг
        test_flag = os.path.join(settings.BASE_DIR, '.test_mode')
        with open(test_flag, 'w') as f:
            f.write('browser_demo_active')

        self.logger.info("✅ Режим тестирования включен")

    def disable_test_mode(self):
        """Выключение режима тестирования"""
        self.logger.info("🔧 Выключаем режим тестирования...")

        test_flag = os.path.join(settings.BASE_DIR, '.test_mode')
        if os.path.exists(test_flag):
            os.remove(test_flag)

        self.logger.info("✅ Режим тестирования выключен")

    def create_test_admin(self):
        """Создание тестового администратора"""
        self.logger.info("📝 Создание тестового администратора...")

        User = get_user_model()

        # Генерируем уникальный telegram_id
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_telegram_id = f"demo_{timestamp}_{random.randint(1000, 9999)}"

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username='demo_admin',
                defaults={
                    'name': 'Демо Администратор',
                    'role': 'store_admin',
                    'is_staff': True,
                    'is_active': True,
                    'telegram_id': unique_telegram_id
                }
            )

            # Обновляем telegram_id если пользователь уже существует
            if not created:
                user.telegram_id = unique_telegram_id
                user.save()

            from django.contrib.auth.models import Permission
            store_permissions = Permission.objects.filter(
                content_type__app_label='magicbeans_store'
            )
            user.user_permissions.set(store_permissions)

            action = "создан" if created else "обновлен"
            self.logger.info(f"✅ Администратор {action}: {user.username}")
            self.logger.info(f"   🆔 Telegram ID: {user.telegram_id}")

            return user

    def demo_admin_workflow(self, admin):
        """Демонстрация рабочего процесса администратора"""
        self.logger.info("\n🎬 НАЧИНАЕМ ДЕМОНСТРАЦИЮ РАБОЧЕГО ПРОЦЕССА")
        self.logger.info("-" * 50)

        # Список действий для демонстрации
        demo_steps = [
            {
                'url': '/admin/login/',
                'title': 'Страница входа Django Admin',
                'description': 'Стандартная страница входа Django'
            },
            {
                'url': '/store_admin/',
                'title': 'Главная страница админки магазина',
                'description': 'Панель управления магазином'
            },
            {
                'url': '/store_admin/magicbeans_store/',
                'title': 'Раздел управления магазином',
                'description': 'Все модели магазина'
            },
            {
                'url': '/store_admin/magicbeans_store/strain/',
                'title': 'Список сортов',
                'description': 'Управление сортами'
            },
            {
                'url': '/store_admin/magicbeans_store/strain/add/',
                'title': 'Форма создания сорта',
                'description': 'Добавление нового сорта'
            }
        ]

        # Создаем сорт заранее
        new_strain = self.create_demo_strain()

        if new_strain:
            demo_steps.append({
                'url': f'/store_admin/magicbeans_store/strain/{new_strain.id}/change/',
                'title': f'Редактирование сорта #{new_strain.id}',
                'description': f'Редактирование созданного сорта: {new_strain.name}'
            })

        # Выполняем демонстрацию
        for i, step in enumerate(demo_steps, 1):
            self.logger.info(f"\n🎯 ШАГ {i}/{len(demo_steps)}: {step['title']}")
            self.logger.info(f"   📋 {step['description']}")

            full_url = f"{self.base_url}{step['url']}"
            self.logger.info(f"   🌐 Открываем: {full_url}")

            webbrowser.open(full_url)

            if i < len(demo_steps):
                self.logger.info(f"   ⏱️ Ждем {self.delay} секунд до следующего шага...")
                time.sleep(self.delay)

        # Финальная статистика
        self.show_final_stats(new_strain)

    def create_demo_strain(self):
        """Создание демонстрационного сорта"""
        self.logger.info("🌿 Создаем демонстрационный сорт...")

        try:
            from magicbeans_store.models import SeedBank, Strain

            seedbank = SeedBank.objects.first()
            if not seedbank:
                self.logger.warning("⚠️ Нет сидбанков для создания сорта")
                return None

            timestamp = datetime.now().strftime("%H%M%S")
            strain_name = f"Demo Strain {timestamp}"

            strain = Strain.objects.create(
                name=strain_name,
                seedbank=seedbank,
                strain_type='regular',
                description=f'Демонстрационный сорт, созданный {datetime.now().strftime("%H:%M:%S")}',
                thc_content='15-20',
                cbd_content='0.5-1',
                flowering_time='8-10',
                genetics='Demo Genetics',
                is_active=True
            )

            self.logger.info(f"✅ Сорт создан: {strain.name} (ID: {strain.id})")
            return strain

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания сорта: {e}")
            return None

    def show_final_stats(self, new_strain):
        """Показ финальной статистики"""
        self.logger.info("\n📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        self.logger.info("-" * 50)

        try:
            from magicbeans_store.models import SeedBank, Strain

            seedbanks_count = SeedBank.objects.count()
            strains_count = Strain.objects.count()

            self.logger.info(f"🏪 Сидбанков в системе: {seedbanks_count}")
            self.logger.info(f"🌿 Сортов в системе: {strains_count}")

            if new_strain:
                self.logger.info(f"🆕 Новый сорт: {new_strain.name}")
                self.logger.info(f"🆔 ID нового сорта: {new_strain.id}")

        except Exception as e:
            self.logger.error(f"❌ Ошибка получения статистики: {e}")

        self.logger.info("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
        self.logger.info("💡 В браузере должны быть открыты страницы админки")
        self.logger.info("💡 Каждая страница открывается в новой вкладке")
        self.logger.info("💡 Вы можете изучить интерфейс админки")
