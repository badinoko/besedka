#!/usr/bin/env python
"""
📦 ДОБАВЛЕНИЕ ТОВАРОВ НА СКЛАД

Создает StockItem для всех сортов:
- Разные упаковки семян (1, 3, 5, 10 штук)
- Реальные цены
- Случайные остатки на складе

Запуск: python manage.py add_stock_items
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from magicbeans_store.models import Strain, StockItem
import random

class Command(BaseCommand):
    help = '📦 Добавление товаров на склад для всех сортов'

    def handle(self, *args, **options):
        print("📦 ДОБАВЛЕНИЕ ТОВАРОВ НА СКЛАД")
        print("=" * 60)

        strains = Strain.objects.filter(is_active=True)
        print(f"🌿 Найдено активных сортов: {strains.count()}")

        # Типовые упаковки семян
        seed_packages = [1, 3, 5, 10]

        # Базовые цены по типам (за семечко)
        base_prices = {
            'autoflower': {'1': 800, '3': 750, '5': 700, '10': 650},
            'photoperiod': {'1': 600, '3': 550, '5': 500, '10': 450}
        }

        created_items = 0

        with transaction.atomic():
            # Очищаем старые товары
            StockItem.objects.all().delete()
            print("🗑️ Очищены старые товары")

            for strain in strains:
                print(f"\n🌱 {strain.name} ({strain.seedbank.name}):")

                # Определяем сколько упаковок создать для этого сорта
                num_packages = random.randint(2, 4)  # 2-4 упаковки
                selected_packages = random.sample(seed_packages, num_packages)

                for seeds_count in selected_packages:
                    # Вычисляем цену
                    strain_type = strain.strain_type
                    base_price = base_prices[strain_type][str(seeds_count)]

                    # Добавляем случайную вариацию цены ±15%
                    price_variation = random.uniform(0.85, 1.15)
                    final_price = int(base_price * price_variation)

                    # Случайное количество на складе
                    quantity = random.randint(0, 20)

                    # Статус активности (90% активны)
                    is_active = random.random() > 0.1

                    stock_item = StockItem.objects.create(
                        strain=strain,
                        seeds_count=seeds_count,
                        price=final_price,
                        quantity=quantity,
                        is_active=is_active
                    )

                    status = "✅" if is_active else "❌"
                    availability = "📦" if quantity > 0 else "⚠️"

                    print(f"   {status} {availability} {seeds_count} семян - {final_price}₽ ({quantity} шт)")
                    created_items += 1

        print(f"\n📊 ИТОГИ:")
        print(f"   📦 Создано товаров: {created_items}")

        # Показываем статистику
        total_active = StockItem.objects.filter(is_active=True).count()
        total_inactive = StockItem.objects.filter(is_active=False).count()
        in_stock = StockItem.objects.filter(is_active=True, quantity__gt=0).count()
        out_of_stock = StockItem.objects.filter(is_active=True, quantity=0).count()

        print(f"   ✅ Активных товаров: {total_active}")
        print(f"   ❌ Неактивных товаров: {total_inactive}")
        print(f"   📦 В наличии: {in_stock}")
        print(f"   ⚠️ Нет в наличии: {out_of_stock}")

        # Общая стоимость склада
        from django.db.models import Sum, F
        total_value = StockItem.objects.filter(is_active=True).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0

        print(f"   💰 Общая стоимость склада: {total_value:,} ₽")

        print(f"\n🎉 СКЛАД ГОТОВ!")
        print(f"🔗 Проверьте админку: http://127.0.0.1:8000/store_admin/")
        print(f"👤 Логин: clean_admin / clean123")
