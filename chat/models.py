import datetime
import re
import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, Count
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import NoReverseMatch

User = get_user_model()


class RoomManager(models.Manager):
    """Менеджер для управления комнатами чата"""

    def total_unread_messages(self, user):
        """Общее количество непрочитанных сообщений для пользователя"""
        unread_count = 0
        rooms = self.model.objects.filter(
            models.Q(room_thread__user1=user) |
            models.Q(room_thread__user2=user) |
            models.Q(discussion_room__members=user)
        ).distinct()
        for room in rooms:
            unread_count += room.unread_count(user)
        return unread_count


class Room(models.Model):
    """Базовая модель комнаты чата"""

    # Приватный чат (1-на-1)
    is_private = models.BooleanField(
        default=False,
        verbose_name=_('Приватный чат'),
        help_text=_('Чат между двумя пользователями')
    )

    # Групповое обсуждение
    is_discussion = models.BooleanField(
        default=False,
        verbose_name=_('Групповое обсуждение'),
        help_text=_('Открытое обсуждение для сообщества')
    )

    # Отключение уведомлений
    muted = models.BooleanField(
        default=False,
        verbose_name=_('Отключить уведомления'),
        help_text=_('Пользователи не будут получать уведомления')
    )

    # История очищена
    history_cleared = models.BooleanField(
        default=False,
        verbose_name=_('История очищена'),
        help_text=_('Отображать сообщение об очистке истории')
    )

    # Подключенные пользователи (онлайн)
    connected_clients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        verbose_name=_('Подключенные пользователи'),
        help_text=_('Пользователи онлайн в данный момент')
    )

    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Изменено'))

    objects = RoomManager()

    class Meta:
        ordering = ('-modified', 'id')
        verbose_name = _('Комната чата')
        verbose_name_plural = _('Комнаты чата')

    def __str__(self):
        if self.is_private and hasattr(self, 'room_thread'):
            return f"Приватный чат: {self.room_thread}"
        elif self.is_discussion and hasattr(self, 'discussion_room'):
            return f"Обсуждение: {self.discussion_room.headline}"
        return f"Комната #{self.id}"

    @property
    def get_absolute_url(self):
        if self.is_private and hasattr(self, 'room_thread') and self.room_thread and self.room_thread.id:
            # Для приватных чатов (Thread) может понадобиться другой URL, возможно, с ID пользователя-партнера,
            # но пока будем использовать ID комнаты/треда, если есть такой маршрут.
            # Пытаемся использовать URL для Thread, если он существует (reverse by name)
            try:
                # Предположим, что у Thread есть get_absolute_url или мы можем его сформировать
                # Если у Thread нет get_absolute_url, но есть у Room, то используем его.
                # Маршрут 'chat:room' ожидает 'id' комнаты
                return reverse('chat:room', kwargs={'room_id': self.id})
            except NoReverseMatch:
                pass # Если такого маршрута нет, или он для другого
        elif self.is_discussion and hasattr(self, 'discussion_room') and self.discussion_room:
            return self.discussion_room.get_absolute_url
        elif hasattr(self, 'global_chat_room') and self.global_chat_room:
            return self.global_chat_room.get_absolute_url
        elif hasattr(self, 'vip_chat_room') and self.vip_chat_room:
            return self.vip_chat_room.get_absolute_url
        # Базовый URL для комнаты, если есть такой маршрут, иначе None
        try:
            return reverse('chat:room', kwargs={'room_id': self.id}) # Используем room_id как в RoomView
        except NoReverseMatch:
            return None # Если нет общего URL для комнаты

    def connect(self, user):
        """Добавить пользователя в список подключенных"""
        if user not in self.connected_clients.all():
            self.connected_clients.add(user)

    def disconnect(self, user):
        """Удалить пользователя из списка подключенных"""
        if user in self.connected_clients.all():
            self.connected_clients.remove(user)

    def has_messages(self):
        """Проверить, есть ли сообщения в комнате"""
        return self.room_messages.exists()

    def unread_messages(self, user):
        """Непрочитанные сообщения для пользователя"""
        return self.room_messages.filter(Q(unread=True) & ~Q(author=user))

    def unread_count(self, user):
        """Количество непрочитанных сообщений"""
        return self.unread_messages(user).count()

    def get_messages(self):
        """Все сообщения комнаты"""
        return self.room_messages.all()

    def latest_message(self):
        """Последнее сообщение в комнате"""
        if self.has_messages():
            return self.room_messages.latest('created')
        return None

    def latest_messages_count(self, days_limit=30):
        """Количество сообщений за последние дни (для трендов)"""
        time_limit = datetime.datetime.now() - datetime.timedelta(days=days_limit)
        return self.room_messages.filter(created__gte=time_limit).count()

    def snip_room_members(self, limit=3):
        """Первые участники комнаты для отображения"""
        messages = (
            self.room_messages.all()
            .order_by('author')
            .distinct('author')[:limit]
        )
        return [m.author for m in messages]

    def members(self):
        """Все участники комнаты"""
        return self.room_messages.all().order_by('author_id').distinct('author')

    def clear_chat_history(self):
        """Очистить историю чата"""
        msgs = self.room_messages.all()
        msgs_count = msgs.count()
        msgs.delete()
        self.history_cleared = True
        self.save()
        return msgs_count


