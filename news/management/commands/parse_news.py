import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.services import NewsParsingService


class Command(BaseCommand):
    help = 'Парсинг новостей с внешних источников'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Запустить в тестовом режиме с демо-данными',
        )
        parser.add_argument(
            '--source',
            type=str,
            help='Парсить только указанный источник (по имени)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Запуск парсера новостей...')
        )

        try:
            service = NewsParsingService()
            result = service.run_parsing()

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Парсинг завершен успешно!\n'
                        f'📊 Всего обработано статей: {result["total_articles"]}\n'
                        f'🆕 Новых статей добавлено: {result["new_articles"]}\n'
                        f'🌐 Успешных источников: {result["successful_sources"]}'
                    )
                )

                if result['errors']:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️ Предупреждения:\n' + '\n'.join(result['errors'])
                        )
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Ошибка парсинга: {result["error"]}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Критическая ошибка: {str(e)}')
            )
