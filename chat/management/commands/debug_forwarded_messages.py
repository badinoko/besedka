from django.core.management.base import BaseCommand
from chat.models import Message

class Command(BaseCommand):
    help = 'Диагностика пересланных сообщений'

    def handle(self, *args, **options):
                # Найти все сообщения помеченные как пересланные
        forwarded_messages = Message.objects.filter(is_forwarded=True)

        self.stdout.write(f"Найдено пересланных сообщений: {forwarded_messages.count()}")

        for msg in forwarded_messages[:10]:  # Первые 10
            self.stdout.write(f"ID: {msg.id}")
            self.stdout.write(f"Автор: {msg.author.display_name}")
            self.stdout.write(f"Содержимое: {msg.content[:100]}...")
            self.stdout.write(f"is_forwarded: {msg.is_forwarded}")
            self.stdout.write(f"original_message_id: {msg.original_message_id}")
            self.stdout.write("---")

        # Найти сообщения которые содержат "Переслано" но НЕ помечены как пересланные
        maybe_forwarded = Message.objects.filter(
            content__icontains='Переслано из',
            is_forwarded=False
        )

        self.stdout.write(f"Сообщения с 'Переслано из' но is_forwarded=False: {maybe_forwarded.count()}")

        for msg in maybe_forwarded[:5]:
            self.stdout.write(f"ID: {msg.id} - {msg.content[:50]}...")
