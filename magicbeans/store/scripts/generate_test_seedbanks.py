from django.core.management.base import BaseCommand
from magicbeans.store.models import SeedBank, Strain
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Генерирует тестовые сидбанки и сорта для UX-отладки'

    def handle(self, *args, **options):
        # Очищаем старые данные
        Strain.objects.all().delete()
        SeedBank.objects.all().delete()

        # Примеры сидбанков
        seedbanks = [
            {'name': 'Empty Seedbank', 'description': '', 'is_visible': True},
            {'name': 'Full Seedbank', 'description': 'Сидбанк с сортами', 'is_visible': True},
            {'name': 'Hidden Seedbank', 'description': 'Скрытый сидбанк', 'is_visible': False},
            {'name': 'Mixed Content', 'description': 'Сидбанк с разными сортами', 'is_visible': True},
        ]
        created_banks = []
        for sb in seedbanks:
            bank = SeedBank.objects.create(
                name=sb['name'],
                description=sb['description'],
                is_visible=sb['is_visible'],
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            created_banks.append(bank)

        # Добавляем сорта в Full Seedbank
        full_bank = SeedBank.objects.get(name='Full Seedbank')
        for i in range(1, 6):
            Strain.objects.create(
                name=f'Strain {i} (desc+photo)',
                description=f'Описание для сорта {i}',
                seed_bank=full_bank,
                is_visible=True,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
        for i in range(6, 8):
            Strain.objects.create(
                name=f'Strain {i} (no desc)',
                description='',
                seed_bank=full_bank,
                is_visible=True,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
        for i in range(8, 11):
            Strain.objects.create(
                name=f'Strain {i} (hidden)',
                description='Скрытый сорт',
                seed_bank=full_bank,
                is_visible=False,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )

        # Добавляем сорта в Mixed Content
        mixed_bank = SeedBank.objects.get(name='Mixed Content')
        for i in range(1, 4):
            Strain.objects.create(
                name=f'Mixed Strain {i} (desc)',
                description=f'Описание для Mixed Strain {i}',
                seed_bank=mixed_bank,
                is_visible=True,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
        for i in range(4, 6):
            Strain.objects.create(
                name=f'Mixed Strain {i} (no desc)',
                description='',
                seed_bank=mixed_bank,
                is_visible=True,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
        # Пустой сидбанк (Empty Seedbank) — без сортов
        # Hidden Seedbank — без сортов, но скрытый
        self.stdout.write(self.style.SUCCESS('Тестовые сидбанки и сорта успешно созданы!')) 