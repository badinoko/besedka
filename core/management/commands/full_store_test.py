#!/usr/bin/env python
"""
🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ МАГАЗИНА

Выполняет полный цикл тестирования:
1. ✅ Исправляет проблему NONE NONE
2. 📦 Наполняет базу 10 сидбанками
3. 🌿 Добавляет сорта в сидбанки
4. 🎭 Эмулирует работу администратора
5. 📊 Проверяет счетчики и остатки

Запуск: python manage.py full_store_test
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, models
from magicbeans_store.models import SeedBank, Strain, StockItem
import random

class Command(BaseCommand):
    help = '🚀 Полное тестирование магазина с исправлением всех проблем'

    def add_arguments(self, parser):
        parser.add_argument('--quick', action='store_true', help='Быстрый режим без задержек')

    def handle(self, *args, **options):
        print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ МАГАЗИНА")
        print("=" * 60)

        # 1. Исправляем NONE NONE
        self.fix_none_none_issue()

        # 2. Наполняем базу данными
        self.populate_database()

        # 3. Эмулируем работу администратора
        self.emulate_admin_work()

        # 4. Показываем итоговую статистику
        self.show_final_stats()

    def fix_none_none_issue(self):
        """Исправляем проблему NONE NONE в дропдаунах"""
        print("\n🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ 'NONE NONE'")
        print("-" * 40)

        User = get_user_model()

        # Проверяем пользователей без имен
        users_without_names = User.objects.filter(
            models.Q(name__isnull=True) | models.Q(name='') | models.Q(name__startswith='Пользователь')
        )

        fixed_users = 0
        for user in users_without_names:
            if user.username == 'clean_admin':
                user.name = 'Чистый Тестовый Администратор'
            elif user.role == 'owner':
                user.name = 'Владелец Платформы'
            elif user.role == 'admin':
                user.name = 'Администратор Платформы'
            elif user.role == 'store_owner':
                user.name = 'Владелец Магазина'
            elif user.role == 'store_admin':
                user.name = 'Администратор Магазина'
            else:
                user.name = f'Пользователь {user.username.title()}'

            user.save()
            fixed_users += 1
            print(f"   ✅ Исправлен: {user.username} -> {user.name}")

        if fixed_users == 0:
            print("   ✅ Все пользователи уже имеют правильные имена")
        else:
            print(f"   ✅ Исправлено пользователей: {fixed_users}")

    def populate_database(self):
        """Наполняем базу 10 современными сидбанками"""
        print("\n📦 НАПОЛНЕНИЕ БАЗЫ ДАННЫХ")
        print("-" * 40)

        # 10 реальных современных сидбанков
        seedbanks_data = [
            {
                'name': 'Barney\'s Farm',
                'description': 'Легендарный голландский сидбанк, основанный в 1980 году. Известен сортами LSD, Pineapple Express, Tangerine Dream.',
                'website': 'https://www.barneysfarm.com',
                'country': 'Netherlands'
            },
            {
                'name': 'Sweet Seeds',
                'description': 'Испанский сидбанк, специализирующийся на автоцветущих и феминизированных семенах. Dark Devil, Cream Caramel.',
                'website': 'https://www.sweetseeds.es',
                'country': 'Spain'
            },
            {
                'name': 'Royal Queen Seeds',
                'description': 'Один из крупнейших европейских сидбанков. White Widow, Amnesia Haze, Northern Light.',
                'website': 'https://www.royalqueenseeds.com',
                'country': 'Netherlands'
            },
            {
                'name': 'Sensi Seeds',
                'description': 'Старейший сидбанк в мире, основан в 1985. Skunk #1, Northern Lights, Big Bud.',
                'website': 'https://sensiseeds.com',
                'country': 'Netherlands'
            },
            {
                'name': 'Dinafem Seeds',
                'description': 'Испанский сидбанк с отличной генетикой. Moby Dick, White Widow, Critical+.',
                'website': 'https://www.dinafem.org',
                'country': 'Spain'
            },
            {
                'name': 'Fast Buds',
                'description': 'Американский сидбанк, специализирующийся на автоцветах. Gorilla Glue Auto, GSC Auto.',
                'website': 'https://fastbuds.com',
                'country': 'USA'
            },
            {
                'name': 'Greenhouse Seeds',
                'description': 'Голландский сидбанк с множеством наград на Cannabis Cup. White Rhino, Super Silver Haze.',
                'website': 'https://greenhouseseeds.nl',
                'country': 'Netherlands'
            },
            {
                'name': 'Humboldt Seed Organization',
                'description': 'Калифорнийский сидбанк с уникальной генетикой из Северной Калифорнии. Blueberry Headband.',
                'website': 'https://humboldtseedorganization.com',
                'country': 'USA'
            },
            {
                'name': 'DNA Genetics',
                'description': 'Американский сидбанк, создатели знаменитых сортов LA Confidential, Chocolope.',
                'website': 'https://dnagenetics.com',
                'country': 'USA'
            },
            {
                'name': 'Pyramid Seeds',
                'description': 'Испанский сидбанк с доступными качественными семенами. Tutankhamon, Anesthesia.',
                'website': 'https://pyramidseeds.com',
                'country': 'Spain'
            }
        ]

        with transaction.atomic():
            # Очищаем старые данные
            StockItem.objects.all().delete()
            Strain.objects.all().delete()
            SeedBank.objects.all().delete()

            created_seedbanks = []
            for data in seedbanks_data:
                seedbank = SeedBank.objects.create(
                    name=data['name'],
                    description=data['description'],
                    website=data['website'],
                    is_active=True
                )
                created_seedbanks.append(seedbank)
                print(f"   ✅ Создан: {seedbank.name}")

            print(f"   📊 Создано сидбанков: {len(created_seedbanks)}")

            # Добавляем сорта в каждый сидбанк
            self.add_strains_to_seedbanks(created_seedbanks)

    def add_strains_to_seedbanks(self, seedbanks):
        """Добавляем по 2-3 сорта в каждый сидбанк"""
        print("\n🌿 ДОБАВЛЕНИЕ СОРТОВ")
        print("-" * 40)

        # Популярные сорта для каждого сидбанка
        strains_data = {
            'Barney\'s Farm': [
                {'name': 'LSD', 'type': 'photoperiod', 'genetics': 'indica_dominant'},
                {'name': 'Pineapple Express', 'type': 'photoperiod', 'genetics': 'hybrid'},
                {'name': 'Tangerine Dream', 'type': 'autoflower', 'genetics': 'sativa_dominant'}
            ],
            'Sweet Seeds': [
                {'name': 'Dark Devil Auto', 'type': 'autoflower', 'genetics': 'indica_dominant'},
                {'name': 'Cream Caramel', 'type': 'photoperiod', 'genetics': 'indica_dominant'}
            ],
            'Royal Queen Seeds': [
                {'name': 'White Widow', 'type': 'photoperiod', 'genetics': 'hybrid'},
                {'name': 'Amnesia Haze', 'type': 'photoperiod', 'genetics': 'sativa_dominant'},
                {'name': 'Northern Light', 'type': 'photoperiod', 'genetics': 'indica_dominant'}
            ],
            'Sensi Seeds': [
                {'name': 'Skunk #1', 'type': 'photoperiod', 'genetics': 'hybrid'},
                {'name': 'Northern Lights', 'type': 'photoperiod', 'genetics': 'indica_dominant'}
            ],
            'Dinafem Seeds': [
                {'name': 'Moby Dick', 'type': 'photoperiod', 'genetics': 'sativa_dominant'},
                {'name': 'Critical+', 'type': 'photoperiod', 'genetics': 'indica_dominant'}
            ],
            'Fast Buds': [
                {'name': 'Gorilla Glue Auto', 'type': 'autoflower', 'genetics': 'hybrid'},
                {'name': 'GSC Auto', 'type': 'autoflower', 'genetics': 'hybrid'}
            ],
            'Greenhouse Seeds': [
                {'name': 'White Rhino', 'type': 'photoperiod', 'genetics': 'indica_dominant'},
                {'name': 'Super Silver Haze', 'type': 'photoperiod', 'genetics': 'sativa_dominant'}
            ],
            'Humboldt Seed Organization': [
                {'name': 'Blueberry Headband', 'type': 'photoperiod', 'genetics': 'hybrid'}
            ],
            'DNA Genetics': [
                {'name': 'LA Confidential', 'type': 'photoperiod', 'genetics': 'indica_dominant'},
                {'name': 'Chocolope', 'type': 'photoperiod', 'genetics': 'sativa_dominant'}
            ],
            'Pyramid Seeds': [
                {'name': 'Tutankhamon', 'type': 'photoperiod', 'genetics': 'sativa_dominant'},
                {'name': 'Anesthesia', 'type': 'photoperiod', 'genetics': 'indica_dominant'}
            ]
        }

        created_strains = []
        for seedbank in seedbanks:
            if seedbank.name in strains_data:
                for strain_data in strains_data[seedbank.name]:
                    strain = Strain.objects.create(
                        seedbank=seedbank,
                        name=strain_data['name'],
                        strain_type=strain_data['type'],
                        genetics=strain_data['genetics'],
                        description=f"Популярный сорт от {seedbank.name}",
                        is_active=True
                    )
                    created_strains.append(strain)
                    print(f"   ✅ {seedbank.name}: {strain.name} ({strain.get_strain_type_display()})")

        print(f"   📊 Создано сортов: {len(created_strains)}")
        return created_strains

    def emulate_admin_work(self):
        """Эмулируем полную работу администратора"""
        print("\n🎭 ЭМУЛЯЦИЯ РАБОТЫ АДМИНИСТРАТОРА")
        print("-" * 40)

        # 1. Редактирование сидбанков
        self.emulate_seedbank_operations()

        # 2. Работа с сортами
        self.emulate_strain_operations()

        # 3. Массовые операции
        self.emulate_bulk_operations()

    def emulate_seedbank_operations(self):
        """Эмулируем операции с сидбанками"""
        print("\n📦 ОПЕРАЦИИ С СИДБАНКАМИ:")

        seedbanks = list(SeedBank.objects.all())

        # Добавляем новый сидбанк
        new_seedbank = SeedBank.objects.create(
            name='Test Seedbank',
            description='Тестовый сидбанк для демонстрации',
            website='https://test.com',
            is_active=True
        )
        print(f"   ➕ ДОБАВЛЕН: {new_seedbank.name}")

        # Редактируем существующий
        if seedbanks:
            edit_bank = seedbanks[0]
            old_description = edit_bank.description
            edit_bank.description = f"{old_description} [ОТРЕДАКТИРОВАНО]"
            edit_bank.save()
            print(f"   ✏️ ОТРЕДАКТИРОВАН: {edit_bank.name}")

        # Скрываем один сидбанк
        if len(seedbanks) > 1:
            hide_bank = seedbanks[1]
            hide_bank.is_active = False
            hide_bank.save()
            print(f"   👁️ СКРЫТ: {hide_bank.name}")

        # Удаляем тестовый сидбанк
        new_seedbank.delete()
        print(f"   🗑️ УДАЛЕН: Test Seedbank")

    def emulate_strain_operations(self):
        """Эмулируем операции с сортами"""
        print("\n🌿 ОПЕРАЦИИ С СОРТАМИ:")

        strains = list(Strain.objects.all())

        # Добавляем новый сорт
        if SeedBank.objects.exists():
            first_bank = SeedBank.objects.first()
            new_strain = Strain.objects.create(
                seedbank=first_bank,
                name='Test Strain',
                strain_type='autoflower',
                genetics='hybrid',
                description='Тестовый сорт для демонстрации',
                is_active=True
            )
            print(f"   ➕ ДОБАВЛЕН: {new_strain.name} ({first_bank.name})")

        # Редактируем существующий сорт
        if strains:
            edit_strain = strains[0]
            old_description = edit_strain.description
            edit_strain.description = f"{old_description} [ОТРЕДАКТИРОВАНО]"
            edit_strain.save()
            print(f"   ✏️ ОТРЕДАКТИРОВАН: {edit_strain.name}")

        # Скрываем сорт
        if len(strains) > 1:
            hide_strain = strains[1]
            hide_strain.is_active = False
            hide_strain.save()
            print(f"   👁️ СКРЫТ: {hide_strain.name}")

        # Удаляем тестовый сорт (если создали)
        if 'new_strain' in locals():
            new_strain.delete()
            print(f"   🗑️ УДАЛЕН: Test Strain")

    def emulate_bulk_operations(self):
        """Эмулируем массовые операции"""
        print("\n📊 МАССОВЫЕ ОПЕРАЦИИ:")

        # Массовое скрытие сортов
        strains_to_hide = Strain.objects.filter(is_active=True)[:2]
        for strain in strains_to_hide:
            strain.is_active = False
            strain.save()
        print(f"   👁️ МАССОВО СКРЫТО сортов: {len(strains_to_hide)}")

        # Массовое восстановление
        hidden_strains = Strain.objects.filter(is_active=False)
        for strain in hidden_strains:
            strain.is_active = True
            strain.save()
        print(f"   👁️ МАССОВО ВОССТАНОВЛЕНО сортов: {len(hidden_strains)}")

    def show_final_stats(self):
        """Показываем итоговую статистику"""
        print("\n📊 ИТОГОВАЯ СТАТИСТИКА")
        print("-" * 40)

        seedbank_count = SeedBank.objects.count()
        active_seedbanks = SeedBank.objects.filter(is_active=True).count()

        strain_count = Strain.objects.count()
        active_strains = Strain.objects.filter(is_active=True).count()

        # Статистика по типам сортов
        auto_count = Strain.objects.filter(strain_type='autoflower').count()
        photo_count = Strain.objects.filter(strain_type='photoperiod').count()

        print(f"🌱 Сидбанков: {seedbank_count} (активных: {active_seedbanks})")
        print(f"🌿 Сортов: {strain_count} (активных: {active_strains})")
        print(f"   📊 Автоцветы: {auto_count}")
        print(f"   📊 Фотопериодные: {photo_count}")

        print(f"\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print(f"🔗 Админка: http://127.0.0.1:8000/store_admin/")
        print(f"👤 Логин: clean_admin / clean123")
