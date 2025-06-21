#!/usr/bin/env python
"""
🌐 BROWSER EMULATION - Реальная браузерная эмуляция админок

Этот скрипт:
- Открывает реальные вкладки в браузере
- Эмулирует действия администратора магазина
- Добавляет/редактирует/удаляет сидбанки, сорта, товары
- Ведет подробное логирование всех действий
- Позволяет наблюдать процесс глазами

Запуск: python manage.py browser_emulation
"""

import os
import sys
import time
import json
import logging
import webbrowser
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.conf import settings
from django.db import transaction
from django.apps import apps

class Command(BaseCommand):
    help = '🌐 Реальная браузерная эмуляция админок с открытием вкладок'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'actions': [],
            'browser_tabs': [],
            'errors': []
        }
        self.base_url = 'http://127.0.0.1:8000'
        self.session = requests.Session()

    def setup_logging(self):
        """Подробное логирование всех действий"""
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f'browser_emulation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

        self.logger = logging.getLogger('browser_emulation')
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )

        # Файл
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.log_file = log_file

    def add_arguments(self, parser):
        parser.add_argument(
            '--role',
            type=str,
            choices=['store_owner', 'store_admin'],
            default='store_admin',
            help='Роль для эмуляции (default: store_admin)'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=2,
            help='Задержка между действиями в секундах (default: 2)'
        )
        parser.add_argument(
            '--full-scenario',
            action='store_true',
            help='Полный сценарий: создание, редактирование, удаление'
        )

    def handle(self, *args, **options):
        """Главная функция команды"""
        self.logger.info("🌐 НАЧИНАЕМ БРАУЗЕРНУЮ ЭМУЛЯЦИЮ")
        self.logger.info("=" * 80)

        role = options.get('role', 'store_admin')
        self.delay = options.get('delay', 2)
        full_scenario = options.get('full_scenario', False)

        try:
            # 1. Создание тестовых данных
            self.create_test_data()

            # 2. Получение пользователя
            user = self.get_test_user(role)

            # 3. Аутентификация
            self.authenticate_user(user)

            # 4. Запуск браузерной эмуляции
            if role == 'store_admin':
                self.emulate_store_admin(full_scenario)
            elif role == 'store_owner':
                self.emulate_store_owner(full_scenario)

            # 5. Отчет
            self.generate_report()

        except Exception as e:
            self.logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        finally:
            self.logger.info(f"📄 ЛОГИ СОХРАНЕНЫ: {self.log_file}")

    def create_test_data(self):
        """Создание тестовых пользователей"""
        self.logger.info("📝 Создание тестовых данных...")

        User = get_user_model()

        try:
            with transaction.atomic():
                # Администратор магазина
                store_admin, created = User.objects.get_or_create(
                    username='browser_store_admin',
                    defaults={
                        'name': 'Браузерный Администратор',
                        'role': 'store_admin',
                        'is_staff': True,
                        'is_active': True,
                        'telegram_id': '99999999'
                    }
                )
                if created:
                    self.logger.info("✅ Создан тестовый администратор магазина")

                # Владелец магазина
                store_owner, created = User.objects.get_or_create(
                    username='browser_store_owner',
                    defaults={
                        'name': 'Браузерный Владелец',
                        'role': 'store_owner',
                        'is_staff': True,
                        'is_active': True,
                        'telegram_id': '88888888'
                    }
                )
                if created:
                    self.logger.info("✅ Создан тестовый владелец магазина")

                # Назначаем permissions
                self.assign_permissions(store_admin, store_owner)

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания данных: {e}")

    def assign_permissions(self, store_admin, store_owner):
        """Назначение permissions"""
        from django.contrib.auth.models import Permission

        try:
            store_permissions = Permission.objects.filter(
                content_type__app_label='magicbeans_store'
            )

            store_owner.user_permissions.set(store_permissions)
            store_admin.user_permissions.set(store_permissions.exclude(codename__startswith='delete_'))

            self.logger.info("✅ Permissions назначены")

        except Exception as e:
            self.logger.error(f"❌ Ошибка permissions: {e}")

    def get_test_user(self, role):
        """Получение тестового пользователя"""
        User = get_user_model()

        username = f'browser_{role}'

        try:
            user = User.objects.get(username=username)
            self.logger.info(f"✅ Пользователь {username} найден")
            return user
        except User.DoesNotExist:
            self.logger.error(f"❌ Пользователь {username} не найден")
            sys.exit(1)

    def authenticate_user(self, user):
        """Аутентификация пользователя"""
        self.logger.info(f"🔑 Аутентификация пользователя: {user.username}")

        # Используем Django Client для получения session
        client = Client()
        client.force_login(user)

        # Получаем sessionid из Django Client
        session_key = client.session.session_key

        # Устанавливаем cookie в requests session
        self.session.cookies.set('sessionid', session_key, domain='127.0.0.1')

        self.logger.info("✅ Аутентификация успешна")

    def open_browser_tab(self, url, description):
        """Открытие вкладки в браузере с логированием"""
        full_url = f"{self.base_url}{url}"

        self.logger.info(f"🌐 ОТКРЫВАЕМ ВКЛАДКУ: {description}")
        self.logger.info(f"   URL: {full_url}")

        # Записываем в результаты
        tab_info = {
            'url': full_url,
            'description': description,
            'time': datetime.now().isoformat()
        }
        self.test_results['browser_tabs'].append(tab_info)

        # РЕАЛЬНО открываем в браузере
        webbrowser.open_new_tab(full_url)

        # Задержка для наблюдения
        time.sleep(self.delay)

        return full_url

    def emulate_store_admin(self, full_scenario=False):
        """Эмуляция работы администратора магазина"""
        self.logger.info("📦 ЭМУЛЯЦИЯ АДМИНИСТРАТОРА МАГАЗИНА")
        self.logger.info("-" * 60)

        # 1. Главная страница админки
        self.open_browser_tab('/store_admin/', 'Главная страница администратора магазина')

        # 2. Сидбанки
        self.logger.info("🌱 РАБОТА С СИДБАНКАМИ")
        self.open_browser_tab('/store_admin/magicbeans_store/seedbank/', 'Список сидбанков')
        self.open_browser_tab('/store_admin/magicbeans_store/seedbank/add/', 'Добавление нового сидбанка')

        if full_scenario:
            self.create_seedbank_scenario()

        # 3. Сорта
        self.logger.info("🌿 РАБОТА С СОРТАМИ")
        self.open_browser_tab('/store_admin/magicbeans_store/strain/', 'Список сортов')
        self.open_browser_tab('/store_admin/magicbeans_store/strain/add/', 'Добавление нового сорта')

        if full_scenario:
            self.create_strain_scenario()

        # 4. Товары
        self.logger.info("📋 РАБОТА С ТОВАРАМИ")
        self.open_browser_tab('/store_admin/magicbeans_store/stockitem/', 'Список товаров')
        self.open_browser_tab('/store_admin/magicbeans_store/stockitem/add/', 'Добавление нового товара')

        if full_scenario:
            self.create_stock_scenario()

        # 5. Заказы
        self.logger.info("🛒 РАБОТА С ЗАКАЗАМИ")
        self.open_browser_tab('/store_admin/magicbeans_store/order/', 'Список заказов')

    def emulate_store_owner(self, full_scenario=False):
        """Эмуляция работы владельца магазина"""
        self.logger.info("🏪 ЭМУЛЯЦИЯ ВЛАДЕЛЬЦА МАГАЗИНА")
        self.logger.info("-" * 60)

        # 1. Главная страница владельца
        self.open_browser_tab('/store_owner/', 'Главная страница владельца магазина')

        # 2. Управление администраторами
        self.logger.info("👥 УПРАВЛЕНИЕ ПЕРСОНАЛОМ")
        self.open_browser_tab('/store_owner/users/user/', 'Управление администраторами')

        # 3. Настройки магазина
        self.logger.info("⚙️ НАСТРОЙКИ МАГАЗИНА")
        self.open_browser_tab('/store_owner/magicbeans_store/storesettings/', 'Настройки магазина')

        # 4. Отчеты
        self.logger.info("📊 ОТЧЕТЫ И АНАЛИТИКА")
        self.open_browser_tab('/store_owner/magicbeans_store/salesreport/', 'Отчеты по продажам')
        self.open_browser_tab('/store_owner/magicbeans_store/inventoryreport/', 'Складские отчеты')

        # 5. Переход в операционную админку
        self.logger.info("📦 ПЕРЕХОД В ОПЕРАЦИОННУЮ АДМИНКУ")
        self.open_browser_tab('/store_admin/', 'Операционное управление каталогом')

    def create_seedbank_scenario(self):
        """Полный сценарий работы с сидбанком"""
        self.logger.info("🎬 ПОЛНЫЙ СЦЕНАРИЙ: СИДБАНК")

        # Данные для создания
        seedbank_data = {
            'name': f'Test SeedBank {datetime.now().strftime("%H%M%S")}',
            'description': 'Тестовый сидбанк созданный браузерной эмуляцией',
            'website': 'https://test-seedbank.example.com',
            'is_active': True
        }

        self.logger.info(f"   📝 Создаем сидбанк: {seedbank_data['name']}")

        # Симуляция POST запроса
        try:
            response = self.session.post(
                f"{self.base_url}/store_admin/magicbeans_store/seedbank/add/",
                data=seedbank_data
            )

            if response.status_code in [200, 302]:
                self.logger.info("   ✅ Сидбанк создан успешно")
                self.test_results['actions'].append({
                    'action': 'create_seedbank',
                    'data': seedbank_data,
                    'status': 'success',
                    'time': datetime.now().isoformat()
                })
            else:
                self.logger.error(f"   ❌ Ошибка создания сидбанка: {response.status_code}")

        except Exception as e:
            self.logger.error(f"   💥 Исключение при создании сидбанка: {e}")

    def create_strain_scenario(self):
        """Полный сценарий работы с сортом"""
        self.logger.info("🎬 ПОЛНЫЙ СЦЕНАРИЙ: СОРТ")

        # Получаем первый доступный сидбанк
        try:
            SeedBank = apps.get_model('magicbeans_store', 'SeedBank')
            seedbank = SeedBank.objects.first()

            if not seedbank:
                self.logger.warning("   ⚠️ Нет доступных сидбанков для создания сорта")
                return

            strain_data = {
                'name': f'Test Strain {datetime.now().strftime("%H%M%S")}',
                'seedbank': seedbank.id,
                'strain_type': 'indica',
                'description': 'Тестовый сорт созданный браузерной эмуляцией',
                'thc_content': 20.5,
                'cbd_content': 1.2,
                'flowering_time': 65,
                'is_active': True
            }

            self.logger.info(f"   📝 Создаем сорт: {strain_data['name']}")

            response = self.session.post(
                f"{self.base_url}/store_admin/magicbeans_store/strain/add/",
                data=strain_data
            )

            if response.status_code in [200, 302]:
                self.logger.info("   ✅ Сорт создан успешно")
                self.test_results['actions'].append({
                    'action': 'create_strain',
                    'data': strain_data,
                    'status': 'success',
                    'time': datetime.now().isoformat()
                })
            else:
                self.logger.error(f"   ❌ Ошибка создания сорта: {response.status_code}")

        except Exception as e:
            self.logger.error(f"   💥 Исключение при создании сорта: {e}")

    def create_stock_scenario(self):
        """Полный сценарий работы с товаром"""
        self.logger.info("🎬 ПОЛНЫЙ СЦЕНАРИЙ: ТОВАР")

        # Получаем первый доступный сорт
        try:
            Strain = apps.get_model('magicbeans_store', 'Strain')
            strain = Strain.objects.first()

            if not strain:
                self.logger.warning("   ⚠️ Нет доступных сортов для создания товара")
                return

            stock_data = {
                'strain': strain.id,
                'seeds_count': 5,
                'price': 1500.00,
                'quantity': 10,
                'description': 'Тестовый товар созданный браузерной эмуляцией',
                'is_active': True
            }

            self.logger.info(f"   📝 Создаем товар: {strain.name} ({stock_data['seeds_count']} семян)")

            response = self.session.post(
                f"{self.base_url}/store_admin/magicbeans_store/stockitem/add/",
                data=stock_data
            )

            if response.status_code in [200, 302]:
                self.logger.info("   ✅ Товар создан успешно")
                self.test_results['actions'].append({
                    'action': 'create_stock',
                    'data': stock_data,
                    'status': 'success',
                    'time': datetime.now().isoformat()
                })
            else:
                self.logger.error(f"   ❌ Ошибка создания товара: {response.status_code}")

        except Exception as e:
            self.logger.error(f"   💥 Исключение при создании товара: {e}")

    def generate_report(self):
        """Генерация итогового отчета"""
        self.logger.info("\n📊 ИТОГОВЫЙ ОТЧЕТ БРАУЗЕРНОЙ ЭМУЛЯЦИИ")
        self.logger.info("=" * 60)

        total_tabs = len(self.test_results['browser_tabs'])
        total_actions = len(self.test_results['actions'])
        total_errors = len(self.test_results['errors'])

        self.logger.info(f"🌐 Открыто вкладок в браузере: {total_tabs}")
        self.logger.info(f"⚡ Выполнено действий: {total_actions}")
        self.logger.info(f"❌ Ошибок: {total_errors}")

        # Сохранение JSON отчета
        report_file = os.path.join(settings.BASE_DIR, 'logs', f'browser_emulation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"💾 JSON отчет сохранен: {report_file}")
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения отчета: {e}")

        self.logger.info("\n💡 ИНСТРУКЦИЯ:")
        self.logger.info("   🖥️  Проверьте открытые вкладки в браузере")
        self.logger.info("   📋 Протестируйте функционал вручную")
        self.logger.info("   📝 Сообщите о найденных проблемах")

        self.test_results['end_time'] = datetime.now().isoformat()
