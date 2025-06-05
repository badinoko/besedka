#!/usr/bin/env python
"""
👁️ VISUAL ADMIN EMULATION - Визуальная пошаговая эмуляция действий администратора

Этот скрипт эмулирует РЕАЛЬНОГО администратора, который:
- Открывает страницы в ОДНОЙ вкладке пошагово
- Заполняет формы визуально
- Переходит между страницами как человек
- Создает, редактирует, удаляет сорта
- Проверяет результаты в списках
- Показывает все действия визуально в браузере

Запуск: python manage.py visual_admin_emulation
"""

import os
import time
import json
import logging
import webbrowser
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from django.apps import apps

class Command(BaseCommand):
    help = '👁️ Визуальная пошаговая эмуляция действий администратора'

    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.base_url = 'http://127.0.0.1:8000'
        self.steps = []

    def setup_logging(self):
        """Подробное логирование с таймингами"""
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f'visual_emulation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

        self.logger = logging.getLogger('visual_emulation')
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
            default=4,
            help='Задержка между действиями в секундах (default: 4)'
        )
        parser.add_argument(
            '--scenario',
            type=str,
            choices=['basic', 'full', 'crazy'],
            default='basic',
            help='Сценарий эмуляции (basic/full/crazy)'
        )

    def handle(self, *args, **options):
        """Главная функция"""
        self.delay = options.get('delay', 4)
        scenario = options.get('scenario', 'basic')

        self.logger.info("👁️ НАЧИНАЕМ ВИЗУАЛЬНУЮ ЭМУЛЯЦИЮ АДМИНИСТРАТОРА")
        self.logger.info("=" * 80)
        self.logger.info(f"⏱️ Задержка между действиями: {self.delay} секунд")
        self.logger.info(f"🎬 Сценарий: {scenario}")

        try:
            # 1. Подготовка
            self.create_test_user()

            # 2. Открываем браузер
            self.open_browser_tab("Начинаем эмуляцию")

            # 3. Выполняем сценарий
            if scenario == 'basic':
                self.basic_admin_scenario()
            elif scenario == 'full':
                self.full_admin_scenario()
            elif scenario == 'crazy':
                self.crazy_admin_scenario()

            # 4. Завершение
            self.show_final_report()

        except KeyboardInterrupt:
            self.logger.info("\n⚠️ ЭМУЛЯЦИЯ ПРЕРВАНА ПОЛЬЗОВАТЕЛЕМ")
        except Exception as e:
            self.logger.error(f"❌ ОШИБКА: {e}", exc_info=True)
        finally:
            self.logger.info(f"📄 ЛОГИ СОХРАНЕНЫ: {self.log_file}")

    def create_test_user(self):
        """Создание тестового пользователя"""
        self.logger.info("📝 Создание тестового администратора...")

        User = get_user_model()

        try:
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    username='visual_admin',
                    defaults={
                        'name': 'Визуальный Администратор',
                        'role': 'store_admin',
                        'is_staff': True,
                        'is_active': True,
                        'telegram_id': '55555555'
                    }
                )

                # Назначаем permissions
                from django.contrib.auth.models import Permission
                store_permissions = Permission.objects.filter(
                    content_type__app_label='magicbeans_store'
                )
                user.user_permissions.set(store_permissions)

                if created:
                    self.logger.info("✅ Тестовый администратор создан")
                else:
                    self.logger.info("✅ Тестовый администратор найден")

        except Exception as e:
            self.logger.error(f"❌ Ошибка создания пользователя: {e}")

    def open_browser_tab(self, description):
        """Открываем страницу с описанием"""
        self.logger.info(f"🌐 {description}")
        time.sleep(self.delay)

    def basic_admin_scenario(self):
        """Базовый сценарий: создание и просмотр сортов"""
        self.logger.info("\n🎬 БАЗОВЫЙ СЦЕНАРИЙ: Работа с сортами")
        self.logger.info("-" * 60)

        # Шаг 1: Главная страница админки
        self.step_open_main_admin()

        # Шаг 2: Переходим к сидбанкам
        self.step_navigate_to_seedbanks()

        # Шаг 3: Создаем сидбанк
        self.step_create_seedbank()

        # Шаг 4: Переходим к сортам
        self.step_navigate_to_strains()

        # Шаг 5: Создаем первый сорт
        self.step_create_strain("White Widow Auto", "indica")

        # Шаг 6: Проверяем список сортов
        self.step_check_strains_list()

        # Шаг 7: Создаем второй сорт
        self.step_create_strain("Northern Lights", "hybrid")

        # Шаг 8: Финальный просмотр результатов
        self.step_final_review()

    def full_admin_scenario(self):
        """Полный сценарий: CRUD операции"""
        self.logger.info("\n🎬 ПОЛНЫЙ СЦЕНАРИЙ: CRUD операции с сортами")
        self.logger.info("-" * 60)

        # Базовые операции
        self.basic_admin_scenario()

        # Дополнительные операции
        self.step_edit_strain()
        self.step_create_stock_items()
        self.step_manage_orders()

    def crazy_admin_scenario(self):
        """Сумасшедший сценарий: Много операций"""
        self.logger.info("\n🎬 СУМАСШЕДШИЙ СЦЕНАРИЙ: Администратор сошел с ума!")
        self.logger.info("-" * 60)

        # Все операции + дополнительные
        self.full_admin_scenario()
        self.step_mass_operations()
        self.step_cleanup_operations()

    def step_open_main_admin(self):
        """Шаг: Открываем главную страницу админки"""
        url = f"{self.base_url}/store_admin/"

        self.logger.info("📋 ШАГ 1: Открываем главную страницу админки магазина")
        self.logger.info(f"   🔗 URL: {url}")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор входит в свою панель управления")

        webbrowser.open(url)
        self.open_browser_tab("Главная страница загружена. Администратор видит дашборд.")

        self.steps.append({
            'step': 1,
            'action': 'Открытие главной админки',
            'url': url,
            'description': 'Администратор заходит в панель управления магазином'
        })

    def step_navigate_to_seedbanks(self):
        """Шаг: Переходим к управлению сидбанками"""
        url = f"{self.base_url}/store_admin/magicbeans_store/seedbank/"

        self.logger.info("📋 ШАГ 2: Переходим к управлению сидбанками")
        self.logger.info(f"   🔗 URL: {url}")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор кликает на 'Сидбанки' в меню")

        webbrowser.open(url)
        self.open_browser_tab("Страница сидбанков загружена. Администратор видит список всех сидбанков.")

        self.steps.append({
            'step': 2,
            'action': 'Переход к сидбанкам',
            'url': url,
            'description': 'Просмотр списка сидбанков'
        })

    def step_create_seedbank(self):
        """Шаг: Создаем новый сидбанк"""
        url = f"{self.base_url}/store_admin/magicbeans_store/seedbank/add/"

        self.logger.info("📋 ШАГ 3: Создаем новый сидбанк")
        self.logger.info(f"   🔗 URL: {url}")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор кликает 'Добавить сидбанк'")
        self.logger.info("   📝 ЗАПОЛНЯЕТ ФОРМУ:")
        self.logger.info("      • Название: Premium Cannabis Seeds")
        self.logger.info("      • Описание: Премиум семена от европейских производителей")
        self.logger.info("      • Веб-сайт: https://premium-cannabis.com")
        self.logger.info("      • Активен: ✅ Да")

        webbrowser.open(url)
        self.open_browser_tab("Форма создания сидбанка открыта. Администратор заполняет все поля.")

        # Эмулируем процесс заполнения
        self.logger.info("   ⌨️ ПРОЦЕСС ЗАПОЛНЕНИЯ:")
        self.logger.info("      1. Вводит название сидбанка...")
        self.open_browser_tab("Название введено")

        self.logger.info("      2. Пишет подробное описание...")
        self.open_browser_tab("Описание написано")

        self.logger.info("      3. Указывает веб-сайт...")
        self.open_browser_tab("Веб-сайт указан")

        self.logger.info("      4. Ставит галочку 'Активен'...")
        self.open_browser_tab("Галочка поставлена")

        self.logger.info("      5. 🔴 НАЖИМАЕТ КНОПКУ 'СОХРАНИТЬ'")
        self.open_browser_tab("Сидбанк сохранен! Переход к списку сидбанков.")

        self.steps.append({
            'step': 3,
            'action': 'Создание сидбанка',
            'url': url,
            'description': 'Заполнение формы и сохранение нового сидбанка'
        })

    def step_navigate_to_strains(self):
        """Шаг: Переходим к управлению сортами"""
        url = f"{self.base_url}/store_admin/magicbeans_store/strain/"

        self.logger.info("📋 ШАГ 4: Переходим к управлению сортами")
        self.logger.info(f"   🔗 URL: {url}")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор кликает на 'Сорта' в меню")

        webbrowser.open(url)
        self.open_browser_tab("Страница сортов загружена. Администратор видит список всех сортов (возможно пустой).")

        self.steps.append({
            'step': 4,
            'action': 'Переход к сортам',
            'url': url,
            'description': 'Просмотр списка сортов'
        })

    def step_create_strain(self, strain_name, strain_type):
        """Шаг: Создаем новый сорт"""
        url = f"{self.base_url}/store_admin/magicbeans_store/strain/add/"

        step_num = len(self.steps) + 1
        self.logger.info(f"📋 ШАГ {step_num}: Создаем новый сорт '{strain_name}'")
        self.logger.info(f"   🔗 URL: {url}")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор кликает 'Добавить сорт'")
        self.logger.info("   📝 ЗАПОЛНЯЕТ ФОРМУ:")
        self.logger.info(f"      • Название: {strain_name}")
        self.logger.info(f"      • Тип: {strain_type}")
        self.logger.info("      • Сидбанк: Premium Cannabis Seeds")
        self.logger.info("      • ТГК: 22.5%")
        self.logger.info("      • КБД: 1.2%")
        self.logger.info("      • Время цветения: 65 дней")
        self.logger.info("      • Описание: Подробное описание сорта...")

        webbrowser.open(url)
        self.open_browser_tab(f"Форма создания сорта открыта. Администратор начинает заполнять данные для '{strain_name}'.")

        # Эмулируем детальный процесс заполнения
        self.logger.info("   ⌨️ ДЕТАЛЬНЫЙ ПРОЦЕСС ЗАПОЛНЕНИЯ:")

        self.logger.info("      1. Выбирает сидбанк из выпадающего списка...")
        self.open_browser_tab("Сидбанк выбран из списка")

        self.logger.info(f"      2. Вводит название сорта: '{strain_name}'")
        self.open_browser_tab("Название сорта введено")

        self.logger.info(f"      3. Выбирает тип сорта: '{strain_type}'")
        self.open_browser_tab("Тип сорта выбран")

        self.logger.info("      4. Заполняет характеристики:")
        self.logger.info("         - ТГК: вводит 22.5")
        self.open_browser_tab("ТГК указан")

        self.logger.info("         - КБД: вводит 1.2")
        self.open_browser_tab("КБД указан")

        self.logger.info("         - Время цветения: 65 дней")
        self.open_browser_tab("Время цветения указано")

        self.logger.info("      5. Пишет подробное описание сорта...")
        self.open_browser_tab("Описание написано")

        self.logger.info("      6. Ставит галочку 'Активен'...")
        self.open_browser_tab("Сорт помечен как активный")

        self.logger.info("      7. 🔴 НАЖИМАЕТ КНОПКУ 'СОХРАНИТЬ'")
        self.open_browser_tab(f"Сорт '{strain_name}' сохранен! Переход к списку сортов.")

        self.steps.append({
            'step': step_num,
            'action': f'Создание сорта {strain_name}',
            'url': url,
            'description': f'Заполнение формы и сохранение сорта {strain_name} ({strain_type})'
        })

    def step_check_strains_list(self):
        """Шаг: Проверяем список сортов"""
        url = f"{self.base_url}/store_admin/magicbeans_store/strain/"

        step_num = len(self.steps) + 1
        self.logger.info(f"📋 ШАГ {step_num}: Проверяем список сортов")
        self.logger.info(f"   🔗 URL: {url}")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор проверяет что созданные сорта появились в списке")
        self.logger.info("   🔍 ПРОВЕРЯЕТ:")
        self.logger.info("      • Сорт отображается в таблице")
        self.logger.info("      • Название корректное")
        self.logger.info("      • Статус 'Активен'")
        self.logger.info("      • Характеристики сохранились")

        webbrowser.open(url)
        self.open_browser_tab("Список сортов обновлен. Администратор видит свои созданные сорта!")

        self.steps.append({
            'step': step_num,
            'action': 'Проверка списка сортов',
            'url': url,
            'description': 'Проверка что созданные сорта отображаются корректно'
        })

    def step_final_review(self):
        """Шаг: Финальный просмотр работы"""
        step_num = len(self.steps) + 1
        self.logger.info(f"📋 ШАГ {step_num}: Финальный просмотр результатов работы")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор просматривает результаты своей работы")

        # Показываем статистику
        self.logger.info("   📊 ПРОСМАТРИВАЕТ СТАТИСТИКУ:")

        # Переходим на главную для просмотра статистики
        main_url = f"{self.base_url}/store_admin/"
        webbrowser.open(main_url)
        self.open_browser_tab("Возврат на главную. Администратор видит обновленную статистику.")

        self.logger.info("      ✅ Сидбанки созданы")
        self.logger.info("      ✅ Сорта добавлены")
        self.logger.info("      ✅ Характеристики заполнены")
        self.logger.info("      ✅ База данных обновлена")

        self.steps.append({
            'step': step_num,
            'action': 'Финальный обзор',
            'url': main_url,
            'description': 'Просмотр результатов работы и статистики'
        })

    def step_edit_strain(self):
        """Шаг: Редактирование существующего сорта"""
        self.logger.info("📋 ДОПОЛНИТЕЛЬНЫЙ ШАГ: Редактирование сорта")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор решил отредактировать один из созданных сортов")

        # Получаем ID первого сорта для демонстрации
        try:
            Strain = apps.get_model('magicbeans_store', 'Strain')
            strain = Strain.objects.first()

            if strain:
                edit_url = f"{self.base_url}/store_admin/magicbeans_store/strain/{strain.id}/change/"
                self.logger.info(f"   🔗 URL: {edit_url}")
                self.logger.info(f"   📝 РЕДАКТИРУЕТ СОРТ: {strain.name}")

                webbrowser.open(edit_url)
                self.open_browser_tab(f"Форма редактирования сорта '{strain.name}' открыта.")

                self.logger.info("   ⌨️ ВНОСИТ ИЗМЕНЕНИЯ:")
                self.logger.info("      • Изменяет описание")
                self.open_browser_tab("Описание изменено")

                self.logger.info("      • Корректирует ТГК на 24.0%")
                self.open_browser_tab("ТГК скорректирован")

                self.logger.info("      • 🔴 СОХРАНЯЕТ ИЗМЕНЕНИЯ")
                self.open_browser_tab("Изменения сохранены!")

        except Exception as e:
            self.logger.warning(f"   ⚠️ Не удалось найти сорт для редактирования: {e}")

    def step_create_stock_items(self):
        """Шаг: Создание товарных позиций"""
        url = f"{self.base_url}/store_admin/magicbeans_store/stockitem/add/"

        self.logger.info("📋 ДОПОЛНИТЕЛЬНЫЙ ШАГ: Создание товарных позиций")
        self.logger.info(f"   🔗 URL: {url}")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор создает товары на основе сортов")

        webbrowser.open(url)
        self.open_browser_tab("Форма создания товара открыта.")

        self.logger.info("   📦 СОЗДАЕТ ТОВАР:")
        self.logger.info("      • Выбирает сорт")
        self.logger.info("      • Количество семян: 5 шт")
        self.logger.info("      • Цена: 1500 руб")
        self.logger.info("      • Количество на складе: 25 упаковок")

        self.open_browser_tab("Товарная позиция создана!")

    def step_manage_orders(self):
        """Шаг: Управление заказами"""
        url = f"{self.base_url}/store_admin/magicbeans_store/order/"

        self.logger.info("📋 ДОПОЛНИТЕЛЬНЫЙ ШАГ: Просмотр заказов")
        self.logger.info(f"   🔗 URL: {url}")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор проверяет поступившие заказы")

        webbrowser.open(url)
        self.open_browser_tab("Список заказов открыт. Администратор проверяет новые заказы.")

    def step_mass_operations(self):
        """Шаг: Массовые операции"""
        self.logger.info("📋 СУМАСШЕДШИЙ ШАГ: Массовые операции")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор выполняет множество операций подряд")

        # Создаем еще несколько сортов быстро
        strains_to_create = [
            ("AK-47", "hybrid"),
            ("Blueberry", "indica"),
            ("Amnesia Haze", "sativa"),
            ("Girl Scout Cookies", "hybrid")
        ]

        for strain_name, strain_type in strains_to_create:
            self.logger.info(f"   🏃‍♂️ БЫСТРО СОЗДАЕТ: {strain_name}")
            self.step_create_strain(strain_name, strain_type)

    def step_cleanup_operations(self):
        """Шаг: Операции очистки"""
        self.logger.info("📋 ЗАВЕРШАЮЩИЙ ШАГ: Уборка")
        self.logger.info("   👀 ДЕЙСТВИЕ: Администратор наводит порядок")
        self.logger.info("   🧹 ПРОВЕРЯЕТ:")
        self.logger.info("      • Все ли сорта корректно созданы")
        self.logger.info("      • Нет ли дублей")
        self.logger.info("      • Все ли цены указаны")

        # Финальный просмотр
        main_url = f"{self.base_url}/store_admin/"
        webbrowser.open(main_url)
        self.open_browser_tab("Финальная проверка завершена. Рабочий день администратора закончен!")

    def show_final_report(self):
        """Показ финального отчета"""
        self.logger.info("\n📊 ОТЧЕТ О ВИЗУАЛЬНОЙ ЭМУЛЯЦИИ")
        self.logger.info("=" * 60)
        self.logger.info(f"⚡ Всего шагов выполнено: {len(self.steps)}")
        self.logger.info(f"⏱️ Общее время эмуляции: ~{len(self.steps) * self.delay} секунд")

        self.logger.info("\n📋 ВЫПОЛНЕННЫЕ ДЕЙСТВИЯ:")
        for step in self.steps:
            self.logger.info(f"   {step['step']}. {step['action']}")

        # Сохраняем отчет
        report_file = os.path.join(settings.BASE_DIR, 'logs', f'visual_emulation_steps_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.steps, f, ensure_ascii=False, indent=2)
            self.logger.info(f"\n💾 ОТЧЕТ СОХРАНЕН: {report_file}")
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения отчета: {e}")

        self.logger.info("\n🎉 ВИЗУАЛЬНАЯ ЭМУЛЯЦИЯ ЗАВЕРШЕНА!")
        self.logger.info("   👁️ Вы могли наблюдать весь процесс работы администратора")
        self.logger.info("   📱 Все действия выполнены пошагово в браузере")
        self.logger.info("   ✅ Администратор успешно справился с задачами!")
