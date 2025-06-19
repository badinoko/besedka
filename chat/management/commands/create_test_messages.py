from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Room, Message, GlobalChatRoom, VIPChatRoom

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает тестовые сообщения с ответами в чате'

    def handle(self, *args, **options):
        # Получаем или создаем пользователей
        owner, _ = User.objects.get_or_create(
            username='owner',
            defaults={'email': 'owner@test.com', 'name': 'Владелец', 'is_staff': True}
        )

        test_user, _ = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@test.com', 'name': 'Тестовый пользователь'}
        )

        store_owner, _ = User.objects.get_or_create(
            username='store_owner',
            defaults={'email': 'store@test.com', 'name': 'Владелец магазина', 'role': 'store_owner'}
        )

        # Устанавливаем роли
        if owner.role != 'owner':
            owner.role = 'owner'
            owner.save()

        if test_user.role != 'user':
            test_user.role = 'user'
            test_user.save()

        if store_owner.role != 'store_owner':
            store_owner.role = 'store_owner'
            store_owner.save()

        # Получаем или создаем общий чат
        general_chat = GlobalChatRoom.get_or_create_default()
        general_room = general_chat.room

        # Получаем или создаем VIP чат
        vip_chat = VIPChatRoom.get_or_create_default(created_by=owner)
        vip_room = vip_chat.room

        # Добавляем участников в VIP чат
        if not vip_chat.can_access(store_owner):
            vip_chat.add_member(store_owner, invited_by=owner)

        # Создаем тестовые сообщения в общем чате
        self.stdout.write('Создаю тестовые сообщения в общем чате...')

        # Исходное сообщение от test_user
        original_msg = Message.objects.create(
            author=test_user,
            room=general_room,
            content='Спасибо за советы по освещению! Мои растения заметно оживились после смены ламп.'
        )

        # Ответ от store_owner
        reply_msg = Message.objects.create(
            author=store_owner,
            room=general_room,
            content='@test_user Отлично! А какие лампы используете сейчас? Поделитесь опытом!',
            reply_to=original_msg
        )

        # Новое сообщение для тестирования ответов
        test_msg = Message.objects.create(
            author=test_user,
            room=general_room,
            content='Кто-нибудь пробовал выращивать томаты в гидропонике? Поделитесь опытом!'
        )

        # Ответ от owner на тестовое сообщение
        reply_to_test = Message.objects.create(
            author=owner,
            room=general_room,
            content='@test_user еще один ответ',
            reply_to=test_msg
        )

        # Создаем тестовые сообщения в VIP чате
        self.stdout.write('Создаю тестовые сообщения в VIP чате...')

        # Исходное сообщение в VIP чате
        vip_original = Message.objects.create(
            author=store_owner,
            room=vip_room,
            content='Отвечаете VIP участнику store_owner'
        )

        # Ответ от owner в VIP чате
        vip_reply = Message.objects.create(
            author=owner,
            room=vip_room,
            content='@store_owner ОТВЕЧАЮ',
            reply_to=vip_original
        )

        # Еще одно сообщение для тестирования
        test_vip_msg = Message.objects.create(
            author=owner,
            room=vip_room,
            content='ТЕСТОВОЕ СООБЩЕНИЕ ПОСЛЕ ПРИМЕНЕНИЯ ИЗМЕНЕНИЙ'
        )

        # Дополнительные тестовые сообщения с ответами для демонстрации
        self.stdout.write('Создаю дополнительные сообщения с ответами...')

        # Сообщение от Buddy для ответа
        buddy_msg = Message.objects.create(
            author=owner,
            room=general_room,
            content='Посоветуйте лучшие удобрения для органического выращивания огурцов.'
        )

        # Ответ test_user на Buddy
        reply_to_buddy = Message.objects.create(
            author=test_user,
            room=general_room,
            content='@Buddy Рекомендую компост собственного приготовления и биогумус. Отличные результаты!',
            reply_to=buddy_msg
        )

        # Ответ store_owner на предыдущее сообщение test_user
        reply_chain = Message.objects.create(
            author=store_owner,
            room=general_room,
            content='@test_user Согласен полностью! В нашем магазине есть качественный биогумус от проверенных поставщиков.',
            reply_to=reply_to_buddy
        )

        # Новое сообщение от test_user
        test_question = Message.objects.create(
            author=test_user,
            room=general_room,
            content='Какая оптимальная температура для проращивания семян перца?'
        )

        # Ответ от store_owner
        pepper_answer = Message.objects.create(
            author=store_owner,
            room=general_room,
            content='@test_user Для перца оптимально 25-27°C. При такой температуре всходы появятся через 7-10 дней.',
            reply_to=test_question
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Создано {Message.objects.count()} сообщений:\n'
                f'- Общий чат: {general_room.room_messages.count()} сообщений\n'
                f'- VIP чат: {vip_room.room_messages.count()} сообщений\n'
                f'- Ответов создано: {Message.objects.filter(reply_to__isnull=False).count()}'
            )
        )
