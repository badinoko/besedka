from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import Room, Message
from users.models import User


class Command(BaseCommand):
    help = 'Создает тестовые сообщения с разными датами для проверки временных меток'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить все существующие сообщения перед созданием новых',
        )
        parser.add_argument(
            '--room',
            type=str,
            default='general',
            help='Название комнаты (general/vip)',
        )

    def handle(self, *args, **options):
        room_name = options['room']

        # Получаем пользователей
        try:
            owner = User.objects.get(username='owner')
            test_user = User.objects.get(username='test_user')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Не найдены пользователи owner или test_user')
            )
            return

        # Получаем или создаем комнату
        room, created = Room.objects.get_or_create(name=room_name)

        if options['clear']:
            deleted_count = Message.objects.filter(room=room).count()
            Message.objects.filter(room=room).delete()
            self.stdout.write(
                self.style.WARNING(f'Удалено {deleted_count} существующих сообщений')
            )

        # Текущее время
        now = timezone.now()

        # Определяем даты для тестирования
        test_dates = [
            # Сегодня - разное время
            (now - timedelta(hours=2), owner, "Привет! Как дела? (2 часа назад)"),
            (now - timedelta(hours=1), test_user, "Отлично! А у тебя как? (1 час назад)"),
            (now - timedelta(minutes=30), owner, "Тоже хорошо, работаю над проектом (30 минут назад)"),

            # Вчера
            (now - timedelta(days=1, hours=10), test_user, "Вчера была отличная погода!"),
            (now - timedelta(days=1, hours=15), owner, "Да, я тоже заметил. Хорошо погуляли"),

            # Позавчера
            (now - timedelta(days=2, hours=9), owner, "Позавчера купил новые семена в магазине"),
            (now - timedelta(days=2, hours=14), test_user, "Какие именно? Интересно посмотреть"),

            # 3 дня назад
            (now - timedelta(days=3, hours=12), test_user, "3 дня назад начал новый гров-репорт"),

            # 4 дня назад
            (now - timedelta(days=4, hours=8), owner, "4 дня назад обновили дизайн сайта"),

            # 5 дней назад
            (now - timedelta(days=5, hours=16), test_user, "5 дней назад нашел отличный рецепт удобрения"),

            # Неделю назад
            (now - timedelta(days=7, hours=11), owner, "Неделю назад запустили новую функцию чата"),
            (now - timedelta(days=7, hours=20), test_user, "Да, помню! Очень удобная штука"),

            # 10 дней назад
            (now - timedelta(days=10, hours=13), owner, "10 дней назад была конференция по садоводству"),

            # 2 недели назад
            (now - timedelta(days=14, hours=15), test_user, "2 недели назад получил отличный урожай!"),

            # Месяц назад
            (now - timedelta(days=30, hours=12), owner, "Месяц назад начали планировать этот проект"),
        ]

        created_messages = []

        for date, author, content in test_dates:
            message = Message.objects.create(
                room=room,
                author=author,
                content=content,
                created_at=date
            )
            created_messages.append(message)

        self.stdout.write(
            self.style.SUCCESS(
                f'Создано {len(created_messages)} тестовых сообщений в комнате "{room_name}"'
            )
        )

        # Показываем созданные сообщения для проверки
        self.stdout.write('\n📅 Созданные сообщения:')
        for msg in created_messages:
            # Рассчитываем разницу для проверки
            diff = now - msg.created_at
            days = diff.days
            hours = diff.seconds // 3600

            if days == 0:
                time_str = f"{hours}ч назад"
            elif days == 1:
                time_str = "вчера"
            elif days <= 6:
                time_str = f"{days}д назад"
            elif days <= 13:
                time_str = "неделю назад"
            else:
                time_str = f"{days}д назад"

            self.stdout.write(
                f"  • {msg.author.display_name}: {msg.content[:50]}... ({time_str})"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Тестовые сообщения созданы! Проверьте чат http://127.0.0.1:8001/chat/{room_name}/'
            )
        )
