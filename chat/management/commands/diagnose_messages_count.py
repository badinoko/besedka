from django.core.management.base import BaseCommand
from chat.models import Room, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Диагностика количества сообщений в чатах'

    def handle(self, *args, **options):
        for room_name in ['general', 'vip']:
            room = Room.objects.get(name=room_name)

            # Статистика сообщений
            total_messages = room.messages.count()
            active_messages = room.messages.filter(is_deleted=False).count()
            deleted_messages = room.messages.filter(is_deleted=True).count()
            forwarded_messages = room.messages.filter(is_forwarded=True).count()
            reply_messages = room.messages.exclude(parent=None).count()

            # Последние 50 согласно логике consumers.py
            last_50_query = room.messages.filter(is_deleted=False).select_related(
                'author', 'parent', 'parent__author'
            ).order_by('-created_at')[:50]

            last_50_count = last_50_query.count()

            self.stdout.write(f'\n📊 {room_name.upper()} CHAT:')
            self.stdout.write(f'├─ Всего сообщений: {total_messages}')
            self.stdout.write(f'├─ Активных (не удаленных): {active_messages}')
            self.stdout.write(f'├─ Удаленных: {deleted_messages}')
            self.stdout.write(f'├─ Пересланных: {forwarded_messages}')
            self.stdout.write(f'├─ Ответов: {reply_messages}')
            self.stdout.write(f'└─ Последние 50 активных (логика consumers.py): {last_50_count}')

            # Проверяем первые 5 сообщений из выборки
            self.stdout.write(f'\n🔍 Первые 5 сообщений из последних 50:')
            for i, msg in enumerate(last_50_query[:5]):
                self.stdout.write(f'├─ {i+1}. ID: {str(msg.id)[:8]}... | Автор: {msg.author.username} | Удалено: {msg.is_deleted} | Переслано: {msg.is_forwarded} | Ответ: {bool(msg.parent)}')
