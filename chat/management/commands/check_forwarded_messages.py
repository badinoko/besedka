from django.core.management.base import BaseCommand
from chat.models import Message

class Command(BaseCommand):
    help = 'Проверяет пересланные сообщения в БД'

    def handle(self, *args, **options):
        # Ищем все пересланные сообщения
        forwarded_messages = Message.objects.filter(
            content__icontains='Переслано'
        ).order_by('-created_at')[:10]

        self.stdout.write(self.style.SUCCESS('Найдено пересланных сообщений: %d' % len(forwarded_messages)))

        for i, msg in enumerate(forwarded_messages, 1):
            self.stdout.write(f"\n--- Сообщение {i} (ID: {msg.id}) ---")
            self.stdout.write(f"Автор: {msg.author.display_name}")
            self.stdout.write(f"Содержимое:")
            self.stdout.write(msg.content)
            self.stdout.write("-" * 50)