class Message(models.Model):
    """Модель сообщения в чате"""

    # Ответ на сообщение
    reply_to = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Ответ на сообщение'),
        help_text=_('Сообщение, на которое отвечает данное')
    )

    # Автор сообщения
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Автор'),
        help_text=_('Пользователь, написавший сообщение')
    )

    # Комната
    room = models.ForeignKey(
        Room,
        related_name='room_messages',
        on_delete=models.CASCADE,
        verbose_name=_('Комната'),
        help_text=_('Комната, в которой написано сообщение')
    )

    # Содержимое сообщения
    content = models.TextField(
        verbose_name=_('Содержимое'),
        help_text=_('Текст сообщения')
    )

    # Непрочитанное сообщение
    unread = models.BooleanField(
        default=True,
        verbose_name=_('Непрочитанное'),
        help_text=_('Сообщение еще не прочитано')
    )

    # Отредактировано
    is_edited = models.BooleanField(
        default=False,
        verbose_name=_('Отредактировано'),
        help_text=_('Сообщение было отредактировано')
    )

    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Изменено'))

    class Meta:
        ordering = ('-created',)
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')

    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}..."

    def likes_count(self):
        """Количество лайков для сообщения"""
        return self.reactions.filter(reaction_type='like').count()

    def dislikes_count(self):
        """Количество дизлайков для сообщения"""
        return self.reactions.filter(reaction_type='dislike').count()


class ThreadManager(models.Manager):
    """Менеджер для приватных чатов"""

    def new_or_get(self, current_user, partner):
        """Создать новый или получить существующий приватный чат"""
        qs = self.get_queryset().filter(
            Q(user1=current_user, user2=partner) |
            Q(user1=partner, user2=current_user)
        )
        if qs.count() == 1:
            created = False
            chat_obj = qs.first()
        else:
            room = Room.objects.create(is_private=True)
            chat_obj = Thread.objects.create(
                room=room,
                user1=current_user,
                user2=partner
            )
            created = True
        return chat_obj, created

    def total_unread_messages(self, user):
        """Общее количество непрочитанных сообщений в приватных чатах"""
        unread_count = 0
        threads = self.model.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).distinct()
        for thread in threads:
            unread_count += thread.room.unread_count(user)
        return unread_count

    def search(self, query=None):
        """Поиск по приватным чатам"""
        qs = self.get_queryset()
        if query is not None:
            or_lookup = (
                Q(user1__first_name__icontains=query) |
                Q(user1__last_name__icontains=query) |
                Q(user1__username__icontains=query) |
                Q(user2__first_name__icontains=query) |
                Q(user2__last_name__icontains=query) |
                Q(user2__username__icontains=query)
            )
            qs = qs.filter(or_lookup).distinct()
        return qs


