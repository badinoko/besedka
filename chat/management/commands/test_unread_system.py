from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Room, Message, UserChatPosition
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Тестирование системы непрочитанных сообщений'

    def add_arguments(self, parser):
        parser.add_argument('--clear-positions', action='store_true', help='Очистить все позиции пользователей')
        parser.add_argument('--add-messages', type=int, default=5, help='Количество новых сообщений для добавления')

    def handle(self, *args, **options):

        if options['clear_positions']:
            self.stdout.write('=== ОЧИСТКА ПОЗИЦИЙ ПОЛЬЗОВАТЕЛЕЙ ===')
            positions_count = UserChatPosition.objects.count()
            UserChatPosition.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Удалено {positions_count} позиций. Все пользователи теперь как новые!')
            )

        # Добавляем новые тестовые сообщения
        messages_count = options['add_messages']
        if messages_count > 0:
            self.stdout.write(f'\n=== ДОБАВЛЕНИЕ {messages_count} НОВЫХ СООБЩЕНИЙ ===')

            # Получаем owner пользователя
            try:
                owner = User.objects.get(role='owner')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR('Owner пользователь не найден!'))
                return

            # Добавляем сообщения в общий чат
            general_room, _ = Room.objects.get_or_create(name='general')
            for i in range(1, messages_count + 1):
                Message.objects.create(
                    room=general_room,
                    author=owner,
                    content=f"🧪 Тестовое сообщение #{i} для проверки разделителя непрочитанных (общий чат)"
                )

            # Добавляем сообщения в VIP чат
            vip_room, _ = Room.objects.get_or_create(name='vip')
            for i in range(1, messages_count + 1):
                Message.objects.create(
                    room=vip_room,
                    author=owner,
                    content=f"💎 VIP тестовое сообщение #{i} для проверки разделителя (VIP чат)"
                )

            self.stdout.write(
                self.style.SUCCESS(f'✅ Добавлено {messages_count} сообщений в общий чат')
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Добавлено {messages_count} сообщений в VIP чат')
            )

        # Показываем статистику
        self.stdout.write('\n=== СТАТИСТИКА ЧАТОВ ===')
        general_count = Message.objects.filter(room__name='general', is_deleted=False).count()
        vip_count = Message.objects.filter(room__name='vip', is_deleted=False).count()
        positions_count = UserChatPosition.objects.count()

        self.stdout.write(f'📊 Общий чат: {general_count} сообщений')
        self.stdout.write(f'💎 VIP чат: {vip_count} сообщений')
        self.stdout.write(f'👥 Позиций пользователей: {positions_count}')

        self.stdout.write('\n🎯 ИНСТРУКЦИИ ПО ТЕСТИРОВАНИЮ:')
        self.stdout.write('1. Зайдите в чат - вы будете как "новый пользователь"')
        self.stdout.write('2. Разделитель НЕ должен появиться (0 непрочитанных для новых)')
        self.stdout.write('3. Кто-то другой отправит сообщение - появится разделитель')
        self.stdout.write('4. Прокрутите и подождите 2 сек - разделитель исчезнет')
