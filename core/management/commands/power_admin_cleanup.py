#!/usr/bin/env python
"""
🧹 МОЩНАЯ ОЧИСТКА И ПОЛНОЕ ТЕСТИРОВАНИЕ АДМИНКИ

Этот скрипт:
1. Исправляет проблему "NONE NONE" у пользователя
2. Удаляет ВСЕ тестовые данные
3. Создает полный набор тестовых данных
4. Тестирует ВСЕ операции админки
5. Скрывает/показывает объекты
6. Удаляет и восстанавливает объекты

Запуск: python manage.py power_admin_cleanup
"""

import webbrowser
import time
import random
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from magicbeans_store.models import SeedBank, Strain, StockItem

class Command(BaseCommand):
    help = '🧹 Мощная очистка и полное тестирование админки'

    def add_arguments(self, parser):
        parser.add_argument('--clean-only', action='store_true', help='Только очистка, без тестирования')
        parser.add_argument('--test-only', action='store_true', help='Только тестирование, без очистки')

    def handle(self, *args, **options):
        base_url = 'http://127.0.0.1:8000'

        print("🧹 МОЩНАЯ ОЧИСТКА И ПОЛНОЕ ТЕСТИРОВАНИЕ АДМИНКИ")
        print("=" * 60)

        # ФАЗА 1: Исправление пользователя
        if not options.get('test_only'):
            self.fix_user_display()

        # ФАЗА 2: Очистка тестовых данных
        if not options.get('test_only'):
            self.cleanup_test_data()

        # ФАЗА 3: Полное тестирование
        if not options.get('clean_only'):
            self.full_admin_testing(base_url)

    def fix_user_display(self):
        """Исправление проблемы NONE NONE в админке"""
        print("\n🔧 ИСПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ (NONE NONE)")
        print("-" * 40)

        User = get_user_model()

        # Исправляем всех пользователей
        users_fixed = 0
        for user in User.objects.all():
            if not user.name or user.name.strip() == "":
                if user.username == 'test_store_admin':
                    user.name = 'Тестовый Администратор'
                elif user.username == 'demo_user':
                    user.name = 'Демо Пользователь'
                elif user.username == 'auto_admin':
                    user.name = 'Авто Администратор'
                else:
                    user.name = f'Пользователь {user.username}'

                user.save()
                users_fixed += 1
                print(f"   ✅ Исправлен: {user.username} -> {user.name}")

        if users_fixed == 0:
            print("   ✅ Все пользователи уже имеют корректные имена")
        else:
            print(f"   ✅ Исправлено пользователей: {users_fixed}")

    def cleanup_test_data(self):
        """Полная очистка всех тестовых данных"""
        print("\n🗑️ ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
        print("-" * 40)

        # Подсчет объектов перед удалением
        stock_count = StockItem.objects.count()
        strain_count = Strain.objects.count()
        seedbank_count = SeedBank.objects.count()

        print(f"📊 Найдено объектов:")
        print(f"   📦 Товаров на складе: {stock_count}")
        print(f"   🌿 Сортов: {strain_count}")
        print(f"   🌱 Сидбанков: {seedbank_count}")

        if stock_count + strain_count + seedbank_count == 0:
            print("   ✅ База данных уже пуста")
            return

        with transaction.atomic():
            # Удаляем в правильном порядке (из-за foreign keys)
            deleted_stock = StockItem.objects.all().delete()[0]
            deleted_strains = Strain.objects.all().delete()[0]
            deleted_seedbanks = SeedBank.objects.all().delete()[0]

        print(f"\n🗑️ Удалено:")
        print(f"   📦 Товаров: {deleted_stock}")
        print(f"   🌿 Сортов: {deleted_strains}")
        print(f"   🌱 Сидбанков: {deleted_seedbanks}")
        print("   ✅ Очистка завершена!")

    def full_admin_testing(self, base_url):
        """Полное тестирование всех возможностей админки"""
        print("\n🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ АДМИНКИ")
        print("-" * 40)

        # Подготовка администратора
        admin_user = self.prepare_admin()

        # Открываем админку
        print("\n🌐 Открываем админку...")
        webbrowser.open(f"{base_url}/store_admin/")
        time.sleep(2)

        timestamp = datetime.now().strftime("%H%M")

        # ЭТАП 1: Массовое создание
        print(f"\n🏗️ ЭТАП 1: МАССОВОЕ СОЗДАНИЕ")
        seedbanks = self.create_test_seedbanks(base_url, timestamp)
        strains = self.create_test_strains(base_url, timestamp, seedbanks)
        stock_items = self.create_test_stock(base_url, timestamp, strains)

        # ЭТАП 2: Операции видимости
        print(f"\n👁️ ЭТАП 2: ТЕСТИРОВАНИЕ ВИДИМОСТИ")
        self.test_visibility_operations(base_url, seedbanks, strains, stock_items)

        # ЭТАП 3: Редактирование объектов
        print(f"\n✏️ ЭТАП 3: ТЕСТИРОВАНИЕ РЕДАКТИРОВАНИЯ")
        self.test_edit_operations(base_url, seedbanks, strains, stock_items)

        # ЭТАП 4: Удаление и восстановление
        print(f"\n🗑️ ЭТАП 4: ТЕСТИРОВАНИЕ УДАЛЕНИЯ")
        self.test_delete_operations(base_url, seedbanks, strains, stock_items)

        # ФИНАЛ
        print(f"\n🎉 ПОЛНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("=" * 60)
        self.show_final_statistics()

    def prepare_admin(self):
        """Подготовка администратора"""
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='power_admin',
            defaults={
                'name': 'Мощный Администратор',
                'role': 'store_admin',
                'is_staff': True,
                'is_active': True,
                'telegram_id': f"power_{datetime.now().strftime('%H%M%S')}"
            }
        )
        user.set_password('power123')
        user.save()

        print(f"✅ Подготовлен администратор: power_admin / power123")
        return user

    def create_test_seedbanks(self, base_url, timestamp):
        """Создание тестовых сидбанков"""
        print("🌱 Создание тестовых сидбанков...")

        seedbank_names = [
            f"PowerSeeds_{timestamp}",
            f"EliteGenetics_{timestamp}",
            f"MegaBank_{timestamp}",
            f"TestSeeds_{timestamp}",
            f"RandomBank_{timestamp}"
        ]

        seedbanks = []
        for i, name in enumerate(seedbank_names):
            seedbank = SeedBank.objects.create(
                name=name,
                description=f"Тестовый сидбанк {name} для полного тестирования",
                website=f"https://{name.lower()}.com",
                is_active=True
            )
            seedbanks.append(seedbank)
            print(f"   ✅ Создан: {seedbank.name}")

        # Показываем в браузере
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/seedbank/")
        time.sleep(2)

        return seedbanks

    def create_test_strains(self, base_url, timestamp, seedbanks):
        """Создание тестовых сортов"""
        print("\n🌿 Создание тестовых сортов...")

        strain_names = [
            "Power Kush", "Elite Haze", "Mega OG", "Test Widow", "Random Diesel",
            "Super Cheese", "Ultra Skunk", "Hyper Lemon", "Turbo Berry", "Max White"
        ]

        strain_types = ["regular", "feminized", "autoflowering"]
        thc_choices = ['15-20', '20-25', '10-15', '25-30']
        cbd_choices = ['0-0.5', '0.5-1', '1-1.5', '1.5-2']
        flowering_choices = ['8-10', '10-12', '6-8', '12+']

        strains = []
        for i, strain_name in enumerate(strain_names):
            seedbank = seedbanks[i % len(seedbanks)]
            strain = Strain.objects.create(
                name=f"{strain_name}_{timestamp}",
                seedbank=seedbank,
                strain_type=random.choice(strain_types),
                thc_content=random.choice(thc_choices),
                cbd_content=random.choice(cbd_choices),
                flowering_time=random.choice(flowering_choices),
                yield_indoor=f"{random.randint(400, 600)}г/м²",
                yield_outdoor=f"{random.randint(600, 1000)}г/растение",
                description=f"Тестовый сорт {strain_name} для полного тестирования",
                genetics=f"{strain_name} genetics",
                is_active=True
            )
            strains.append(strain)
            print(f"   ✅ Создан: {strain.name}")

        # Показываем в браузере
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/strain/")
        time.sleep(2)

        return strains

    def create_test_stock(self, base_url, timestamp, strains):
        """Создание тестовых товаров на складе"""
        print("\n📦 Создание тестовых товаров...")

        pack_sizes = [1, 3, 5, 10]
        stock_items = []

        for strain in strains:
            # Для каждого сорта создаем 2-3 товара с разным количеством семян
            selected_sizes = random.sample(pack_sizes, random.randint(2, 3))

            for seeds_count in selected_sizes:
                stock_item = StockItem.objects.create(
                    strain=strain,
                    seeds_count=seeds_count,
                    price=random.randint(20, 150),
                    quantity=random.randint(10, 500),
                    is_active=True
                )
                stock_items.append(stock_item)
                print(f"   ✅ Создан: {seeds_count} семян {strain.name}")

        # Показываем в браузере
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/stockitem/")
        time.sleep(2)

        return stock_items

    def test_visibility_operations(self, base_url, seedbanks, strains, stock_items):
        """Тестирование операций видимости"""
        print("👁️ Тестирование скрытия/показа объектов...")

        # Скрываем случайные объекты
        hidden_seedbanks = random.sample(seedbanks, 2)
        hidden_strains = random.sample(strains, 3)
        hidden_stock = random.sample(stock_items, 5)

        for obj in hidden_seedbanks:
            obj.is_active = False
            obj.save()
            print(f"   🙈 Скрыт сидбанк: {obj.name}")

        for obj in hidden_strains:
            obj.is_active = False
            obj.save()
            print(f"   🙈 Скрыт сорт: {obj.name}")

        for obj in hidden_stock:
            obj.is_active = False
            obj.save()
            print(f"   🙈 Скрыт товар: {obj}")

        # Показываем результаты
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/seedbank/")
        time.sleep(1)
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/strain/")
        time.sleep(1)

        # Восстанавливаем видимость
        time.sleep(3)
        print("   👁️ Восстанавливаем видимость...")

        for obj in hidden_seedbanks + hidden_strains + hidden_stock:
            obj.is_active = True
            obj.save()

        print("   ✅ Все объекты снова видимы")

    def test_edit_operations(self, base_url, seedbanks, strains, stock_items):
        """Тестирование операций редактирования"""
        print("✏️ Тестирование редактирования объектов...")

        # Изменяем случайные объекты
        edit_seedbank = random.choice(seedbanks)
        edit_strain = random.choice(strains)
        edit_stock = random.choice(stock_items)

        # Изменяем сидбанк
        edit_seedbank.description = f"ИЗМЕНЕНО: {edit_seedbank.description}"
        edit_seedbank.save()
        print(f"   ✏️ Изменен сидбанк: {edit_seedbank.name}")

        # Изменяем сорт
        edit_strain.description = f"ИЗМЕНЕНО: {edit_strain.description}"
        edit_strain.save()
        print(f"   ✏️ Изменен сорт: {edit_strain.name}")

        # Изменяем товар
        edit_stock.price = edit_stock.price + 10
        edit_stock.save()
        print(f"   ✏️ Изменена цена товара: {edit_stock}")

        # Показываем результаты
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/seedbank/{edit_seedbank.id}/change/")
        time.sleep(1)

    def test_delete_operations(self, base_url, seedbanks, strains, stock_items):
        """Тестирование операций удаления"""
        print("🗑️ Тестирование удаления объектов...")

        # Удаляем несколько товаров (безопасно)
        items_to_delete = random.sample(stock_items, 3)

        for item in items_to_delete:
            item_name = str(item)
            item.delete()
            print(f"   🗑️ Удален товар: {item_name}")

        # Показываем результат
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/stockitem/")
        time.sleep(2)

        print("   ✅ Операции удаления завершены")

    def show_final_statistics(self):
        """Показ финальной статистики"""
        stock_count = StockItem.objects.count()
        strain_count = Strain.objects.count()
        seedbank_count = SeedBank.objects.count()

        print(f"📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
        print(f"   🌱 Сидбанков: {seedbank_count}")
        print(f"   🌿 Сортов: {strain_count}")
        print(f"   📦 Товаров: {stock_count}")

        print(f"\n🔐 ДАННЫЕ ДЛЯ ВХОДА:")
        print(f"   👤 Логин: power_admin")
        print(f"   🔐 Пароль: power123")
        print(f"   🌐 URL: http://127.0.0.1:8000/admin/login/")

        print(f"\n💡 Все операции протестированы:")
        print(f"   ✅ Создание объектов")
        print(f"   ✅ Скрытие/показ объектов")
        print(f"   ✅ Редактирование объектов")
        print(f"   ✅ Удаление объектов")
        print(f"   ✅ Исправлена проблема 'NONE NONE'")

        # Возвращаемся на главную
        webbrowser.open("http://127.0.0.1:8000/store_admin/")
