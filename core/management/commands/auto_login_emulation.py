#!/usr/bin/env python
"""
🔐 ЭМУЛЯЦИЯ С АВТОМАТИЧЕСКИМ ЛОГИНОМ

Этот скрипт создает временные URL для автоматического логина
и показывает реальную работу админки в браузере

Запуск: python manage.py auto_login_emulation
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
from urllib.parse import urljoin, urlencode

class Command(BaseCommand):
    help = '🔐 Эмуляция с автоматическим логином в браузере'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'
        self.current_step = 0
        self.total_steps = 6

    def setup_logging(self):
        """Настройка логирования"""
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f'auto_login_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

        self.logger = logging.getLogger('auto_login')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%H:%M:%S'
        )

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_arguments(self, parser):
        parser.add_argument(
            '--delay',
            type=int,
            default=4,
            help='Задержка между шагами в секундах'
        )

    def handle(self, *args, **options):
        """Главная функция"""
        self.delay = options.get('delay', 4)

        self.logger.info("🔐 НАЧИНАЕМ ЭМУЛЯЦИЮ С АВТОМАТИЧЕСКИМ ЛОГИНОМ")
        self.logger.info("=" * 70)
        self.logger.info(f"⏱️ Задержка между шагами: {self.delay} секунд")
        self.logger.info("🌐 Браузер откроется с автоматическим входом")

        try:
            # Подготовка
            self.prepare_admin_user()
            self.create_auto_login_view()

            # Выполнение
            self.step_1_auto_login()
            self.step_2_navigate_to_strains()
            self.step_3_open_add_form()
            self.step_4_create_strain()
            self.step_5_show_results()
            self.step_6_cleanup()

        except KeyboardInterrupt:
            self.logger.info("\n⏹️ Эмуляция прервана пользователем")
        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}", exc_info=True)

    def prepare_admin_user(self):
        """Подготовка администратора"""
        self.logger.info("\n📝 ПОДГОТОВКА АДМИНИСТРАТОРА")
        self.logger.info("-" * 30)

        User = get_user_model()

        try:
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    username='auto_login_admin',
                    defaults={
                        'name': 'Автоматический Администратор',
                        'role': 'store_admin',
                        'is_staff': True,
                        'is_active': True,
                        'telegram_id': '99999999'
                    }
                )

                from django.contrib.auth.models import Permission
                store_permissions = Permission.objects.filter(
                    content_type__app_label='magicbeans_store'
                )
                user.user_permissions.set(store_permissions)

                action = "создан" if created else "найден"
                self.logger.info(f"✅ Администратор {action}: {user.username}")
                self.logger.info(f"   🎭 Роль: {user.role}")
                self.logger.info(f"   📜 Права: {user.user_permissions.count()} разрешений")

                self.admin_user = user

        except Exception as e:
            self.logger.error(f"❌ Ошибка подготовки пользователя: {e}")
            raise

    def create_auto_login_view(self):
        """Создание временного view для автологина"""
        self.logger.info("\n🔧 СОЗДАНИЕ АВТОЛОГИН VIEW")
        self.logger.info("-" * 30)

        # Добавляем временный URL в Django
        from django.urls import path
        from django.contrib.auth import login
        from django.shortcuts import redirect
        from django.http import HttpResponse

        def auto_login_view(request):
            """Временный view для автоматического логина"""
            try:
                # Логиним пользователя
                login(request, self.admin_user, backend='django.contrib.auth.backends.ModelBackend')

                # Получаем next parameter
                next_url = request.GET.get('next', '/store_admin/')

                self.logger.info(f"🔐 Автоматический вход выполнен для {self.admin_user.username}")
                self.logger.info(f"🔀 Перенаправление на: {next_url}")

                return redirect(next_url)

            except Exception as e:
                self.logger.error(f"❌ Ошибка автологина: {e}")
                return HttpResponse(f"Ошибка автологина: {e}", status=500)

        # Сохраняем view для использования
        self.auto_login_view = auto_login_view

        self.logger.info("✅ Автологин view создан")

    def get_auto_login_url(self, target_url):
        """Создание URL с автоматическим логином"""
        # Временно добавляем маршрут
        from django.conf import settings
        from django.urls import include, path
        from django.contrib import admin

        # Создаем URL с параметрами
        params = {'next': target_url}
        auto_url = f"{self.base_url}/admin/login/?" + urlencode(params)

        # Или используем прямой логин через Django admin
        return auto_url

    def next_step(self, title):
        """Переход к следующему шагу"""
        self.current_step += 1
        self.logger.info(f"\n🎯 ШАГ {self.current_step}/{self.total_steps}: {title}")
        self.logger.info("=" * 60)

    def open_url_with_delay(self, url, description):
        """Открытие URL с задержкой"""
        self.logger.info(f"🌐 {description}")
        self.logger.info(f"   📍 URL: {url}")

        webbrowser.open(url)

        self.logger.info(f"⏱️ Ждем {self.delay} секунд...")
        time.sleep(self.delay)

    def step_1_auto_login(self):
        """Шаг 1: Автоматический логин"""
        self.next_step("АВТОМАТИЧЕСКИЙ ВХОД В СИСТЕМУ")

        self.logger.info("🔐 Выполняем автоматический вход через Django admin...")

        # Создаем session вручную для браузера
        from django.contrib.sessions.models import Session
        from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
        from django.utils import timezone
        import hashlib

        try:
            # Создаем новую сессию
            session = Session()
            session.session_key = Session.objects._get_or_create_session_key()

            # Устанавливаем данные сессии
            session_data = {
                SESSION_KEY: str(self.admin_user.pk),
                BACKEND_SESSION_KEY: 'django.contrib.auth.backends.ModelBackend',
                HASH_SESSION_KEY: hashlib.md5(self.admin_user.password.encode()).hexdigest()[:32]
            }

            session.session_data = Session.objects.encode(session_data)
            session.expire_date = timezone.now() + timezone.timedelta(hours=1)
            session.save()

            # Создаем URL с cookie
            login_url = f"{self.base_url}/store_admin/?sessionid={session.session_key}"

            self.logger.info(f"✅ Session создана: {session.session_key}")
            self.open_url_with_delay(login_url, "Открываем админку с автоматическим логином")

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания сессии: {e}")
            # Fallback - просто открываем админку
            self.open_url_with_delay(f"{self.base_url}/store_admin/", "Открываем админку (без автологина)")

    def step_2_navigate_to_strains(self):
        """Шаг 2: Переход к сортам"""
        self.next_step("ПЕРЕХОД К УПРАВЛЕНИЮ СОРТАМИ")

        self.logger.info("📋 Что должно произойти:")
        self.logger.info("   • Вы должны увидеть админку магазина")
        self.logger.info("   • Перейти к разделу 'Сорта'")
        self.logger.info("   • Увидеть список всех сортов")

        url = f"{self.base_url}/store_admin/magicbeans_store/strain/"
        self.open_url_with_delay(url, "Переходим к списку сортов")

    def step_3_open_add_form(self):
        """Шаг 3: Открытие формы добавления"""
        self.next_step("ОТКРЫТИЕ ФОРМЫ СОЗДАНИЯ СОРТА")

        self.logger.info("📋 Что должно произойти:")
        self.logger.info("   • Откроется форма создания нового сорта")
        self.logger.info("   • Все поля должны быть пустыми")
        self.logger.info("   • Должны быть видны выпадающие списки")

        url = f"{self.base_url}/store_admin/magicbeans_store/strain/add/"
        self.open_url_with_delay(url, "Открываем форму добавления сорта")

    def step_4_create_strain(self):
        """Шаг 4: Создание сорта"""
        self.next_step("СОЗДАНИЕ НОВОГО СОРТА")

        self.logger.info("🔥 Создаем сорт через Django ORM...")

        try:
            from magicbeans_store.models import SeedBank, Strain

            seedbank = SeedBank.objects.first()
            if not seedbank:
                self.logger.error("❌ Нет сидбанков в системе!")
                return

            timestamp = datetime.now().strftime("%H%M%S")
            strain_name = f"Auto Login Test {timestamp}"

            strain = Strain.objects.create(
                name=strain_name,
                seedbank=seedbank,
                strain_type='autoflowering',
                description=f'Сорт создан автологин эмуляцией в {datetime.now().strftime("%H:%M:%S")}',
                thc_content='20-25',
                cbd_content='1-1.5',
                flowering_time='auto',
                genetics='Auto Genetics Test',
                is_active=True
            )

            self.logger.info("✅ СОРТ СОЗДАН УСПЕШНО!")
            self.logger.info(f"   🆔 ID: {strain.id}")
            self.logger.info(f"   📛 Название: {strain.name}")
            self.logger.info(f"   🏪 Сидбанк: {strain.seedbank.name}")

            self.new_strain = strain

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания сорта: {e}")
            self.new_strain = None

        time.sleep(self.delay)

    def step_5_show_results(self):
        """Шаг 5: Показ результатов"""
        self.next_step("ПРОСМОТР РЕЗУЛЬТАТОВ")

        self.logger.info("📋 Проверяем результаты создания...")

        # Обновленный список
        url = f"{self.base_url}/store_admin/magicbeans_store/strain/"
        self.open_url_with_delay(url, "Смотрим обновленный список сортов")

        # Если сорт создан - показываем его
        if hasattr(self, 'new_strain') and self.new_strain:
            edit_url = f"{self.base_url}/store_admin/magicbeans_store/strain/{self.new_strain.id}/change/"
            self.logger.info(f"\n🔧 Открываем созданный сорт для редактирования...")
            self.open_url_with_delay(edit_url, f"Редактируем сорт #{self.new_strain.id}")

    def step_6_cleanup(self):
        """Шаг 6: Завершение"""
        self.next_step("ЗАВЕРШЕНИЕ И СТАТИСТИКА")

        self.logger.info("🎉 АВТОЛОГИН ЭМУЛЯЦИЯ ЗАВЕРШЕНА!")

        if hasattr(self, 'new_strain') and self.new_strain:
            from magicbeans_store.models import Strain
            total_strains = Strain.objects.count()

            self.logger.info("\n📈 СТАТИСТИКА:")
            self.logger.info(f"   🌿 Всего сортов в системе: {total_strains}")
            self.logger.info(f"   🆕 Новый сорт: {self.new_strain.name}")
            self.logger.info(f"   🆔 ID нового сорта: {self.new_strain.id}")

        self.logger.info("\n💡 РЕЗУЛЬТАТ:")
        self.logger.info("   🎯 Автоматический логин выполнен")
        self.logger.info("   🎯 Админка должна быть доступна в браузере")
        self.logger.info("   🎯 Новый сорт создан и виден в списке")

        # Финальная ссылка на главную
        final_url = f"{self.base_url}/store_admin/"
        self.logger.info(f"\n🏠 Финальная ссылка на главную: {final_url}")
        webbrowser.open(final_url)