class Thread(models.Model):
    """Приватный чат между двумя пользователями"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Комната для этого приватного чата
    room = models.OneToOneField(
        Room,
        related_name='room_thread',
        on_delete=models.CASCADE,
        verbose_name=_('Комната')
    )

    # Первый пользователь
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='chat_thread_first',
        on_delete=models.SET_NULL,
        verbose_name=_('Первый пользователь')
    )

    # Второй пользователь
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='chat_thread_second',
        on_delete=models.SET_NULL,
        verbose_name=_('Второй пользователь')
    )

    objects = ThreadManager()

    class Meta:
        unique_together = ['user1', 'user2']
        ordering = ('-room__modified',)
        verbose_name = _('Приватный чат')
        verbose_name_plural = _('Приватные чаты')

    def __str__(self):
        return f"{self.user1.username} ↔ {self.user2.username}"

    def get_all_messages(self):
        """Все сообщения приватного чата"""
        return self.room.get_messages()

    def get_partner(self, user):
        """Получить собеседника для данного пользователя"""
        if self.user1 == user:
            return self.user2
        return self.user1


class Tag(models.Model):
    """Теги для категоризации обсуждений"""

    name = models.CharField(
        max_length=124,
        unique=True,
        verbose_name=_('Название'),
        help_text=_('Название тега для категоризации')
    )

    slug = models.SlugField(
        max_length=124,
        unique=True,
        verbose_name=_('Слаг'),
        help_text=_('URL-дружественное название')
    )

    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))

    class Meta:
        ordering = ('name',)
        verbose_name = _('Тег')
        verbose_name_plural = _('Теги')

    def __str__(self):
        return self.name


class DiscussionRoomManager(models.Manager):
    """Менеджер для групповых обсуждений"""

    def search(self, query=None):
        """Поиск по обсуждениям"""
        qs = self.get_queryset()
        if query is not None:
            or_lookup = (
                Q(headline__icontains=query) |
                Q(description__icontains=query) |
                Q(messages_dump__icontains=query) |
                Q(tags__name__icontains=query)
            )
            qs = qs.filter(or_lookup).distinct()
        return qs

    def get_trendings(self, qs=None, excludes=None):
        """Получить трендовые обсуждения"""
        if qs is None:
            qs = self.get_queryset()

        if excludes:
            qs = qs.exclude(id__in=excludes)

        # Сортировка по количеству сообщений за последние 30 дней
        trending_rooms = []
        for room in qs:
            messages_count = room.room.latest_messages_count()
            trending_rooms.append((room, messages_count))

        # Сортировка по убыванию количества сообщений
        trending_rooms.sort(key=lambda x: x[1], reverse=True)
        return [room[0] for room in trending_rooms]


class DiscussionRoom(models.Model):
    """Групповое обсуждение"""

    # Владелец обсуждения
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Владелец'),
        help_text=_('Пользователь, создавший обсуждение')
    )

    # Комната для этого обсуждения
    room = models.OneToOneField(
        Room,
        related_name='discussion_room',
        on_delete=models.CASCADE,
        verbose_name=_('Комната')
    )

    # Заголовок обсуждения
    headline = models.CharField(
        max_length=220,
        unique=True,
        verbose_name=_('Заголовок'),
        help_text=_('Основная тема обсуждения')
    )

    # Описание
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Описание'),
        help_text=_('Подробное описание темы обсуждения')
    )

    # Участники
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='discussion_members',
        blank=True,
        verbose_name=_('Участники'),
        help_text=_('Пользователи, участвующие в обсуждении')
    )

    # Теги
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        verbose_name=_('Теги'),
        help_text=_('Теги для категоризации обсуждения')
    )

    # URL-дружественный слаг
    slug = models.SlugField(
        max_length=250,
        unique=True,
        verbose_name=_('Слаг'),
        help_text=_('URL-дружественное название')
    )

    # Дамп сообщений для поиска
    messages_dump = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Дамп сообщений'),
        help_text=_('Содержимое всех сообщений для поиска')
    )

    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Изменено'))

    objects = DiscussionRoomManager()

    class Meta:
        ordering = ('-modified',)
        verbose_name = _('Групповое обсуждение')
        verbose_name_plural = _('Групповые обсуждения')

    def __str__(self):
        return self.headline

    @property
    def get_absolute_url(self):
        return reverse('chat:discussion', kwargs={'slug': self.slug})

    def set_messages_dump(self):
        """Обновить дамп сообщений для поиска"""
        messages = self.room.room_messages.all()
        content_list = [msg.content for msg in messages]
        self.messages_dump = ' '.join(content_list)
        self.save()


class GlobalChatRoom(models.Model):
    """Общий чат для всех пользователей платформы"""

    name = models.CharField(
        max_length=100,
        default="Общий чат",
        verbose_name=_('Название'),
        help_text=_('Название общего чата')
    )

    description = models.TextField(
        blank=True,
        default="Общий чат для всех пользователей платформы Беседка",
        verbose_name=_('Описание'),
        help_text=_('Описание общего чата')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        help_text=_('Включен ли общий чат')
    )

    # Связь с базовой Room
    room = models.OneToOneField(
        Room,
        related_name='global_chat_room',
        on_delete=models.CASCADE,
        verbose_name=_('Комната')
    )

    # Автоматически добавлять новых пользователей
    auto_add_users = models.BooleanField(
        default=True,
        verbose_name=_('Автодобавление пользователей'),
        help_text=_('Автоматически добавлять новых пользователей в общий чат')
    )

    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Изменено'))

    class Meta:
        verbose_name = _('Общий чат')
        verbose_name_plural = _('Общие чаты')

    def __str__(self):
        return self.name

    @property
    def get_absolute_url(self):
        return reverse('chat:general')

    def get_recent_messages(self, limit=10):
        """Получить последние сообщения"""
        return self.room.room_messages.all()[:limit]

    def get_online_users(self):
        """Получить пользователей онлайн"""
        return self.room.connected_clients.all()

    @classmethod
    def get_or_create_default(cls):
        """Получить или создать общий чат по умолчанию"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            # Создаем новую комнату
            room = Room.objects.create(
                is_private=False,
                is_discussion=False
            )
            return cls.objects.create(
                name="Общий чат",
                description="Общий чат для всех пользователей платформы Беседка",
                room=room,
                is_active=True
            )


