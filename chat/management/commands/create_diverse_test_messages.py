from django.core.management.base import BaseCommand
from django.utils import timezone
from chat.models import Room, Message, UserChatPosition
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает разнообразные тестовые сообщения для проверки системы уведомлений'

    def add_arguments(self, parser):
        parser.add_argument('--room', type=str, default='general', help='Название комнаты')
        parser.add_argument('--reset-position', action='store_true', help='Сбросить позицию owner')

    def handle(self, *args, **options):
        room_name = options['room']
        reset_position = options['reset_position']

        try:
            # Получаем пользователей и комнату
            owner = User.objects.get(username='owner')
            test_user = User.objects.get(username='test_user')
            room = Room.objects.get(name=room_name)

            self.stdout.write(f'Найдены пользователи: {owner.username}, {test_user.username}')
            self.stdout.write(f'Комната: {room.name}')

            # Сбрасываем позицию owner если указано
            if reset_position:
                position, created = UserChatPosition.objects.get_or_create(user=owner, room=room)
                old_time = timezone.now() - timedelta(hours=1)
                position.last_visit_at = old_time
                position.last_read_at = old_time
                position.save()
                self.stdout.write(f'Сброшена позиция owner на: {old_time}')

            # Создаем разнообразную базу сообщений
            messages_data = [
                # БЛОК 1: Обычные сообщения
                ('test_user', 'Привет всем! Как дела?'),
                ('test_user', 'Сегодня отличная погода для выращивания'),
                ('test_user', 'Кто-нибудь пробовал новые семена?'),
                ('test_user', 'У меня растения прекрасно развиваются'),
                ('test_user', 'Поделюсь фотографиями через неделю'),

                # БЛОК 2: Упоминания owner
                ('test_user', '@owner Можешь посоветовать удобрения?'),
                ('test_user', '@owner Привет! Как твои дела с проектом?'),
                ('test_user', 'Думаю @owner согласится с моим мнением'),

                # БЛОК 3: Еще обычные сообщения
                ('test_user', 'Читал интересную статью о гидропонике'),
                ('test_user', 'Хочу попробовать новую технологию'),
                ('test_user', 'LED лампы действительно эффективны'),
                ('test_user', 'Температура в гроубоксе оптимальная'),

                # БЛОК 4: Больше упоминаний
                ('test_user', '@owner А что думаешь о CO2?'),
                ('test_user', 'Кстати, @owner, спасибо за совет вчера'),
                ('test_user', '@owner Можешь глянуть на мои растения?'),

                # БЛОК 5: Обычные сообщения
                ('test_user', 'Урожай в этом месяце отличный'),
                ('test_user', 'Влажность держу на уровне 65%'),
                ('test_user', 'pH проверяю каждый день'),
                ('test_user', 'Питательный раствор меняю раз в неделю'),

                # БЛОК 6: Финальные упоминания
                ('test_user', '@owner Когда планируешь новый гайд?'),
                ('test_user', 'Всем рекомендую советы от @owner'),
            ]

            # Создаем сообщения с небольшими интервалами
            created_messages = []
            base_time = timezone.now() - timedelta(minutes=len(messages_data))

            for i, (author_name, content) in enumerate(messages_data):
                author = User.objects.get(username=author_name)
                message_time = base_time + timedelta(minutes=i)

                message = Message.objects.create(
                    room=room,
                    author=author,
                    content=content,
                    created_at=message_time
                )
                created_messages.append(message)

            self.stdout.write(f'Создано {len(created_messages)} разнообразных сообщений')

            # Создаем ответы на некоторые сообщения owner (имитируем что у owner были сообщения ранее)
            owner_messages = Message.objects.filter(room=room, author=owner).order_by('-created_at')[:3]

            replies_created = 0
            if owner_messages:
                for i, owner_msg in enumerate(owner_messages):
                    reply_time = timezone.now() - timedelta(minutes=5-i)
                    reply = Message.objects.create(
                        room=room,
                        author=test_user,
                        content=f'Отвечаю на твое сообщение! Полностью согласен.',
                        parent=owner_msg,
                        created_at=reply_time
                    )
                    replies_created += 1
                    self.stdout.write(f'Создан ответ на сообщение {owner_msg.id}')

            # Проверяем финальные счетчики
            position, created = UserChatPosition.objects.get_or_create(user=owner, room=room)
            unread_count = position.get_unread_messages_count()
            personal_count = position.get_personal_notifications_count()
            mentions_count = len([msg for msg in created_messages if '@owner' in msg.content])

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('ИТОГОВАЯ СТАТИСТИКА:'))
            self.stdout.write(f'Всего новых сообщений: {len(created_messages)}')
            self.stdout.write(f'Ответов создано: {replies_created}')
            self.stdout.write(f'Упоминаний: {mentions_count}')
            self.stdout.write(f'Непрочитанных: {unread_count}')
            self.stdout.write(f'Персональных уведомлений: {personal_count}')

        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Пользователь не найден: {e}'))
        except Room.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Комната не найдена: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
