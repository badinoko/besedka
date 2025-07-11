from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Room, Message
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает тестовые сообщения-ответы на сообщения от Buddy'

    def add_arguments(self, parser):
        parser.add_argument('--room', type=str, default='general', help='Имя комнаты (general/vip)')
        parser.add_argument('--count', type=int, default=5, help='Количество ответов на создание')

    def handle(self, *args, **options):
        room_name = options['room']
        count = options['count']

        # Получаем пользователей
        try:
            buddy = User.objects.get(username='owner')  # Buddy = owner
            test_user = User.objects.get(username='test_user')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Не найдены пользователи owner или test_user')
            )
            return

        # Получаем или создаем комнату
        room, created = Room.objects.get_or_create(name=room_name)

        # Находим существующие сообщения от Buddy
        buddy_messages = Message.objects.filter(
            room=room,
            author=buddy,
            is_deleted=False
        ).order_by('created_at')

        if not buddy_messages.exists():
            self.stdout.write(
                self.style.ERROR('Не найдены сообщения от Buddy для создания ответов')
            )
            return

        self.stdout.write(f'Найдено {buddy_messages.count()} сообщений от Buddy')

        # Создаем ответы на сообщения от Buddy
        created_replies = 0
        now = timezone.now()

        # Шаблоны ответов
        reply_templates = [
            "Отличный совет! Спасибо за информацию.",
            "Согласен полностью! У меня такой же опыт.",
            "Интересная точка зрения. Попробую применить.",
            "Buddy, а можешь поделиться подробностями?",
            "Это именно то, что я искал! Благодарю.",
            "Отличная идея! Обязательно попробую.",
            "Полезная информация, как всегда!",
            "Buddy, спасибо за развернутый ответ.",
            "Круто! Не знал об этом.",
            "Очень актуальная тема, спасибо!"
        ]

        for i, buddy_msg in enumerate(buddy_messages[:count]):
            # Создаем ответ от test_user на сообщение от Buddy
            reply_content = random.choice(reply_templates)

            # Добавляем временную задержку (от 1 до 10 минут после оригинального сообщения)
            reply_time = buddy_msg.created_at + timedelta(minutes=random.randint(1, 10))

            reply = Message.objects.create(
                room=room,
                author=test_user,
                content=reply_content,
                parent=buddy_msg,
                created_at=reply_time
            )

            created_replies += 1
            self.stdout.write(f'✅ Создан ответ на сообщение "{buddy_msg.content[:50]}..."')

        # Также создаем несколько сообщений с упоминаниями @Buddy
        mention_templates = [
            "@Buddy Привет! Как дела с новыми семенами?",
            "@Buddy Можешь посоветовать лучшие удобрения?",
            "@Buddy Спасибо за вчерашние советы!",
            "@Buddy Как думаешь, стоит попробовать гидропонику?",
            "@Buddy Твой совет по освещению очень помог!"
        ]

        mentions_created = 0
        for i, template in enumerate(mention_templates[:3]):  # Создаем 3 упоминания
            mention_time = now + timedelta(minutes=i * 2)

            mention = Message.objects.create(
                room=room,
                author=test_user,
                content=template,
                created_at=mention_time
            )

            mentions_created += 1
            self.stdout.write(f'✅ Создано упоминание: "{template}"')

        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Создано {created_replies} ответов на сообщения Buddy '
                f'и {mentions_created} упоминаний в чате {room_name}'
            )
        )

        # Показываем статистику
        total_messages = Message.objects.filter(room=room, is_deleted=False).count()
        replies_to_buddy = Message.objects.filter(
            room=room,
            parent__author=buddy,
            is_deleted=False
        ).count()
        mentions_of_buddy = Message.objects.filter(
            room=room,
            content__icontains='@Buddy',
            is_deleted=False
        ).count()

        self.stdout.write(f'\n📊 СТАТИСТИКА ЧАТА {room_name.upper()}:')
        self.stdout.write(f'├─ Всего сообщений: {total_messages}')
        self.stdout.write(f'├─ Ответов на сообщения Buddy: {replies_to_buddy}')
        self.stdout.write(f'└─ Упоминаний @Buddy: {mentions_of_buddy}')

        self.stdout.write(f'\n🎯 ГОТОВО К ТЕСТИРОВАНИЮ:')
        self.stdout.write(f'1. Зайдите в чат под пользователем Buddy')
        self.stdout.write(f'2. Должен появиться конверт с количеством персональных уведомлений')
        self.stdout.write(f'3. Клик на конверт должен переводить к сообщениям, требующим внимания')
