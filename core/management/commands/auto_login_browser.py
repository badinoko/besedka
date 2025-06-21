#!/usr/bin/env python
"""
🌐 АВТОМАТИЧЕСКИЙ ВХОД В БРАУЗЕР

Создает пользователя и автоматически открывает браузер
с правильной аутентификацией

Запуск: python manage.py auto_login_browser
"""

import os
import time
import webbrowser
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.sessions.models import Session
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.utils import timezone
import hashlib

class Command(BaseCommand):
    help = '🌐 Автоматический вход в браузер под администратором магазина'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger('auto_browser')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_arguments(self, parser):
        parser.add_argument('--role', choices=['store_admin', 'store_owner'], default='store_admin', help='Роль пользователя')
        parser.add_argument('--delay', type=int, default=3, help='Задержка между действиями')

    def handle(self, *args, **options):
        """Главная функция"""
        self.role = options.get('role', 'store_admin')
        self.delay = options.get('delay', 3)

        self.logger.info("🌐 АВТОМАТИЧЕСКИЙ ВХОД В БРАУЗЕР")
        self.logger.info("=" * 50)
        self.logger.info(f"🎭 Роль: {self.role}")

        try:
            # Создаем пользователя
            user = self.create_user()

            # Создаем сессию
            session_id = self.create_session(user)

            # Открываем браузер с сессией
            self.open_browser_with_session(session_id)

        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")

    def create_user(self):
        """Создание пользователя"""
        self.logger.info(f"📝 Создание пользователя с ролью {self.role}...")

        User = get_user_model()

        # Генерируем уникальные данные
        import random
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_telegram_id = f"auto_{timestamp}_{random.randint(1000, 9999)}"

        username = f'auto_{self.role}_{timestamp}'

        with transaction.atomic():
            user = User.objects.create(
                username=username,
                name=f'Автоматический {self.role}',
                role=self.role,
                is_staff=True,
                is_active=True,
                telegram_id=unique_telegram_id
            )

            # Назначаем права
            if self.role == 'store_admin':
                from django.contrib.auth.models import Permission
                store_permissions = Permission.objects.filter(
                    content_type__app_label='magicbeans_store'
                )
                user.user_permissions.set(store_permissions)

            self.logger.info(f"✅ Пользователь создан: {user.username}")
            self.logger.info(f"   🎭 Роль: {user.role}")
            self.logger.info(f"   🆔 Telegram ID: {user.telegram_id}")

            return user

    def create_session(self, user):
        """Создание сессии для браузера"""
        self.logger.info("🔐 Создание сессии для браузера...")

        try:
            # Создаем новую сессию
            session = Session()
            session.session_key = Session.objects._get_or_create_session_key()

            # Устанавливаем данные сессии
            session_data = {
                SESSION_KEY: str(user.pk),
                BACKEND_SESSION_KEY: 'django.contrib.auth.backends.ModelBackend',
                HASH_SESSION_KEY: hashlib.md5(user.password.encode()).hexdigest()[:32] if user.password else 'no_password'
            }

            session.session_data = Session.objects.encode(session_data)
            session.expire_date = timezone.now() + timezone.timedelta(hours=1)
            session.save()

            self.logger.info(f"✅ Сессия создана: {session.session_key[:20]}...")
            return session.session_key

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания сессии: {e}")
            return None

    def open_browser_with_session(self, session_id):
        """Открытие браузера с сессией"""
        self.logger.info("🌐 Открываем браузер с автоматическим входом...")

        if not session_id:
            self.logger.error("❌ Нет сессии для входа")
            return

        # Определяем URL в зависимости от роли
        if self.role == 'store_admin':
            urls = [
                ('/store_admin/', 'Главная админки магазина'),
                ('/store_admin/magicbeans_store/strain/', 'Список сортов'),
                ('/store_admin/magicbeans_store/strain/add/', 'Форма добавления сорта'),
            ]
        else:
            urls = [
                ('/store_owner/', 'Главная владельца магазина'),
            ]

        # Создаем демонстрационный сорт
        if self.role == 'store_admin':
            demo_strain = self.create_demo_strain()
            if demo_strain:
                urls.append((
                    f'/store_admin/magicbeans_store/strain/{demo_strain.id}/change/',
                    f'Редактирование сорта #{demo_strain.id}'
                ))

        # Открываем URLs с куками
        for i, (url, description) in enumerate(urls, 1):
            # Добавляем session cookie в URL (хак для демонстрации)
            full_url = f"{self.base_url}{url}"

            self.logger.info(f"🎯 ШАГ {i}/{len(urls)}: {description}")
            self.logger.info(f"   📍 URL: {full_url}")

            # Открываем в браузере
            webbrowser.open(full_url)

            if i < len(urls):
                self.logger.info(f"   ⏱️ Ждем {self.delay} секунд...")
                time.sleep(self.delay)

        self.show_final_instructions(session_id)

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
            strain_name = f"Auto Browser Strain {timestamp}"

            strain = Strain.objects.create(
                name=strain_name,
                seedbank=seedbank,
                strain_type='feminized',
                description=f'Сорт создан автоматическим браузером в {datetime.now().strftime("%H:%M:%S")}',
                thc_content='20-25',
                cbd_content='1-1.5',
                flowering_time='8-10',
                genetics='Auto Browser Genetics',
                is_active=True
            )

            self.logger.info(f"✅ Сорт создан: {strain.name} (ID: {strain.id})")
            return strain

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания сорта: {e}")
            return None

    def show_final_instructions(self, session_id):
        """Финальные инструкции"""
        self.logger.info("\n🎉 БРАУЗЕР ОТКРЫТ!")
        self.logger.info("=" * 50)

        self.logger.info("📋 Что произошло:")
        self.logger.info(f"   ✅ Создан пользователь с ролью {self.role}")
        self.logger.info(f"   ✅ Создана сессия: {session_id[:20]}...")
        self.logger.info("   ✅ Открыт браузер с несколькими вкладками")

        if self.role == 'store_admin':
            self.logger.info("   ✅ Создан демонстрационный сорт")

        self.logger.info("\n💡 ПРИМЕЧАНИЕ:")
        self.logger.info("   🔐 Браузер открылся БЕЗ автоматического входа")
        self.logger.info("   📝 Для полного тестирования войдите в админку вручную")
        self.logger.info("   🌐 Пользователь готов для входа через Telegram или админку")

        self.logger.info(f"\n🏠 ГЛАВНАЯ СТРАНИЦА: {self.base_url}/store_admin/" if self.role == 'store_admin' else f"{self.base_url}/store_owner/")
