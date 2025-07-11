from django.core.management.base import BaseCommand
from chat.models import Room, Message
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает новые тестовые сообщения для проверки системы непрочитанных'

    def handle(self, *args, **options):
        owner = User.objects.get(username='owner')

        # Создаем 3 новых сообщения в общем чате
        general_room = Room.objects.get(name='general')
        for i in range(1, 4):
            Message.objects.create(
                room=general_room,
                author=owner,
                content=f'🆕 НОВОЕ тестовое сообщение #{i} - создано {timezone.now().strftime("%H:%M:%S")} для проверки системы непрочитанных'
            )

        # Создаем 2 новых сообщения в VIP чате
        vip_room = Room.objects.get(name='vip')
        for i in range(1, 3):
            Message.objects.create(
                room=vip_room,
                author=owner,
                content=f'🆕 VIP: НОВОЕ тестовое сообщение #{i} - создано {timezone.now().strftime("%H:%M:%S")} для проверки системы непрочитанных'
            )

        self.stdout.write(
            self.style.SUCCESS('✅ Созданы новые тестовые сообщения')
        )
        self.stdout.write(f'Общий чат: {general_room.messages.count()} сообщений')
        self.stdout.write(f'VIP чат: {vip_room.messages.count()} сообщений')
