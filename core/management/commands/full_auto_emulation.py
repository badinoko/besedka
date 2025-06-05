#!/usr/bin/env python
"""
🚀 ПОЛНАЯ АВТОМАТИЧЕСКАЯ ЭМУЛЯЦИЯ

Полностью автоматическая эмуляция которая:
- Сама логинится
- Сама создает объекты через HTTP запросы
- Показывает процесс в браузере в реальном времени
- Создает МНОГО тестовых данных
- Все происходит автоматически!

Запуск: python manage.py full_auto_emulation
"""

import os
import time
import webbrowser
import logging
import random
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.urls import reverse
import threading
from magicbeans_store.models import SeedBank, Strain

class Command(BaseCommand):
    help = '🚀 Полная автоматическая эмуляция админки'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'
        self.session = requests.Session()  # Используем requests.Session вместо Django Test Client
        self.current_step = 0
        self.results = {
            'seedbanks_created': 0,
            'strains_created': 0,
            'stock_items_created': 0,
            'total_operations': 0
        }

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger('auto_emulation')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=int, default=2, help='Задержка между операциями (секунды)')
        parser.add_argument('--count', type=int, default=10, help='Количество объектов каждого типа')

    def create_test_admin(self):
        """Создание и подготовка тестового администратора"""
        self.logger.info("📝 Создание тестового администратора...")

        User = get_user_model()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username='auto_admin',
                defaults={
                    'name': 'Auto Test Admin',
                    'role': 'store_admin',
                    'is_staff': True,
                    'is_active': True,
                    'telegram_id': f"auto_{timestamp}"
                }
            )

            user.set_password('admin123')
            user.save()

            if created:
                self.logger.info(f"✅ Создан новый пользователь: {user.username}")
            else:
                self.logger.info(f"✅ Обновлен пользователь: {user.username}")

            return user

    def auto_login(self, user):
        """Автоматический вход в систему"""
        self.logger.info("🔐 Автоматический вход в систему...")

        # Сначала получаем форму логина для CSRF токена
        login_page = self.session.get(f"{self.base_url}/accounts/login/")
        if login_page.status_code != 200:
            self.logger.error(f"❌ Не удалось получить страницу логина: {login_page.status_code}")
            return False

        # Извлекаем CSRF токен
        csrf_token = None
        if 'csrfmiddlewaretoken' in login_page.text:
            import re
            csrf_match = re.search(r'csrfmiddlewaretoken.*?value="([^"]*)"', login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)

        # Данные для логина
        login_data = {
            'username': user.username,
            'password': 'admin123',
        }

        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token

        # Отправляем запрос логина
        login_response = self.session.post(
            f"{self.base_url}/accounts/login/",
            data=login_data,
            allow_redirects=False
        )

        if login_response.status_code == 302:
            self.logger.info("✅ Авторизация успешна!")
            return True
        else:
            self.logger.error(f"❌ Ошибка авторизации: {login_response.status_code}")
            return False

    def show_browser_page(self, url, title, delay=1):
        """Показать страницу в браузере с задержкой"""
        self.current_step += 1

        self.logger.info(f"\n🎯 ШАГ {self.current_step}: {title}")
        self.logger.info(f"   🌐 Открываем: {url}")

        webbrowser.open(url)

        self.logger.info(f"   ⏱️ Ждем {delay} секунд...")
        time.sleep(delay)

    def create_seedbank_auto(self, name, delay=1):
        """Автоматическое создание сидбанка"""
        self.logger.info(f"🌱 Создаем сидбанк: {name}")

        # Получаем форму добавления
        add_url = f"{self.base_url}/store_admin/magicbeans_store/seedbank/add/"
        response = self.session.get(add_url)

        if response.status_code != 200:
            self.logger.error(f"❌ Ошибка получения формы: {response.status_code}")
            return False

        # Извлекаем CSRF токен
        csrf_token = None
        if 'csrfmiddlewaretoken' in response.content.decode():
            import re
            csrf_match = re.search(r'csrfmiddlewaretoken.*?value="([^"]*)"', response.content.decode())
            if csrf_match:
                csrf_token = csrf_match.group(1)

        # Данные для создания сидбанка
        data = {
            'name': name,
            'description': f'Автоматически созданный сидбанк {name}',
            'website': f'https://{name.lower().replace(" ", "")}.com',
            'email': f'info@{name.lower().replace(" ", "")}.com',
            'is_active': True,
        }

        if csrf_token:
            data['csrfmiddlewaretoken'] = csrf_token

        # Отправляем POST запрос
        response = self.session.post(add_url, data)

        if response.status_code == 302:  # Успешное перенаправление
            self.logger.info(f"✅ Сидбанк '{name}' создан успешно!")
            self.results['seedbanks_created'] += 1
            self.results['total_operations'] += 1

            # Показываем результат в браузере
            self.show_browser_page(f"{self.base_url}/store_admin/magicbeans_store/seedbank/",
                                 f"Результат: создан сидбанк {name}", delay)
            return True
        else:
            self.logger.error(f"❌ Ошибка создания сидбанка: {response.status_code}")
            return False

    def create_strain_auto(self, name, seedbank_id, delay=1):
        """Автоматическое создание сорта"""
        self.logger.info(f"🌿 Создаем сорт: {name}")

        # Получаем форму добавления
        add_url = f"{self.base_url}/store_admin/magicbeans_store/strain/add/"
        response = self.session.get(add_url)

        if response.status_code != 200:
            self.logger.error(f"❌ Ошибка получения формы: {response.status_code}")
            return False

        # Извлекаем CSRF токен
        csrf_token = None
        if 'csrfmiddlewaretoken' in response.content.decode():
            import re
            csrf_match = re.search(r'csrfmiddlewaretoken.*?value="([^"]*)"', response.content.decode())
            if csrf_match:
                csrf_token = csrf_match.group(1)

        # Данные для создания сорта (правильные значения из choices)
        strain_types = ["regular", "feminized", "autoflowering"]

        data = {
            'name': name,
            'seedbank': seedbank_id,
            'strain_type': random.choice(strain_types),
            'indica_percentage': random.randint(30, 70),
            'sativa_percentage': random.randint(30, 70),
            'thc_content': f"{random.randint(15, 25)}-{random.randint(26, 30)}%",
            'cbd_content': f"{random.randint(0, 2)}-{random.randint(3, 5)}%",
            'flowering_time': random.randint(7, 12),
            'yield_indoor': f"{random.randint(400, 600)}г/м²",
            'yield_outdoor': f"{random.randint(600, 1000)}г/растение",
            'description': f'Автоматически созданный сорт {name}',
            'is_active': True,
        }

        if csrf_token:
            data['csrfmiddlewaretoken'] = csrf_token

        # Отправляем POST запрос
        response = self.session.post(add_url, data)

        if response.status_code == 302:  # Успешное перенаправление
            self.logger.info(f"✅ Сорт '{name}' создан успешно!")
            self.results['strains_created'] += 1
            self.results['total_operations'] += 1

            # Показываем результат в браузере
            self.show_browser_page(f"{self.base_url}/store_admin/magicbeans_store/strain/",
                                 f"Результат: создан сорт {name}", delay)
            return True
        else:
            self.logger.error(f"❌ Ошибка создания сорта: {response.status_code}")
            return False

    def create_stock_item_auto(self, strain_id, delay=1):
        """Автоматическое создание товара на складе"""
        self.logger.info(f"📦 Создаем товар на складе для сорта ID: {strain_id}")

        # Получаем форму добавления
        add_url = f"{self.base_url}/store_admin/magicbeans_store/stockitem/add/"
        response = self.session.get(add_url)

        if response.status_code != 200:
            self.logger.error(f"❌ Ошибка получения формы: {response.status_code}")
            return False

        # Извлекаем CSRF токен
        csrf_token = None
        if 'csrfmiddlewaretoken' in response.content.decode():
            import re
            csrf_match = re.search(r'csrfmiddlewaretoken.*?value="([^"]*)"', response.content.decode())
            if csrf_match:
                csrf_token = csrf_match.group(1)

        # Данные для создания товара
        pack_sizes = [1, 3, 5, 10]
        pack_size = random.choice(pack_sizes)

        data = {
            'strain': strain_id,
            'pack_size': pack_size,
            'price': f"{random.randint(20, 100)}.00",
            'quantity_in_stock': random.randint(50, 200),
            'is_available': True,
        }

        if csrf_token:
            data['csrfmiddlewaretoken'] = csrf_token

        # Отправляем POST запрос
        response = self.session.post(add_url, data)

        if response.status_code == 302:  # Успешное перенаправление
            self.logger.info(f"✅ Товар (пакет {pack_size} семян) создан успешно!")
            self.results['stock_items_created'] += 1
            self.results['total_operations'] += 1

            # Показываем результат в браузере
            self.show_browser_page(f"{self.base_url}/store_admin/magicbeans_store/stockitem/",
                                 f"Результат: создан товар пакет {pack_size} семян", delay)
            return True
        else:
            self.logger.error(f"❌ Ошибка создания товара: {response.status_code}")
            return False

    def run_full_emulation(self, delay, count):
        """Запуск полной автоматической эмуляции"""
        self.logger.info("🚀 ЗАПУСК ПОЛНОЙ АВТОМАТИЧЕСКОЙ ЭМУЛЯЦИИ")
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 Будет создано:")
        self.logger.info(f"   🌱 Сидбанков: {count}")
        self.logger.info(f"   🌿 Сортов: {count * 2}")  # По 2 сорта на сидбанк
        self.logger.info(f"   📦 Товаров: {count * 4}")  # По 2 товара на сорт
        self.logger.info(f"   ⏱️ Задержка: {delay} сек между операциями")
        self.logger.info("-" * 60)

        # Создаем и логинимся под администратором
        admin_user = self.create_test_admin()
        if not self.auto_login(admin_user):
            self.logger.error("❌ Не удалось войти в систему!")
            return

        # Показываем начальную страницу
        self.show_browser_page(f"{self.base_url}/store_admin/",
                              "Начало: главная страница админки", delay)

        # ФАЗА 1: Создание сидбанков
        self.logger.info("\n🌱 ФАЗА 1: СОЗДАНИЕ СИДБАНКОВ")
        timestamp = datetime.now().strftime("%H%M")

        # Получаем реальные ID созданных сидбанков
        initial_seedbank_count = SeedBank.objects.count()

        for i in range(1, count + 1):
            seedbank_name = f"AutoBank {timestamp}_{i:02d}"
            success = self.create_seedbank_auto(seedbank_name, delay)

        # Получаем ID всех созданных сидбанков
        created_seedbanks = SeedBank.objects.filter(
            name__startswith=f"AutoBank {timestamp}_"
        ).values_list('id', flat=True)

        # ФАЗА 2: Создание сортов
        self.logger.info("\n🌿 ФАЗА 2: СОЗДАНИЕ СОРТОВ")

        # Получаем реальные ID созданных сортов
        initial_strain_count = Strain.objects.count()

        for seedbank_id in created_seedbanks:
            for j in range(1, 3):  # По 2 сорта на сидбанк
                strain_name = f"AutoStrain {timestamp}_{seedbank_id}_{j}"
                success = self.create_strain_auto(strain_name, seedbank_id, delay)

        # Получаем ID всех созданных сортов
        created_strains = Strain.objects.filter(
            name__startswith=f"AutoStrain {timestamp}_"
        ).values_list('id', flat=True)

        # ФАЗА 3: Создание товаров на складе
        self.logger.info("\n📦 ФАЗА 3: СОЗДАНИЕ ТОВАРОВ НА СКЛАДЕ")

        for strain_id in created_strains:
            for k in range(1, 3):  # По 2 товара на сорт
                success = self.create_stock_item_auto(strain_id, delay)

        # Финальная статистика
        self.logger.info("\n🎉 ЭМУЛЯЦИЯ ЗАВЕРШЕНА!")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 ИТОГОВАЯ СТАТИСТИКА:")
        self.logger.info(f"   🌱 Создано сидбанков: {self.results['seedbanks_created']}")
        self.logger.info(f"   🌿 Создано сортов: {self.results['strains_created']}")
        self.logger.info(f"   📦 Создано товаров: {self.results['stock_items_created']}")
        self.logger.info(f"   🎯 Всего операций: {self.results['total_operations']}")

        # Показываем финальную страницу
        self.show_browser_page(f"{self.base_url}/store_admin/",
                              "Финал: просмотр всех созданных объектов", delay * 2)

    def handle(self, *args, **options):
        """Главная функция"""
        delay = options.get('delay', 2)
        count = options.get('count', 10)

        self.logger.info("🚀 ПОЛНАЯ АВТОМАТИЧЕСКАЯ ЭМУЛЯЦИЯ АДМИНКИ")
        self.logger.info("🎭 ВСЕ ПРОИСХОДИТ АВТОМАТИЧЕСКИ - ПРОСТО НАБЛЮДАЙТЕ!")

        # Запускаем эмуляцию в отдельном потоке
        emulation_thread = threading.Thread(
            target=self.run_full_emulation,
            args=(delay, count)
        )
        emulation_thread.start()

        # Ждем завершения
        emulation_thread.join()

        self.logger.info("\n🎉 ВСЯ АВТОМАТИЧЕСКАЯ ЭМУЛЯЦИЯ ЗАВЕРШЕНА!")
        self.logger.info("💡 Проверьте результаты в админке")
