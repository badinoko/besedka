from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import VIPChatRoom, VIPChatMembership, Room

User = get_user_model()


class Command(BaseCommand):
    help = 'Настройка VIP-чата и добавление участников'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-default',
            action='store_true',
            help='Создать VIP-чат по умолчанию',
        )
        parser.add_argument(
            '--add-user',
            type=str,
            help='Добавить пользователя в VIP-чат (username)',
        )
        parser.add_argument(
            '--remove-user',
            type=str,
            help='Удалить пользователя из VIP-чата (username)',
        )
        parser.add_argument(
            '--list-members',
            action='store_true',
            help='Показать всех участников VIP-чата',
        )

    def handle(self, *args, **options):
        if options['create_default']:
            self.create_default_vip_chat()

        if options['add_user']:
            self.add_user_to_vip_chat(options['add_user'])

        if options['remove_user']:
            self.remove_user_from_vip_chat(options['remove_user'])

        if options['list_members']:
            self.list_vip_members()

    def create_default_vip_chat(self):
        """Создать VIP-чат по умолчанию"""
        try:
            owner = User.objects.filter(role='owner').first()
            if not owner:
                self.stdout.write(
                    self.style.ERROR('Владелец платформы не найден.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при поиске владельца: {e}')
            )
            return

        # Проверяем, существует ли уже VIP-чат
        if VIPChatRoom.objects.filter(is_active=True).exists():
            self.stdout.write(
                self.style.WARNING('VIP-чат уже существует.')
            )
            return

        # Создаем комнату
        room = Room.objects.create(
            is_private=False,
            is_discussion=False
        )

        # Создаем VIP-чат
        vip_chat = VIPChatRoom.objects.create(
            name="Резерв",
            description="Приватный чат для избранных участников сообщества Беседка",
            room=room,
            created_by=owner,
            is_active=True
        )

        # Автоматически добавляем владельца платформы
        VIPChatMembership.objects.create(
            vip_chat=vip_chat,
            user=owner,
            invited_by=owner,
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'VIP-чат "{vip_chat.name}" успешно создан!')
        )

    def add_user_to_vip_chat(self, username):
        """Добавить пользователя в VIP-чат"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь "{username}" не найден.')
            )
            return

        try:
            vip_chat = VIPChatRoom.objects.get(is_active=True)
        except VIPChatRoom.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('VIP-чат не найден. Создайте его сначала с --create-default.')
            )
            return

        try:
            owner = User.objects.filter(role='owner').first()
            if not owner:
                self.stdout.write(
                    self.style.ERROR('Владелец платформы не найден.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при поиске владельца: {e}')
            )
            return

        # Проверяем, не является ли пользователь уже участником
        if VIPChatMembership.objects.filter(vip_chat=vip_chat, user=user, is_active=True).exists():
            self.stdout.write(
                self.style.WARNING(f'Пользователь "{username}" уже является участником VIP-чата.')
            )
            return

        # Добавляем пользователя
        membership, created = VIPChatMembership.objects.get_or_create(
            vip_chat=vip_chat,
            user=user,
            defaults={
                'invited_by': owner,
                'is_active': True
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Пользователь "{username}" добавлен в VIP-чат!')
            )
        else:
            # Активируем существующее членство
            membership.is_active = True
            membership.save()
            self.stdout.write(
                self.style.SUCCESS(f'Членство пользователя "{username}" в VIP-чате активировано!')
            )

    def remove_user_from_vip_chat(self, username):
        """Удалить пользователя из VIP-чата"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь "{username}" не найден.')
            )
            return

        try:
            vip_chat = VIPChatRoom.objects.get(is_active=True)
        except VIPChatRoom.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('VIP-чат не найден.')
            )
            return

        # Проверяем, что это не владелец платформы
        if user.role == 'owner':
            self.stdout.write(
                self.style.ERROR('Нельзя удалить владельца платформы из VIP-чата.')
            )
            return

        try:
            membership = VIPChatMembership.objects.get(vip_chat=vip_chat, user=user, is_active=True)
            membership.is_active = False
            membership.save()
            self.stdout.write(
                self.style.SUCCESS(f'Пользователь "{username}" удален из VIP-чата!')
            )
        except VIPChatMembership.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'Пользователь "{username}" не является участником VIP-чата.')
            )

    def list_vip_members(self):
        """Показать всех участников VIP-чата"""
        try:
            vip_chat = VIPChatRoom.objects.get(is_active=True)
        except VIPChatRoom.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('VIP-чат не найден.')
            )
            return

        members = VIPChatMembership.objects.filter(vip_chat=vip_chat, is_active=True).select_related('user', 'invited_by')

        if not members.exists():
            self.stdout.write(
                self.style.WARNING('В VIP-чате нет участников.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Участники VIP-чата "{vip_chat.name}":')
        )
        self.stdout.write('-' * 50)

        for membership in members:
            user = membership.user
            invited_by = membership.invited_by
            role_display = user.get_role_display() if hasattr(user, 'get_role_display') else user.role

            self.stdout.write(
                f'• {user.username} ({role_display}) - приглашен {invited_by.username}'
            )

        self.stdout.write('-' * 50)
        self.stdout.write(f'Всего участников: {members.count()}')
