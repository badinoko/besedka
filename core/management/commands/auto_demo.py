#!/usr/bin/env python
"""
🎭 АВТОМАТИЧЕСКАЯ ДЕМОНСТРАЦИЯ

Создает объекты автоматически и показывает в браузере

Запуск: python manage.py auto_demo
"""

import webbrowser
import time
import random
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from magicbeans_store.models import SeedBank, Strain, StockItem

class Command(BaseCommand):
    help = 'Автоматическая демонстрация'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=3, help='Количество объектов')

    def handle(self, *args, **options):
        count = options['count']
        base_url = 'http://127.0.0.1:8000'

        print("🎭 АВТОМАТИЧЕСКАЯ ДЕМОНСТРАЦИЯ АДМИНКИ")
        print("=" * 50)

        # Создаем администратора
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'name': 'Demo User',
                'role': 'store_admin',
                'is_staff': True,
                'is_active': True,
                'telegram_id': f"demo_{datetime.now().strftime('%H%M%S')}"
            }
        )
        user.set_password('demo123')
        user.save()

        print(f"✅ Подготовлен пользователь: demo_user / demo123")

        # Открываем админку
        print("\n🌐 Открываем админку...")
        webbrowser.open(f"{base_url}/store_admin/")
        time.sleep(2)

        timestamp = datetime.now().strftime("%H%M")

        # Создаем сидбанки
        print(f"\n🌱 Создаем {count} сидбанков...")
        seedbanks = []
        for i in range(count):
            seedbank = SeedBank.objects.create(
                name=f"AutoBank_{timestamp}_{i+1}",
                description=f"Автоматически созданный сидбанк #{i+1}",
                website=f"https://autobank{i+1}.com",
                is_active=True
            )
            seedbanks.append(seedbank)
            print(f"   ✅ Создан: {seedbank.name}")

        # Показываем сидбанки
        print("🌐 Показываем созданные сидбанки...")
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/seedbank/")
        time.sleep(3)

        # Создаем сорта
        print(f"\n🌿 Создаем {count * 2} сортов...")
        strains = []
        strain_types = ["regular", "feminized", "autoflowering"]

        for i, seedbank in enumerate(seedbanks):
            for j in range(2):
                strain = Strain.objects.create(
                    name=f"AutoStrain_{timestamp}_{i+1}_{j+1}",
                    seedbank=seedbank,
                    strain_type=random.choice(strain_types),
                    thc_content=random.choice(['15-20', '20-25', '10-15']),
                    cbd_content=random.choice(['0-0.5', '0.5-1', '1-1.5']),
                    flowering_time=random.choice(['8-10', '10-12', '6-8']),
                    yield_indoor=f"{random.randint(400, 600)}г/м²",
                    description=f"Автоматически созданный сорт",
                    is_active=True
                )
                strains.append(strain)
                print(f"   ✅ Создан: {strain.name}")

        # Показываем сорта
        print("🌐 Показываем созданные сорта...")
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/strain/")
        time.sleep(3)

        # Создаем товары
        print(f"\n📦 Создаем товары на складе...")
        pack_sizes = [1, 3, 5, 10]

        for strain in strains:
            # Для каждого сорта создаем товары с РАЗНЫМ количеством семян
            for seeds_count in pack_sizes[:2]:  # Берем только первые 2 размера чтобы избежать дубликатов
                stock_item = StockItem.objects.create(
                    strain=strain,
                    seeds_count=seeds_count,
                    price=random.randint(20, 100),
                    quantity=random.randint(50, 200),
                    is_active=True
                )
                print(f"   ✅ Создан товар: {stock_item.seeds_count} семян {strain.name}")

        # Показываем товары
        print("🌐 Показываем созданные товары...")
        webbrowser.open(f"{base_url}/store_admin/magicbeans_store/stockitem/")
        time.sleep(3)

        # Финал
        print("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
        print("=" * 50)
        print(f"✅ Создано сидбанков: {len(seedbanks)}")
        print(f"✅ Создано сортов: {len(strains)}")
        print(f"✅ Создано товаров: {len(strains) * 2}")
        print(f"\n🔐 Для входа в админку:")
        print(f"   👤 Логин: demo_user")
        print(f"   🔐 Пароль: demo123")
        print(f"   🌐 URL: {base_url}/admin/login/")

        # Возвращаемся на главную
        print("\n🏠 Возвращаемся на главную админки...")
        webbrowser.open(f"{base_url}/store_admin/")
