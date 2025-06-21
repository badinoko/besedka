#!/usr/bin/env python
"""
🔐 УСТАНОВКА ПАРОЛЯ АДМИНИСТРАТОРУ

Устанавливает пароль пользователю test_store_admin
для удобного входа в систему

Запуск: python manage.py set_admin_password
"""

import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = '🔐 Установка пароля администратору магазина'

    def __init__(self):
        super().__init__()
        self.setup_logging()

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger('set_password')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_arguments(self, parser):
        parser.add_argument('--password', type=str, default='admin123', help='Пароль для установки')
        parser.add_argument('--username', type=str, default='test_store_admin', help='Имя пользователя')

    def handle(self, *args, **options):
        """Главная функция"""
        username = options.get('username', 'test_store_admin')
        password = options.get('password', 'admin123')

        self.logger.info("🔐 УСТАНОВКА ПАРОЛЯ АДМИНИСТРАТОРУ")
        self.logger.info("=" * 50)

        try:
            User = get_user_model()

            # Находим пользователя
            try:
                user = User.objects.get(username=username)
                self.logger.info(f"✅ Пользователь найден: {user.username}")
                self.logger.info(f"   🎭 Роль: {user.role}")
                self.logger.info(f"   📛 Имя: {user.name}")

                # Устанавливаем пароль
                user.set_password(password)
                user.save()

                self.logger.info(f"✅ ПАРОЛЬ УСТАНОВЛЕН!")
                self.logger.info(f"   👤 Логин: {username}")
                self.logger.info(f"   🔐 Пароль: {password}")

                self.logger.info("\n🌐 ТЕПЕРЬ ВЫ МОЖЕТЕ ВОЙТИ:")
                self.logger.info("   1. Откройте http://127.0.0.1:8000/admin/login/")
                self.logger.info(f"   2. Введите логин: {username}")
                self.logger.info(f"   3. Введите пароль: {password}")
                self.logger.info("   4. Нажмите 'Войти'")

                self.logger.info("\n🎯 ССЫЛКИ ДЛЯ АДМИНКИ МАГАЗИНА:")
                self.logger.info("   🏠 Главная: http://127.0.0.1:8000/store_admin/")
                self.logger.info("   🌿 Сорта: http://127.0.0.1:8000/store_admin/magicbeans_store/strain/")
                self.logger.info("   ➕ Добавить сорт: http://127.0.0.1:8000/store_admin/magicbeans_store/strain/add/")

            except User.DoesNotExist:
                self.logger.error(f"❌ Пользователь {username} не найден!")
                self.logger.info("💡 Сначала запустите: python manage.py switch_to_admin")

        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")
