#!/usr/bin/env python
"""
🎯 REAL ADMIN EMULATION - Реальная эмуляция с настоящими операциями в БД

Этот скрипт выполняет НАСТОЯЩИЕ действия администратора:
- Создает реального пользователя с permissions
- Выполняет HTTP POST запросы для создания объектов
- Проверяет что объекты сохранились в базе данных
- Показывает результаты в браузере
- Подробно логирует каждое действие

Запуск: python manage.py real_admin_emulation
"""

import os
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
from bs4 import BeautifulSoup

class Command(BaseCommand):
    help = '🎯 Реальная эмуляция администратора с настоящими операциями в БД'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'
        self.session = requests.Session()
        self.csrf_token = None
        self.operations = []

    def setup_logging(self):
        """Детальное логирование"""
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f'real_emulation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

        self.logger = logging.getLogger('real_emulation')
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

        self.log_file = log_file

    def add_arguments(self, parser):
        parser.add_argument(
            '--delay',
            type=int,
            default=3,
            help='Задержка между операциями в секундах'
        )

    def handle(self, *args, **options):
        """Главная функция"""
        self.delay = options.get('delay', 3)

        self.logger.info("🎯 НАЧИНАЕМ РЕАЛЬНУЮ ЭМУЛЯЦИЮ АДМИНИСТРАТОРА")
        self.logger.info("=" * 80)
        self.logger.info("🔥 ЭТА ЭМУЛЯЦИЯ СОЗДАЕТ НАСТОЯЩИЕ ОБЪЕКТЫ В БД!")

        try:
            # 1. Создание и настройка пользователя
            user = self.create_admin_user()

            # 2. Аутентификация
            self.authenticate_user(user)

            # 3. Получение CSRF токена
            self.get_csrf_token()

            # 4. Создание сидбанка (если нужно)
            seedbank_id = self.ensure_seedbank_exists()

            # 5. РЕАЛЬНОЕ СОЗДАНИЕ СОРТА
            strain_data = self.create_real_strain(seedbank_id)

            # 6. Проверка в БД
            self.verify_strain_in_database(strain_data)

            # 7. Показ результатов в браузере
            self.show_results_in_browser()

            # 8. Отчет
            self.generate_report()

        except Exception as e:
            self.logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        finally:
            self.logger.info(f"📄 ЛОГИ: {self.log_file}")

    def create_admin_user(self):
        """Создание администратора с правами"""
        self.logger.info("📝 Создание администратора магазина...")

        User = get_user_model()

        try:
            with transaction.atomic():
                # Создаем или получаем пользователя
                user, created = User.objects.get_or_create(
                    username='real_store_admin',
                    defaults={
                        'name': 'Реальный Администратор',
                        'role': 'store_admin',
                        'is_staff': True,
                        'is_active': True,
                        'telegram_id': '12345678'
                    }
                )

                # Назначаем все права на магазин
                from django.contrib.auth.models import Permission
                store_permissions = Permission.objects.filter(
                    content_type__app_label='magicbeans_store'
                )
                user.user_permissions.set(store_permissions)

                if created:
                    self.logger.info("✅ Администратор создан")
                else:
                    self.logger.info("✅ Администратор найден")

                self.logger.info(f"   👤 Пользователь: {user.username}")
                self.logger.info(f"   🎭 Роль: {user.role}")
                self.logger.info(f"   🔐 Staff: {user.is_staff}")
                self.logger.info(f"   📜 Permissions: {user.user_permissions.count()}")

                return user

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания пользователя: {e}")
            raise

    def authenticate_user(self, user):
        """Аутентификация пользователя для HTTP запросов"""
        self.logger.info("🔑 Аутентификация для HTTP запросов...")

        # Используем Django Test Client для получения session
        client = Client()
        client.force_login(user)
        session_key = client.session.session_key

        # Устанавливаем cookie в requests session
        self.session.cookies.set('sessionid', session_key, domain='127.0.0.1')

        self.logger.info(f"✅ Session ID: {session_key[:20]}...")

    def get_csrf_token(self):
        """Получение CSRF токена"""
        self.logger.info("🛡️ Получение CSRF токена...")

        try:
            # Запрашиваем любую страницу админки для получения CSRF
            response = self.session.get(f"{self.base_url}/store_admin/")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})

                if csrf_input:
                    self.csrf_token = csrf_input.get('value')
                    self.logger.info(f"✅ CSRF токен получен: {self.csrf_token[:20]}...")
                else:
                    # Пробуем получить из cookies
                    csrf_cookie = self.session.cookies.get('csrftoken')
                    if csrf_cookie:
                        self.csrf_token = csrf_cookie
                        self.logger.info("✅ CSRF токен получен из cookie")
                    else:
                        self.logger.warning("⚠️ CSRF токен не найден")
            else:
                self.logger.error(f"❌ Ошибка доступа к админке: {response.status_code}")

        except Exception as e:
            self.logger.error(f"❌ Ошибка получения CSRF: {e}")

    def ensure_seedbank_exists(self):
        """Убеждаемся что есть сидбанк для создания сорта"""
        self.logger.info("🌱 Проверка наличия сидбанка...")

        try:
            SeedBank = apps.get_model('magicbeans_store', 'SeedBank')

            # Ищем существующий сидбанк
            seedbank = SeedBank.objects.first()

            if seedbank:
                self.logger.info(f"✅ Найден сидбанк: {seedbank.name} (ID: {seedbank.id})")
                return seedbank.id

            # Создаем новый сидбанк
            self.logger.info("📝 Создаем новый сидбанк...")

            seedbank_data = {
                'name': f'Test SeedBank {datetime.now().strftime("%H%M%S")}',
                'description': 'Автоматически созданный сидбанк для тестирования',
                'website': 'https://test-seedbank.com',
                'is_active': True,
                'csrfmiddlewaretoken': self.csrf_token
            }

            response = self.session.post(
                f"{self.base_url}/store_admin/magicbeans_store/seedbank/add/",
                data=seedbank_data
            )

            if response.status_code in [200, 302]:
                # Получаем созданный сидбанк
                seedbank = SeedBank.objects.filter(name=seedbank_data['name']).first()
                if seedbank:
                    self.logger.info(f"✅ Сидбанк создан: {seedbank.name} (ID: {seedbank.id})")
                    return seedbank.id
                else:
                    self.logger.error("❌ Сидбанк не найден после создания")
            else:
                self.logger.error(f"❌ Ошибка создания сидбанка: {response.status_code}")

        except Exception as e:
            self.logger.error(f"❌ Ошибка с сидбанком: {e}")

        return None

    def create_real_strain(self, seedbank_id):
        """РЕАЛЬНОЕ создание сорта с заполнением всех полей"""
        self.logger.info("🌿 СОЗДАЕМ РЕАЛЬНЫЙ СОРТ В БАЗЕ ДАННЫХ!")
        self.logger.info("-" * 50)

        if not seedbank_id:
            self.logger.error("❌ Нет сидбанка для создания сорта")
            return None

        # Генерируем случайные данные из правильных choices
        timestamp = datetime.now().strftime("%H%M%S")
        strain_names = ["White Widow", "Northern Lights", "AK-47", "Blueberry", "Amnesia Haze"]

        # Правильные значения из модели
        strain_types = ["regular", "feminized", "autoflowering"]
        thc_contents = ["15-20", "20-25", "10-15", "25-30", "5-10"]
        cbd_contents = ["0-0.5", "0.5-1", "1-1.5", "1.5-2", "2-2.5"]
        flowering_times = ["8-10", "10-12", "6-8", "auto", "12+"]

        import random
        strain_name = f"{random.choice(strain_names)} {timestamp}"
        strain_type = random.choice(strain_types)

        strain_data = {
            'seedbank': seedbank_id,
            'name': strain_name,
            'strain_type': strain_type,
            'description': f'Автоматически созданный сорт для тестирования. '
                          f'Высококачественный {strain_type} сорт с отличными характеристиками. '
                          f'Подходит как для новичков, так и для опытных гроверов.',
            'thc_content': random.choice(thc_contents),
            'cbd_content': random.choice(cbd_contents),
            'flowering_time': random.choice(flowering_times),
            'is_active': True,
            'csrfmiddlewaretoken': self.csrf_token
        }

        self.logger.info("📝 ЗАПОЛНЯЕМ ФОРМУ СОЗДАНИЯ СОРТА:")
        self.logger.info(f"   • Название: {strain_data['name']}")
        self.logger.info(f"   • Сидбанк: ID {strain_data['seedbank']}")
        self.logger.info(f"   • Тип: {strain_data['strain_type']}")
        self.logger.info(f"   • ТГК: {strain_data['thc_content']}")
        self.logger.info(f"   • КБД: {strain_data['cbd_content']}")
        self.logger.info(f"   • Цветение: {strain_data['flowering_time']}")
        self.logger.info(f"   • Описание: {strain_data['description'][:50]}...")
        self.logger.info(f"   • Активен: {strain_data['is_active']}")

        time.sleep(self.delay)  # Пауза для наблюдения

        try:
            self.logger.info("🔥 ОТПРАВЛЯЕМ POST ЗАПРОС НА СОЗДАНИЕ...")

            response = self.session.post(
                f"{self.base_url}/store_admin/magicbeans_store/strain/add/",
                data=strain_data
            )

            self.logger.info(f"📡 Статус ответа: {response.status_code}")

            if response.status_code == 302:
                # 302 = редирект = успешное создание
                self.logger.info("✅ РЕДИРЕКТ! СОРТ СОЗДАН УСПЕШНО!")

                self.operations.append({
                    'action': 'create_strain',
                    'data': strain_data,
                    'status_code': response.status_code,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })

                return strain_data

            elif response.status_code == 200:
                # 200 = форма отобразилась снова = есть ошибки валидации
                self.logger.error("❌ СТАТУС 200 = ОШИБКИ ВАЛИДАЦИИ В ФОРМЕ!")

                # Извлекаем ошибки из HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                errors = soup.find_all(class_='errorlist')

                if errors:
                    self.logger.error("📝 ОШИБКИ ФОРМЫ:")
                    for error in errors:
                        error_text = error.get_text(strip=True)
                        self.logger.error(f"   • {error_text}")
                else:
                    self.logger.error("📝 ОШИБКИ НЕ НАЙДЕНЫ В HTML, ПРОВЕРЯЕМ ДРУГИЕ МЕСТА...")

                    # Ищем любые div с классом error
                    error_divs = soup.find_all('div', class_=lambda x: x and 'error' in x.lower())
                    for div in error_divs:
                        self.logger.error(f"   • {div.get_text(strip=True)}")

                    # Ищем ul с ошибками
                    error_lists = soup.find_all('ul', class_=lambda x: x and 'error' in x.lower())
                    for ul in error_lists:
                        self.logger.error(f"   • {ul.get_text(strip=True)}")

                    # Если ничего не найдено, показываем часть HTML
                    if not error_divs and not error_lists:
                        form_html = soup.find('form')
                        if form_html:
                            self.logger.error("📝 ЧАСТЬ HTML ФОРМЫ:")
                            self.logger.error(f"   {str(form_html)[:500]}...")

                self.operations.append({
                    'action': 'create_strain',
                    'data': strain_data,
                    'status_code': response.status_code,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'Form validation errors'
                })

                return None

            else:
                self.logger.error(f"❌ НЕОЖИДАННЫЙ HTTP СТАТУС: {response.status_code}")

                self.operations.append({
                    'action': 'create_strain',
                    'data': strain_data,
                    'status_code': response.status_code,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })

                return None

        except Exception as e:
            self.logger.error(f"💥 ИСКЛЮЧЕНИЕ ПРИ СОЗДАНИИ СОРТА: {e}")
            return None

    def verify_strain_in_database(self, strain_data):
        """Проверка что сорт действительно создался в БД"""
        if not strain_data:
            return False

        self.logger.info("🔍 ПРОВЕРЯЕМ БАЗУ ДАННЫХ...")

        try:
            Strain = apps.get_model('magicbeans_store', 'Strain')

            # Ищем созданный сорт
            strain = Strain.objects.filter(name=strain_data['name']).first()

            if strain:
                self.logger.info("🎉 СОРТ НАЙДЕН В БАЗЕ ДАННЫХ!")
                self.logger.info(f"   🆔 ID: {strain.id}")
                self.logger.info(f"   📛 Название: {strain.name}")
                self.logger.info(f"   🏪 Сидбанк: {strain.seedbank.name}")
                self.logger.info(f"   🔬 Тип: {strain.strain_type}")
                self.logger.info(f"   🌿 ТГК: {strain.thc_content}%")
                self.logger.info(f"   💚 КБД: {strain.cbd_content}%")
                self.logger.info(f"   ⏰ Цветение: {strain.flowering_time} дней")
                self.logger.info(f"   ✅ Активен: {strain.is_active}")
                self.logger.info(f"   📅 Создан: {strain.created_at}")

                # Считаем общее количество сортов
                total_strains = Strain.objects.count()
                self.logger.info(f"📊 Всего сортов в БД: {total_strains}")

                return True
            else:
                self.logger.error("❌ СОРТ НЕ НАЙДЕН В БАЗЕ ДАННЫХ!")
                return False

        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки БД: {e}")
            return False

    def show_results_in_browser(self):
        """Показываем результаты в браузере"""
        self.logger.info("🌐 ОТКРЫВАЕМ РЕЗУЛЬТАТЫ В БРАУЗЕРЕ...")

        # Показываем список сортов
        strains_url = f"{self.base_url}/store_admin/magicbeans_store/strain/"

        self.logger.info(f"📋 Открываем список сортов: {strains_url}")
        webbrowser.open(strains_url)

        time.sleep(self.delay)

        # Также показываем главную страницу с обновленной статистикой
        main_url = f"{self.base_url}/store_admin/"
        self.logger.info(f"🏠 Открываем главную страницу: {main_url}")
        webbrowser.open(main_url)

    def generate_report(self):
        """Генерация итогового отчета"""
        self.logger.info("\n📊 ИТОГОВЫЙ ОТЧЕТ РЕАЛЬНОЙ ЭМУЛЯЦИИ")
        self.logger.info("=" * 60)

        total_operations = len(self.operations)
        successful_operations = len([op for op in self.operations if op.get('success')])

        self.logger.info(f"⚡ Операций выполнено: {total_operations}")
        self.logger.info(f"✅ Успешных операций: {successful_operations}")
        self.logger.info(f"❌ Неудачных операций: {total_operations - successful_operations}")

        if successful_operations > 0:
            self.logger.info("\n🎯 УСПЕШНЫЕ ОПЕРАЦИИ:")
            for op in self.operations:
                if op.get('success'):
                    action = op['action']
                    data = op['data']
                    if action == 'create_strain':
                        self.logger.info(f"   ✅ Создан сорт: {data['name']}")

        # Сохраняем отчет в JSON
        report_file = os.path.join(settings.BASE_DIR, 'logs', f'real_emulation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.operations, f, ensure_ascii=False, indent=2)
            self.logger.info(f"\n💾 Отчет сохранен: {report_file}")
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения отчета: {e}")

        if successful_operations == total_operations and total_operations > 0:
            self.logger.info("\n🎉 ВСЕ ОПЕРАЦИИ ВЫПОЛНЕНЫ УСПЕШНО!")
            self.logger.info("   🌿 Сорт создан в базе данных")
            self.logger.info("   🌐 Результаты показаны в браузере")
            self.logger.info("   📋 Вы можете увидеть новый сорт в списке")
        else:
            self.logger.warning("\n⚠️ НЕ ВСЕ ОПЕРАЦИИ ВЫПОЛНЕНЫ УСПЕШНО")
            self.logger.info("   🔧 Проверьте логи для диагностики")

        self.logger.info(f"\n📄 ПОДРОБНЫЕ ЛОГИ: {self.log_file}")
