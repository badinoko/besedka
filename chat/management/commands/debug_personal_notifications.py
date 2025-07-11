from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Room, Message, UserChatPosition
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Диагностика системы персональных уведомлений'

    def add_arguments(self, parser):
        parser.add_argument('--room', type=str, default='general', help='Имя комнаты (general/vip)')
        parser.add_argument('--username', type=str, default='owner', help='Имя пользователя для проверки')

    def handle(self, *args, **options):
        room_name = options['room']
        username = options['username']

        try:
            # Получаем пользователя и комнату
            user = User.objects.get(username=username)
            room = Room.objects.get(name=room_name)
            position = UserChatPosition.objects.get(user=user, room=room)

            self.stdout.write(f"\n🔍 ДИАГНОСТИКА ПЕРСОНАЛЬНЫХ УВЕДОМЛЕНИЙ")
            self.stdout.write(f"Пользователь: {user.username} ({user.display_name})")
            self.stdout.write(f"Комната: {room.name}")
            self.stdout.write(f"last_visit_at: {position.last_visit_at}")
            self.stdout.write(f"last_read_at: {position.last_read_at}")

            # Получаем все сообщения после last_visit_at
            if position.last_visit_at:
                messages_after_visit = Message.objects.filter(
                    room=room,
                    created_at__gt=position.last_visit_at,
                    is_deleted=False
                ).exclude(author=user).order_by('created_at')
            else:
                self.stdout.write("\n❌ last_visit_at не установлен!")
                return

            self.stdout.write(f"\nСообщений после last_visit_at: {messages_after_visit.count()}")

            # Проверяем каждое сообщение
            personal_count = 0
            for msg in messages_after_visit:
                is_personal = msg.is_personal_notification_for(user)
                is_reply = msg.parent and msg.parent.author == user
                is_mention = msg.mentions_user(user)

                self.stdout.write(f"\n📝 Сообщение #{msg.id}")
                self.stdout.write(f"  Автор: {msg.author.display_name}")
                self.stdout.write(f"  Содержание: {msg.content[:50]}...")
                self.stdout.write(f"  Является ответом на мое сообщение: {is_reply}")
                self.stdout.write(f"  Упоминает меня: {is_mention}")
                self.stdout.write(f"  Персональное уведомление: {is_personal}")

                if is_personal:
                    personal_count += 1

            self.stdout.write(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
            self.stdout.write(f"Всего сообщений после визита: {messages_after_visit.count()}")
            self.stdout.write(f"Персональных уведомлений (посчитано): {personal_count}")
            self.stdout.write(f"Персональных уведомлений (кешировано): {position.personal_notifications_count}")
            self.stdout.write(f"Персональных уведомлений (актуально): {position.get_personal_notifications_count()}")

            # Проверяем логику mentions_user для конкретных примеров
            self.stdout.write(f"\n🔍 ПРОВЕРКА ЛОГИКИ УПОМИНАНИЙ:")
            self.stdout.write(f"Ищем паттерны для пользователя {user.username}:")
            self.stdout.write(f"  @{user.username}")
            self.stdout.write(f"  @{user.display_name}")
            if user.name:
                self.stdout.write(f"  @{user.name}")

            # Показываем примеры сообщений с @owner
            owner_mentions = Message.objects.filter(
                room=room,
                content__icontains='@owner',
                is_deleted=False
            ).order_by('-created_at')[:5]

            self.stdout.write(f"\n📝 ПРИМЕРЫ СООБЩЕНИЙ С @owner:")
            for msg in owner_mentions:
                mentions_me = msg.mentions_user(user)
                self.stdout.write(f"  '{msg.content}' - упоминает меня: {mentions_me}")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Пользователь {username} не найден'))
        except Room.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Комната {room_name} не найдена'))
        except UserChatPosition.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Позиция пользователя {username} в комнате {room_name} не найдена'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
