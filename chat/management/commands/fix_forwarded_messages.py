from django.core.management.base import BaseCommand
from chat.models import Message

class Command(BaseCommand):
    help = 'Исправляет неправильно помеченные пересланные сообщения'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтвердить исправление без интерактивного запроса',
        )

    def handle(self, *args, **options):
        # Найти сообщения помеченные как пересланные но НЕ начинающиеся с префикса
        wrong_forwarded = Message.objects.filter(
            is_forwarded=True
        ).exclude(
            content__startswith='📤 Переслано из «'
        ).exclude(
            content__startswith='Переслано из «'
        )

        count = wrong_forwarded.count()
        self.stdout.write(f"Найдено неправильно помеченных сообщений: {count}")

        if count > 0:
            # Показать что будет исправлено
            for msg in wrong_forwarded[:5]:
                self.stdout.write(f"ID: {msg.id} - '{msg.content[:50]}...'")

                        # Подтверждение
            if options['confirm']:
                confirm_action = True
            else:
                confirm = input(f"Исправить {count} сообщений? (yes/no): ")
                confirm_action = confirm.lower() == 'yes'

            if confirm_action:
                # Исправить - убрать флаг is_forwarded и очистить original_message_id
                updated = wrong_forwarded.update(
                    is_forwarded=False,
                    original_message_id=None
                )

                self.stdout.write(self.style.SUCCESS(f"Исправлено {updated} сообщений"))
            else:
                self.stdout.write("Отменено")
        else:
            self.stdout.write("Неправильных сообщений не найдено")
