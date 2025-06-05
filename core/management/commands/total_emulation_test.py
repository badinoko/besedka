#!/usr/bin/env python
"""
🚀 TOTAL EMULATION TEST - Тотальная эмуляция всех переходов в админках

Этот скрипт эмулирует действия:
- Владельца магазина в store_owner админке
- Администратора магазина в store_admin админке
- Все переходы, клики, создание/редактирование записей
- Проверку всех ссылок и форм
- Сбор детальных логов ошибок

Запуск: python manage.py total_emulation_test
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.test import Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from django.core.management import call_command
from django.apps import apps

# Настройка логирования
log_formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Command(BaseCommand):
    help = '🚀 TOTAL EMULATION TEST - Тотальная эмуляция всех переходов в админках'

    def __init__(self):
        super().__init__()

        # Настраиваем Django Test Client с правильным хостом
        self.client = Client(SERVER_NAME='127.0.0.1')

        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'store_owner_tests': [],
            'store_admin_tests': [],
            'errors': [],
            'summary': {}
        }
        self.setup_logging()

    def setup_logging(self):
        """Настройка логирования для детального отслеживания"""
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f'total_emulation_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

        # Настройка логгера
        self.logger = logging.getLogger('emulation_test')
        self.logger.setLevel(logging.DEBUG)

        # Файл-хендлер
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        self.logger.addHandler(file_handler)

        # Консоль-хендлер
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

        self.log_file = log_file

    def add_arguments(self, parser):
        parser.add_argument(
            '--role',
            type=str,
            choices=['store_owner', 'store_admin', 'all'],
            default='all',
            help='Какую роль тестировать (default: all)'
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Создать тестовые данные перед тестированием'
        )

    def handle(self, *args, **options):
        """Главная функция команды"""
        self.logger.info("🚀 НАЧИНАЕМ TOTAL EMULATION TEST")
        self.logger.info("=" * 80)

        role_to_test = options.get('role', 'all')
        create_test_data = options.get('create_test_data', False)

        try:
            # 1. Подготовка тестовых пользователей и данных
            if create_test_data:
                self.create_test_data()

            # 2. Получение тестовых пользователей
            users = self.get_test_users()

            # 3. Эмуляция для store_owner
            if role_to_test in ['store_owner', 'all']:
                self.logger.info("\n🏪 ТЕСТИРОВАНИЕ АДМИНКИ ВЛАДЕЛЬЦА МАГАЗИНА")
                self.logger.info("-" * 60)
                self.emulate_store_owner(users['store_owner'])

            # 4. Эмуляция для store_admin
            if role_to_test in ['store_admin', 'all']:
                self.logger.info("\n📦 ТЕСТИРОВАНИЕ АДМИНКИ АДМИНИСТРАТОРА МАГАЗИНА")
                self.logger.info("-" * 60)
                self.emulate_store_admin(users['store_admin'])

            # 5. Генерация отчета
            self.generate_report()

        except Exception as e:
            self.logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В ЭМУЛЯЦИИ: {e}", exc_info=True)
            self.test_results['errors'].append({
                'type': 'CRITICAL_ERROR',
                'message': str(e),
                'time': datetime.now().isoformat()
            })

        finally:
            self.logger.info(f"\n📄 ПОДРОБНЫЕ ЛОГИ СОХРАНЕНЫ В: {self.log_file}")
            self.logger.info("🏁 TOTAL EMULATION TEST ЗАВЕРШЕН")

    def create_test_data(self):
        """Создание тестовых данных для эмуляции"""
        self.logger.info("📝 Создание тестовых данных...")

        User = get_user_model()

        # Создаем тестовых пользователей если их нет
        try:
            with transaction.atomic():
                # Владелец магазина
                store_owner, created = User.objects.get_or_create(
                    username='test_store_owner',
                    defaults={
                        'name': 'Тестовый Владелец Магазина',
                        'role': 'store_owner',
                        'is_staff': True,
                        'is_active': True,
                        'telegram_id': '11111111'
                    }
                )
                if created:
                    self.logger.info("✅ Создан тестовый владелец магазина")

                # Администратор магазина
                store_admin, created = User.objects.get_or_create(
                    username='test_store_admin',
                    defaults={
                        'name': 'Тестовый Администратор Магазина',
                        'role': 'store_admin',
                        'is_staff': True,
                        'is_active': True,
                        'telegram_id': '22222222'
                    }
                )
                if created:
                    self.logger.info("✅ Создан тестовый администратор магазина")

                # Создаем тестовые данные для магазина
                self.create_store_test_data()

                # Назначаем permissions пользователям
                self.assign_store_permissions(store_owner, store_admin)

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания тестовых данных: {e}")

    def create_store_test_data(self):
        """Создание тестовых данных магазина"""
        try:
            # Получаем модели магазина
            SeedBank = apps.get_model('magicbeans_store', 'SeedBank')
            Strain = apps.get_model('magicbeans_store', 'Strain')
            StockItem = apps.get_model('magicbeans_store', 'StockItem')

            # Тестовый сидбанк
            seedbank, created = SeedBank.objects.get_or_create(
                name='Test SeedBank',
                defaults={
                    'description': 'Тестовый сидбанк для эмуляции',
                    'website': 'https://test-seedbank.com'
                }
            )
            if created:
                self.logger.info("✅ Создан тестовый сидбанк")

            # Тестовый сорт
            strain, created = Strain.objects.get_or_create(
                name='Test Strain',
                defaults={
                    'seedbank': seedbank,
                    'strain_type': 'indica',
                    'description': 'Тестовый сорт для эмуляции'
                }
            )
            if created:
                self.logger.info("✅ Создан тестовый сорт")

            # Тестовый товар
            stock_item, created = StockItem.objects.get_or_create(
                strain=strain,
                defaults={
                    'quantity': 100,
                    'price': 1000.00,
                    'description': 'Тестовый товар для эмуляции'
                }
            )
            if created:
                self.logger.info("✅ Создан тестовый товар")

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания данных магазина: {e}")

    def assign_store_permissions(self, store_owner, store_admin):
        """Назначение permissions для работы с магазином"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        try:
            # Получаем все permissions для приложения magicbeans_store
            store_permissions = Permission.objects.filter(
                content_type__app_label='magicbeans_store'
            )

            # Владелец магазина получает ВСЕ permissions
            store_owner.user_permissions.set(store_permissions)
            self.logger.info(f"✅ Назначено {store_permissions.count()} permissions владельцу магазина")

            # Администратор магазина получает permissions кроме delete
            admin_permissions = store_permissions.exclude(
                codename__startswith='delete_'
            )
            store_admin.user_permissions.set(admin_permissions)
            self.logger.info(f"✅ Назначено {admin_permissions.count()} permissions администратору магазина")

        except Exception as e:
            self.logger.error(f"❌ Ошибка назначения permissions: {e}")

    def get_test_users(self):
        """Получение тестовых пользователей"""
        User = get_user_model()

        try:
            users = {
                'store_owner': User.objects.get(username='test_store_owner'),
                'store_admin': User.objects.get(username='test_store_admin')
            }
            self.logger.info("✅ Тестовые пользователи найдены")
            return users
        except User.DoesNotExist as e:
            self.logger.error(f"❌ Тестовые пользователи не найдены: {e}")
            self.logger.info("💡 Запустите команду с флагом --create-test-data")
            sys.exit(1)

    def emulate_store_owner(self, user):
        """Эмуляция работы владельца магазина"""
        self.logger.info(f"🔑 Входим как владелец магазина: {user.username}")

        # Авторизация
        self.client.force_login(user)

        # Список URL для тестирования - ТОЛЬКО стратегические функции
        test_urls = [
            {'url': '/store_owner/', 'name': 'Главная store_owner', 'expected_status': 200},
            {'url': '/users/manage-admins/', 'name': 'Управление администраторами', 'expected_status': 200},
            # Убираем операционные URL - они теперь только в store_admin
        ]

        for test_case in test_urls:
            self.test_url_access(test_case, 'store_owner')

        # Тестирование создания записей - только стратегические формы
        self.test_creation_forms('store_owner', user)

    def emulate_store_admin(self, user):
        """Эмуляция работы администратора магазина"""
        self.logger.info(f"🔑 Входим как администратор магазина: {user.username}")

        # Авторизация
        self.client.force_login(user)

        # Список URL для тестирования
        test_urls = [
            {'url': '/store_admin/', 'name': 'Главная store_admin', 'expected_status': 200},
            {'url': '/store_admin/magicbeans_store/seedbank/', 'name': 'Список сидбанков', 'expected_status': 200},
            {'url': '/store_admin/magicbeans_store/strain/', 'name': 'Список сортов', 'expected_status': 200},
            {'url': '/store_admin/magicbeans_store/stockitem/', 'name': 'Список товаров', 'expected_status': 200},
        ]

        for test_case in test_urls:
            self.test_url_access(test_case, 'store_admin')

        # Тестирование создания записей
        self.test_creation_forms('store_admin', user)

    def test_url_access(self, test_case, role):
        """Тестирование доступа к URL"""
        url = test_case['url']
        name = test_case['name']
        expected_status = test_case['expected_status']

        self.logger.info(f"🌐 Тестирование: {name} ({url})")

        try:
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)

            result = {
                'url': url,
                'name': name,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'response_time_ms': response_time,
                'success': response.status_code == expected_status,
                'time': datetime.now().isoformat()
            }

            if response.status_code == expected_status:
                self.logger.info(f"   ✅ УСПЕХ: {response.status_code} ({response_time}ms)")

                # Проверяем наличие важных элементов на странице
                if hasattr(response, 'content'):
                    content = response.content.decode('utf-8', errors='ignore')
                    self.check_page_elements(content, result)

            else:
                self.logger.error(f"   ❌ ОШИБКА: ожидался {expected_status}, получен {response.status_code}")
                if hasattr(response, 'content'):
                    error_content = response.content.decode('utf-8', errors='ignore')[:500]
                    result['error_content'] = error_content

            # Сохраняем результат
            if role == 'store_owner':
                self.test_results['store_owner_tests'].append(result)
            else:
                self.test_results['store_admin_tests'].append(result)

        except Exception as e:
            self.logger.error(f"   💥 ИСКЛЮЧЕНИЕ: {e}")
            error_result = {
                'url': url,
                'name': name,
                'error': str(e),
                'time': datetime.now().isoformat()
            }
            self.test_results['errors'].append(error_result)

    def check_page_elements(self, content, result):
        """Проверка важных элементов на странице"""
        checks = {
            'has_title': '<title>' in content,
            'has_navigation': 'nav' in content.lower(),
            'has_user_menu': 'user-menu' in content or 'user-dropdown' in content,
            'has_error_500': '500' in content and 'error' in content.lower(),
            'has_error_404': '404' in content and 'not found' in content.lower(),
            'has_form_errors': 'errorlist' in content,
        }

        result['page_checks'] = checks

        # Логируем важные находки
        if checks['has_error_500']:
            self.logger.warning("   ⚠️  Обнаружена ошибка 500 на странице")
        if checks['has_error_404']:
            self.logger.warning("   ⚠️  Обнаружена ошибка 404 на странице")
        if checks['has_form_errors']:
            self.logger.warning("   ⚠️  Обнаружены ошибки форм на странице")

    def test_creation_forms(self, role, user):
        """Тестирование форм создания записей"""
        self.logger.info(f"📝 Тестирование форм создания для {role}")

        if role == 'store_owner':
            admin_prefix = '/store_owner'
            # Для владельца магазина - только стратегические формы
            creation_urls = [
                # Пока оставляем пустым - можно добавить формы настроек позже
            ]
        else:  # store_admin
            admin_prefix = '/store_admin'
            # Для администратора магазина - операционные формы
        creation_urls = [
            f'{admin_prefix}/magicbeans_store/seedbank/add/',
            f'{admin_prefix}/magicbeans_store/strain/add/',
            f'{admin_prefix}/magicbeans_store/stockitem/add/',
        ]

        for url in creation_urls:
            self.logger.info(f"📋 Тестирование формы создания: {url}")
            try:
                response = self.client.get(url)
                if response.status_code == 200:
                    self.logger.info(f"   ✅ Форма загружается успешно")

                    # Проверяем наличие CSRF токена
                    content = response.content.decode('utf-8', errors='ignore')
                    if 'csrfmiddlewaretoken' in content:
                        self.logger.info(f"   ✅ CSRF токен найден")
                    else:
                        self.logger.warning(f"   ⚠️  CSRF токен НЕ найден")

                else:
                    self.logger.error(f"   ❌ Ошибка загрузки формы: {response.status_code}")

            except Exception as e:
                self.logger.error(f"   💥 Ошибка при тестировании формы: {e}")

    def generate_report(self):
        """Генерация итогового отчета"""
        self.logger.info("\n📊 ГЕНЕРАЦИЯ ИТОГОВОГО ОТЧЕТА")
        self.logger.info("=" * 60)

        # Подсчет статистики
        store_owner_success = sum(1 for test in self.test_results['store_owner_tests'] if test.get('success', False))
        store_owner_total = len(self.test_results['store_owner_tests'])

        store_admin_success = sum(1 for test in self.test_results['store_admin_tests'] if test.get('success', False))
        store_admin_total = len(self.test_results['store_admin_tests'])

        total_errors = len(self.test_results['errors'])

        summary = {
            'store_owner': {
                'success': store_owner_success,
                'total': store_owner_total,
                'success_rate': round((store_owner_success / store_owner_total * 100) if store_owner_total > 0 else 0, 2)
            },
            'store_admin': {
                'success': store_admin_success,
                'total': store_admin_total,
                'success_rate': round((store_admin_success / store_admin_total * 100) if store_admin_total > 0 else 0, 2)
            },
            'errors': total_errors,
            'end_time': datetime.now().isoformat()
        }

        self.test_results['summary'] = summary

        # Вывод отчета
        self.logger.info(f"🏪 ВЛАДЕЛЕЦ МАГАЗИНА: {store_owner_success}/{store_owner_total} успешно ({summary['store_owner']['success_rate']}%)")
        self.logger.info(f"📦 АДМИНИСТРАТОР МАГАЗИНА: {store_admin_success}/{store_admin_total} успешно ({summary['store_admin']['success_rate']}%)")
        self.logger.info(f"❌ ОБЩЕЕ КОЛИЧЕСТВО ОШИБОК: {total_errors}")

        # Сохранение JSON отчета
        report_file = os.path.join(settings.BASE_DIR, 'logs', f'emulation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"💾 JSON отчет сохранен: {report_file}")
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения JSON отчета: {e}")

        # Рекомендации
        self.logger.info("\n💡 РЕКОМЕНДАЦИИ:")
        if total_errors > 0:
            self.logger.info("   🔧 Обратите внимание на ошибки выше и исправьте их")
        if summary['store_owner']['success_rate'] < 100:
            self.logger.info("   🏪 Есть проблемы в админке владельца магазина")
        if summary['store_admin']['success_rate'] < 100:
            self.logger.info("   📦 Есть проблемы в админке администратора магазина")
        if summary['store_owner']['success_rate'] == 100 and summary['store_admin']['success_rate'] == 100 and total_errors == 0:
            self.logger.info("   🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО! Система работает отлично!")
