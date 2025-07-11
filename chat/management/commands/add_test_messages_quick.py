from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import ChatRoom, ChatMessage
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Добавляет 20 быстрых тестовых сообщений для тестирования навигации'

    def add_arguments(self, parser):
        parser.add_argument(
            '--room',
            type=str,
            default='general',
            help='Название комнаты (general или vip)',
        )

    def handle(self, *args, **options):
        room_name = options['room']

        try:
            room = ChatRoom.objects.get(name=room_name)
            user = User.objects.get(username='admin')
        except (ChatRoom.DoesNotExist, User.DoesNotExist) as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка: {e}')
            )
            return

        # Добавляем 20 сообщений с интервалом в 1 минуту назад
        messages_added = 0
        base_time = timezone.now()

        quick_messages = [
            "🚀 Тестовое сообщение для навигации",
            "📍 Проверяем систему позиционирования",
            "⬇️ Тестируем кнопку навигации вниз",
            "🎯 Отладка системы скроллинга",
            "📬 Проверка системы непрочитанных",
            "🔧 Диагностика работы чата",
            "💫 Тестирование плавной прокрутки",
            "🎪 Проверяем возврат к позиции",
            "⚡ Быстрая навигация работает?",
            "🏠 Тест возвращения домой в чат",
            "🔄 Система обновления позиции",
            "📊 Тестовые данные для отладки",
            "🎭 Проверка отображения сообщений",
            "🌟 Навигация по истории чата",
            "🔍 Поиск оптимальной позиции",
            "🎨 Красивая система навигации",
            "⭐ Финальный тест позиционирования",
            "🎉 Завершение тестовых сообщений",
            "✅ Последнее сообщение для теста",
            "🏆 Система навигации готова!"
        ]

        for i, message_text in enumerate(quick_messages):
            # Сообщения идут с интервалом 30 секунд назад от текущего времени
            created_time = base_time - timezone.timedelta(minutes=len(quick_messages) - i)

            message = ChatMessage.objects.create(
                room=room,
                author=user,
                content=f"{message_text} #{len(quick_messages) - i}",
                created_at=created_time
            )
            messages_added += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Добавлено {messages_added} тестовых сообщений в комнату "{room_name}"'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '🔄 Перезапустите Django контейнер для обновления WebSocket кеша'
            )
        )
