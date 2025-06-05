from django.core.management.base import BaseCommand
from news.models import NewsCategory, NewsSource


class Command(BaseCommand):
    help = 'Инициализация базовых данных для системы новостей'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Инициализация данных системы новостей...')
        )

        # Создаем категории
        categories_data = [
            {
                'name': 'Выращивание',
                'slug': 'growing',
                'description': 'Новости и статьи о выращивании каннабиса'
            },
            {
                'name': 'Медицинский каннабис',
                'slug': 'medical',
                'description': 'Исследования и новости медицинского применения каннабиса'
            },
            {
                'name': 'Сорта и штаммы',
                'slug': 'strains',
                'description': 'Обзоры сортов и новых штаммов каннабиса'
            },
            {
                'name': 'Оборудование',
                'slug': 'equipment',
                'description': 'Новости об оборудовании для выращивания'
            },
            {
                'name': 'Освещение',
                'slug': 'lighting',
                'description': 'Технологии освещения для гровинга'
            },
            {
                'name': 'Удобрения',
                'slug': 'nutrients',
                'description': 'Удобрения и подкормки для растений'
            },
            {
                'name': 'Гидропоника',
                'slug': 'hydroponics',
                'description': 'Гидропонные системы и технологии'
            },
            {
                'name': 'Законодательство',
                'slug': 'legal',
                'description': 'Новости законодательства о каннабисе'
            },
            {
                'name': 'Исследования',
                'slug': 'research',
                'description': 'Научные исследования каннабиса'
            },
            {
                'name': 'Общие новости',
                'slug': 'general',
                'description': 'Общие новости индустрии каннабиса'
            }
        ]

        categories_created = 0
        for cat_data in categories_data:
            category, created = NewsCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            if created:
                categories_created += 1
                self.stdout.write(f"✅ Создана категория: {category.name}")

        # Создаем источники новостей
        sources_data = [
            {
                'name': 'Leafly News',
                'url': 'https://www.leafly.com/news',
                'parsing_enabled': True
            },
            {
                'name': 'Leafly Strains',
                'url': 'https://www.leafly.com/strains',
                'parsing_enabled': True
            },
            {
                'name': 'Marijuana Moment',
                'url': 'https://www.marijuanamoment.net/',
                'parsing_enabled': True
            },
            {
                'name': 'Ganjapreneur News',
                'url': 'https://www.ganjapreneur.com/cannabis-news/',
                'parsing_enabled': True
            },
            {
                'name': 'Ganjapreneur Cultivation',
                'url': 'https://www.ganjapreneur.com/news/cannabis-cultivation/',
                'parsing_enabled': True
            },
            {
                'name': 'GPN Mag Cannabis',
                'url': 'https://gpnmag.com/category/cannabis/',
                'parsing_enabled': True
            },
            {
                'name': 'News-Medical Cannabis',
                'url': 'https://news-medical.net/condition/Cannabis',
                'parsing_enabled': True
            },
            {
                'name': 'Cannabis Science Tech',
                'url': 'https://www.cannabissciencetech.com/news',
                'parsing_enabled': True
            },
            {
                'name': 'CannaConnection Strains',
                'url': 'https://www.cannaconnection.com/strains',
                'parsing_enabled': True
            }
        ]

        sources_created = 0
        for source_data in sources_data:
            source, created = NewsSource.objects.get_or_create(
                url=source_data['url'],
                defaults={
                    'name': source_data['name'],
                    'parsing_enabled': source_data['parsing_enabled']
                }
            )
            if created:
                sources_created += 1
                self.stdout.write(f"✅ Создан источник: {source.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Инициализация завершена!\n'
                f'📚 Создано категорий: {categories_created}\n'
                f'🌐 Создано источников: {sources_created}\n\n'
                f'💡 Теперь можно запустить парсинг командой:\n'
                f'   python manage.py parse_news\n'
            )
        )
