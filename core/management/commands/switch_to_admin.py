#!/usr/bin/env python
"""
🔄 ПЕРЕКЛЮЧЕНИЕ НА АДМИНИСТРАТОРА МАГАЗИНА

Создает временного администратора магазина для тестирования
и показывает инструкции для входа

Запуск: python manage.py switch_to_admin
"""

import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

class Command(BaseCommand):
    help = '🔄 Переключение на администратора магазина для тестирования'

    def __init__(self):
        super().__init__()
        self.setup_logging()

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger('switch_admin')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def handle(self, *args, **options):
        """Главная функция"""
        self.logger.info("🔄 ПЕРЕКЛЮЧЕНИЕ НА АДМИНИСТРАТОРА МАГАЗИНА")
        self.logger.info("=" * 60)

        try:
            # Создаем тестового администратора
            admin_user = self.create_test_admin()

            # Показываем инструкции
            self.show_instructions(admin_user)

        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")

    def create_test_admin(self):
        """Создание тестового администратора магазина"""
        self.logger.info("📝 Создание тестового администратора магазина...")

        User = get_user_model()

        # Генерируем уникальные данные
        import random
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_telegram_id = f"admin_{timestamp}_{random.randint(1000, 9999)}"

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username='test_store_admin',
                defaults={
                    'name': 'Тестовый Администратор Магазина',
                    'role': 'store_admin',
                    'is_staff': True,
                    'is_active': True,
                    'telegram_id': unique_telegram_id
                }
            )

            # Обновляем данные если пользователь уже существует
            if not created:
                user.role = 'store_admin'
                user.telegram_id = unique_telegram_id
                user.is_staff = True
                user.is_active = True
                user.save()

            # Назначаем права на магазин
            from django.contrib.auth.models import Permission
            store_permissions = Permission.objects.filter(
                content_type__app_label='magicbeans_store'
            )
            user.user_permissions.set(store_permissions)

            action = "создан" if created else "обновлен"
            self.logger.info(f"✅ Администратор {action}: {user.username}")
            self.logger.info(f"   🎭 Роль: {user.role}")
            self.logger.info(f"   🆔 Telegram ID: {user.telegram_id}")
            self.logger.info(f"   📜 Права: {user.user_permissions.count()} разрешений")

            return user

    def show_instructions(self, admin_user):
        """Показать инструкции для входа"""
        self.logger.info("\n🎯 ИНСТРУКЦИИ ДЛЯ ВХОДА")
        self.logger.info("=" * 60)

        self.logger.info("📋 Теперь вы можете войти как администратор магазина:")
        self.logger.info(f"   👤 Логин: {admin_user.username}")
        self.logger.info(f"   🎭 Роль: Администратор магазина")
        self.logger.info(f"   🔐 Telegram ID: {admin_user.telegram_id}")

        self.logger.info("\n🌐 ССЫЛКИ ДЛЯ ДОСТУПА:")
        self.logger.info("   🏠 Главная админки: http://127.0.0.1:8000/store_admin/")
        self.logger.info("   🌿 Сорта: http://127.0.0.1:8000/store_admin/magicbeans_store/strain/")
        self.logger.info("   ➕ Добавить сорт: http://127.0.0.1:8000/store_admin/magicbeans_store/strain/add/")

        self.logger.info("\n📝 КАК ВОЙТИ:")
        self.logger.info("   1. Откройте /admin/login/ в браузере")
        self.logger.info("   2. Войдите как владелец платформы (owner)")
        self.logger.info("   3. Перейдите в управление пользователями")
        self.logger.info("   4. Найдите пользователя 'test_store_admin'")
        self.logger.info("   5. Используйте функцию 'Войти как этот пользователь'")

        self.logger.info("\n💡 БЫСТРЫЙ ВХОД:")
        self.logger.info("   Или используйте Django shell:")
        self.logger.info("   from django.contrib.auth import get_user_model")
        self.logger.info("   User = get_user_model()")
        self.logger.info(f"   user = User.objects.get(username='{admin_user.username}')")

        self.logger.info("\n🎉 ГОТОВО!")
        self.logger.info("   Теперь кнопки и формы админки магазина должны работать!")
        self.logger.info("   Вы сможете создавать сорта через интерфейс!")

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Пересоздать пользователя с новыми данными'
        )
