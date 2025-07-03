from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Room, Message
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Добавляет дополнительные тестовые сообщения в существующие комнаты чата'

    def handle(self, *args, **options):
        # Получаем или создаем пользователей
        owner, _ = User.objects.get_or_create(
            username='owner',
            defaults={'email': 'owner@test.com', 'name': 'Buddy', 'role': 'owner'}
        )

        test_user, _ = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@test.com', 'name': 'test_user', 'role': 'user'}
        )

        # Создаем дополнительного пользователя для разнообразия
        user2, _ = User.objects.get_or_create(
            username='user2',
            defaults={'email': 'user2@test.com', 'name': 'User2', 'role': 'user'}
        )

        # Устанавливаем правильные роли
        if owner.role != 'owner':
            owner.role = 'owner'
            owner.save()

        # Получаем существующие комнаты
        try:
            general_room = Room.objects.get(name='general')
        except Room.DoesNotExist:
            general_room = Room.objects.create(name='general', description='Общий чат')

        try:
            vip_room = Room.objects.get(name='vip')
        except Room.DoesNotExist:
            vip_room = Room.objects.create(name='vip', description='VIP чат')

        # Новые тестовые сообщения для общего чата
        general_messages = [
            "Добро пожаловать в обновленный чат! Проверяем систему непрочитанных сообщений 🚀",
            "Это второе тестовое сообщение для проверки скроллинга",
            "Третье сообщение - проверяем разделитель непрочитанных",
            "Четвертое сообщение добавлено для тестирования навигации",
            "Пятое сообщение - тестируем автоскроллинг к непрочитанным",
            "Шестое сообщение поможет проверить систему отметки прочтения",
            "Седьмое сообщение для полноценного тестирования всех функций",
            "Восьмое сообщение - последнее в серии тестовых сообщений",
        ]

        # VIP сообщения
        vip_messages = [
            "🎉 VIP чат обновлен! Проверяем систему непрочитанных",
            "💎 Второе VIP сообщение для тестирования",
            "👑 Третье эксклюзивное сообщение в VIP чате",
            "🏆 Четвертое VIP сообщение - тестируем навигацию",
            "⭐ Пятое премиум сообщение для VIP участников",
        ]

        users = [owner, test_user, user2]

        self.stdout.write('Добавляю новые тестовые сообщения в общий чат...')

        # Добавляем сообщения в общий чат с разными авторами
        for i, content in enumerate(general_messages):
            author = users[i % len(users)]  # Чередуем авторов

            Message.objects.create(
                author=author,
                room=general_room,
                content=content,
                created_at=timezone.now() + timezone.timedelta(seconds=i*10)  # Разные времена
            )

        self.stdout.write('Добавляю новые тестовые сообщения в VIP чат...')

        # Добавляем сообщения в VIP чат
        for i, content in enumerate(vip_messages):
            # В VIP чате только owner и test_user
            author = owner if i % 2 == 0 else test_user

            Message.objects.create(
                author=author,
                room=vip_room,
                content=content,
                created_at=timezone.now() + timezone.timedelta(seconds=i*15)  # Разные времена
            )

        # Обновляем статистику
        total_messages = Message.objects.count()
        general_count = general_room.messages.count()
        vip_count = vip_room.messages.count()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Тестовые сообщения добавлены!\n'
                f'📊 Общая статистика:\n'
                f'   • Всего сообщений в базе: {total_messages}\n'
                f'   • В общем чате: {general_count} сообщений\n'
                f'   • В VIP чате: {vip_count} сообщений\n'
                f'   • Добавлено в общий: {len(general_messages)} новых\n'
                f'   • Добавлено в VIP: {len(vip_messages)} новых\n\n'
                f'🔍 Теперь можно тестировать систему непрочитанных сообщений!'
            )
        )
