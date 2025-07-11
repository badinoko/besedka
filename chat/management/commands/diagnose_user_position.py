from django.core.management.base import BaseCommand
from chat.models import Room, Message, UserChatPosition
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Диагностика позиции пользователя и логики непрочитанных сообщений'

    def handle(self, *args, **options):
        owner = User.objects.get(username='owner')

        # Диагностика по каждому чату
        for room_name in ['general', 'vip']:
            room = Room.objects.get(name=room_name)
            position, created = UserChatPosition.objects.get_or_create(
                user=owner,
                room=room
            )

            self.stdout.write(f"\n🔍 ДИАГНОСТИКА ЧАТА '{room_name.upper()}':")
            self.stdout.write(f"├─ Всего сообщений в чате: {room.messages.count()}")
            self.stdout.write(f"├─ Позиция пользователя создана: {'ДА' if not created else 'ТОЛЬКО ЧТО'}")
            self.stdout.write(f"├─ last_read_at: {position.last_read_at}")
            self.stdout.write(f"├─ last_message_id: {position.last_message_id}")
            self.stdout.write(f"├─ Кешированный unread_count: {position.unread_count}")

            # Вычисляем актуальное количество непрочитанных
            actual_unread = position.get_unread_messages_count()
            self.stdout.write(f"├─ Актуальный unread_count: {actual_unread}")

            # Получаем первое непрочитанное сообщение
            first_unread = position.get_first_unread_message()
            if first_unread:
                self.stdout.write(f"├─ Первое непрочитанное: {first_unread.content[:50]}...")
                self.stdout.write(f"├─ Создано: {first_unread.created_at}")
            else:
                self.stdout.write(f"├─ Первое непрочитанное: НЕТ")

            # Показываем последние 3 сообщения
            last_messages = room.messages.order_by('-created_at')[:3]
            self.stdout.write(f"└─ Последние 3 сообщения:")
            for i, msg in enumerate(last_messages, 1):
                is_read = "✅ ПРОЧИТАНО" if position.last_read_at and msg.created_at <= position.last_read_at else "❌ НЕПРОЧИТАНО"
                self.stdout.write(f"   {i}. {msg.content[:30]}... | {msg.created_at} | {is_read}")