class VIPChatRoom(models.Model):
    """VIP-чат только по приглашениям"""

    name = models.CharField(
        max_length=100,
        default="VIP Беседка",
        verbose_name=_('Название'),
        help_text=_('Название VIP-чата')
    )

    description = models.TextField(
        blank=True,
        default="Приватный VIP-чат для избранных участников",
        verbose_name=_('Описание'),
        help_text=_('Описание VIP-чата')
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Создатель'),
        help_text=_('Пользователь, создавший VIP-чат')
    )

    # Связь с базовой Room
    room = models.OneToOneField(
        Room,
        related_name='vip_chat_room',
        on_delete=models.CASCADE,
        verbose_name=_('Комната')
    )

    # Участники (только по приглашениям)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='VIPChatMembership',
        through_fields=('vip_chat', 'user'),
        related_name='vip_chats',
        verbose_name=_('Участники'),
        help_text=_('Участники VIP-чата')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        help_text=_('Включен ли VIP-чат')
    )

    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))
    modified = models.DateTimeField(auto_now=True, verbose_name=_('Изменено'))

    class Meta:
        verbose_name = _('VIP-чат')
        verbose_name_plural = _('VIP-чаты')

    def __str__(self):
        return self.name

    @property
    def get_absolute_url(self):
        return reverse('chat:vip')

    def can_access(self, user):
        """Проверить, может ли пользователь получить доступ к VIP-чату"""
        if not user.is_authenticated:
            return False

        # Owner всегда имеет доступ
        if hasattr(user, 'role') and user.role == 'owner':
            return True

        # Проверяем членство
        return self.vipchatmembership_set.filter(
            user=user,
            is_active=True
        ).exists()

    def add_member(self, user, invited_by):
        """Добавить участника в VIP-чат"""
        membership, created = VIPChatMembership.objects.get_or_create(
            vip_chat=self,
            user=user,
            defaults={'invited_by': invited_by}
        )
        return membership, created

    def remove_member(self, user):
        """Удалить участника из VIP-чата"""
        VIPChatMembership.objects.filter(
            vip_chat=self,
            user=user
        ).update(is_active=False)

    @classmethod
    def get_or_create_default(cls, created_by):
        """Получить или создать VIP-чат по умолчанию"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            # Создаем новую комнату
            room = Room.objects.create(
                is_private=False,
                is_discussion=False
            )
            return cls.objects.create(
                name="VIP Беседка",
                description="Приватный VIP-чат для избранных участников",
                room=room,
                created_by=created_by,
                is_active=True
            )


class VIPChatMembership(models.Model):
    """Членство в VIP-чате"""

    vip_chat = models.ForeignKey(
        VIPChatRoom,
        on_delete=models.CASCADE,
        verbose_name=_('VIP-чат')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь')
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='vip_invitations_sent',
        on_delete=models.CASCADE,
        verbose_name=_('Пригласил'),
        help_text=_('Пользователь, который отправил приглашение')
    )

    invited_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата приглашения')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активное членство'),
        help_text=_('Активно ли членство в VIP-чате')
    )

    # Дата принятия приглашения
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата принятия')
    )

    class Meta:
        unique_together = ['vip_chat', 'user']
        verbose_name = _('Членство в VIP-чате')
        verbose_name_plural = _('Членства в VIP-чатах')

    def __str__(self):
        return f"{self.user.username} в {self.vip_chat.name}"

    def accept_invitation(self):
        """Принять приглашение"""
        self.accepted_at = timezone.now()
        self.is_active = True
        self.save()


class ChatReaction(models.Model):
    """Неотзывные реакции (Like / Dislike) на сообщения чата."""

    REACTION_CHOICES = [
        ('like', '👍 Like'),
        ('dislike', '👎 Dislike'),
    ]

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_('Сообщение')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь')
    )
    reaction_type = models.CharField(
        max_length=7,
        choices=REACTION_CHOICES,
        verbose_name=_('Тип реакции')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Создано'))

    class Meta:
        verbose_name = _('Реакция сообщения')
        verbose_name_plural = _('Реакции сообщений')
        unique_together = ('message', 'user')  # Однократная, безотзывная реакция
        indexes = [
            models.Index(fields=['message', 'reaction_type']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.get_reaction_type_display()} msg#{self.message_id}"
