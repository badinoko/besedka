import os
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Архивирует основной файл прогресса и очищает его для новых записей.'

    def handle(self, *args, **options):
        progress_file_path = os.path.join(settings.BASE_DIR, 'docs', 'CUSTOM_CHAT_DEVELOPMENT_PROGRESS.md')
        archive_file_path = os.path.join(settings.BASE_DIR, 'docs', 'CUSTOM_CHAT_DEVELOPMENT_PROGRESS_ARCHIVE.md')

        try:
            # Читаем содержимое основного файла прогресса
            with open(progress_file_path, 'r', encoding='utf-8') as f:
                progress_content = f.read()

            # Разделяем заголовок и тело
            header_end_pos = progress_content.find('---') + 3
            if header_end_pos == 2: # Если '---' не найдено
                self.stdout.write(self.style.WARNING('Не удалось найти разделитель "---" в файле прогресса. Архивация отменена.'))
                return

            header_content = progress_content[:header_end_pos]
            body_content_to_archive = progress_content[header_end_pos:].strip()

            if not body_content_to_archive:
                self.stdout.write(self.style.SUCCESS('✅ Основной файл прогресса уже пуст. Архивировать нечего.'))
                return

            # Добавляем содержимое в архивный файл
            with open(archive_file_path, 'a', encoding='utf-8') as f:
                archive_separator = f"\\n\\n---\\n\\n## Архив от {datetime.now().strftime('%d %B %Y')}\\n\\n---\\n"
                f.write(archive_separator)
                f.write(body_content_to_archive)

            self.stdout.write(self.style.SUCCESS(f'✅ Успешно добавлено {len(body_content_to_archive.splitlines())} строк в архив.'))

            # Очищаем основной файл прогресса, оставляя только заголовок
            new_progress_header = f"""# 📋 Журнал разработки кастомного чата "Беседка" (АКТУАЛЬНЫЙ)

**Дата создания журнала:** 26 июня 2025
**Последнее обновление:** {datetime.now().strftime('%d %B %Y')}

---
"""
            with open(progress_file_path, 'w', encoding='utf-8') as f:
                f.write(new_progress_header)

            self.stdout.write(self.style.SUCCESS('✅ Основной файл прогресса очищен и готов к новым записям.'))

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: Файл не найден - {e.filename}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Произошла непредвиденная ошибка: {e}'))
