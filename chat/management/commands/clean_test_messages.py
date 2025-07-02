import re
from django.core.management.base import BaseCommand
from django.db import transaction
from chat.models import Message

class Command(BaseCommand):
    help = 'Очищает отладочные данные "ТЕСТ" из старых сообщений чата'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет изменено без фактических изменений',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.SUCCESS('🔍 Поиск сообщений с отладочными данными "ТЕСТ"...')
        )

        # Ищем сообщения содержащие "ТЕСТ"
        test_messages = Message.objects.filter(
            content__icontains='ТЕСТ',
            is_deleted=False
        ).select_related('author', 'room')

        if not test_messages.exists():
            self.stdout.write(
                self.style.WARNING('📭 Сообщения с "ТЕСТ" не найдены.')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'📊 Найдено {test_messages.count()} сообщений с "ТЕСТ"')
        )

        cleaned_count = 0

        for message in test_messages:
            original_content = message.content

            # Очищаем различные варианты отладочного текста
            cleaned_content = original_content

            # Убираем "ТЕСТ" и варианты
            patterns_to_remove = [
                r'^\s*ТЕСТ\s*$',  # Строка содержащая только "ТЕСТ"
                r'^\s*тест\s*$',  # Строка содержащая только "тест"
                r'^\s*Test\s*$',  # Строка содержащая только "Test"
                r'^\s*test\s*$',  # Строка содержащая только "test"
                r'\[ТЕСТ\]',      # В квадратных скобках
                r'\[тест\]',
                r'\(ТЕСТ\)',      # В круглых скобках
                r'\(тест\)',
                r'ТЕСТ:\s*',      # С двоеточием в начале строки
                r'тест:\s*',
                r'^ТЕСТ\s+',      # В начале строки с пробелом
                r'^тест\s+',
                r'\bТЕСТ\b(?=\s|$)',  # Отдельное слово в конце строки или перед пробелом
                r'\bтест\b(?=\s|$)',
            ]

            for pattern in patterns_to_remove:
                cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE)

            # Убираем лишние пробелы и переносы строк
            cleaned_content = re.sub(r'\n\s*\n', '\n', cleaned_content)  # Убираем пустые строки
            cleaned_content = re.sub(r'^\s+', '', cleaned_content, flags=re.MULTILINE)  # Убираем пробелы в начале строк
            cleaned_content = cleaned_content.strip()

            # Если контент изменился
            if cleaned_content != original_content and cleaned_content:
                if dry_run:
                    self.stdout.write(
                        f'📝 [DRY RUN] Сообщение {message.id} в {message.room.name}:'
                    )
                    self.stdout.write(f'   ❌ Было: "{original_content[:100]}..."')
                    self.stdout.write(f'   ✅ Будет: "{cleaned_content[:100]}..."')
                    self.stdout.write('')
                else:
                    # Обновляем сообщение
                    message.content = cleaned_content
                    message.save()

                    self.stdout.write(
                        f'✅ Очищено сообщение {message.id} от {message.author.display_name}'
                    )

                cleaned_count += 1

            elif not cleaned_content:
                # Если после очистки ничего не осталось - помечаем как удаленное
                if dry_run:
                    self.stdout.write(
                        f'🗑️ [DRY RUN] Сообщение {message.id} будет помечено как удаленное (пустое после очистки)'
                    )
                else:
                    message.is_deleted = True
                    message.content = "[Сообщение удалено]"
                    message.save()

                    self.stdout.write(
                        f'🗑️ Сообщение {message.id} помечено как удаленное (было пустым после очистки)'
                    )

                cleaned_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'📊 [DRY RUN] Будет обработано {cleaned_count} сообщений')
            )
            self.stdout.write(
                self.style.SUCCESS('💡 Запустите без --dry-run для применения изменений')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Обработано {cleaned_count} сообщений!')
            )

            if cleaned_count > 0:
                self.stdout.write(
                    self.style.SUCCESS('🎉 Отладочные данные "ТЕСТ" успешно очищены!')
                )
