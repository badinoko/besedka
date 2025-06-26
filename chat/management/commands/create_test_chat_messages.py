from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Room, Message
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает тестовые сообщения в чатах от пользователей с разными ролями'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие сообщения перед созданием новых',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Message.objects.all().delete()
            self.stdout.write('🧹 Все сообщения очищены')

        # Создаем комнаты если их нет
        general_room, _ = Room.objects.get_or_create(name='general')
        vip_room, _ = Room.objects.get_or_create(name='vip')

        # Тестовые сообщения для общего чата
        general_messages = [
            ("owner", "👑 Добро пожаловать в нашу Беседку! Здесь мы обсуждаем все что связано с растениеводством."),
            ("user_test1", "Привет всем! Новичок тут, подскажите с чего лучше начать?"),
            ("moderator", "🛡️ @user_test1 Добро пожаловать! Рекомендую начать с изучения раздела 'Новости' - там много полезной информации."),
            ("store_admin", "📦 Кстати, у нас есть стартовые наборы для новичков в магазине. Очень удобно!"),
            ("user_test2", "А я уже третий год выращиваю томаты. Если есть вопросы - спрашивайте!"),
            ("store_owner", "🏪 Скоро поступление новых сортов семян. Следите за обновлениями!"),
            ("user_test1", "Спасибо за теплый прием! Очень рад быть частью сообщества."),
            ("moderator", "🛡️ Напоминаю всем о правилах чата - будьте вежливы и помогайте друг другу!"),
        ]

        # Тестовые сообщения для VIP чата
        vip_messages = [
            ("owner", "👑 VIP чат для особых обсуждений и эксклюзивной информации."),
            ("moderator", "🛡️ Здесь мы можем обсуждать новые функции сайта и делиться инсайдерской информацией."),
            ("store_owner", "🏪 Планируем запустить программу лояльности для VIP участников."),
            ("owner", "👑 Отличная идея! Также думаю над созданием закрытых мастер-классов."),
            ("moderator", "🛡️ Предлагаю еженедельные Q&A сессии только для VIP участников."),
        ]

        # Создаем сообщения в общем чате
        for i, (username, text) in enumerate(general_messages):
            try:
                user = User.objects.get(username=username)
                Message.objects.create(
                    room=general_room,
                    author=user,
                    content=text,
                    created_at=timezone.now() - timezone.timedelta(minutes=len(general_messages)-i)
                )
            except User.DoesNotExist:
                self.stdout.write(f'⚠️ Пользователь {username} не найден')

        # Создаем сообщения в VIP чате
        for i, (username, text) in enumerate(vip_messages):
            try:
                user = User.objects.get(username=username)
                Message.objects.create(
                    room=vip_room,
                    author=user,
                    content=text,
                    created_at=timezone.now() - timezone.timedelta(minutes=len(vip_messages)-i)
                )
            except User.DoesNotExist:
                self.stdout.write(f'⚠️ Пользователь {username} не найден')

        self.stdout.write('✅ Тестовые сообщения созданы успешно!')
        self.stdout.write(f'📊 Общий чат: {len(general_messages)} сообщений')
        self.stdout.write(f'👑 VIP чат: {len(vip_messages)} сообщений')
        self.stdout.write('💡 Используйте --clear для очистки сообщений перед повторным запуском')
