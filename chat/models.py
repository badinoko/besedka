from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import re

User = get_user_model()


class Room(models.Model):
    """
    Модель для представления общей комнаты чата.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Название комнаты"), max_length=100, unique=True, default='general')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(_("Дата создания"), default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Комната чата")
        verbose_name_plural = _("Комнаты чата")
        ordering = ["created_at"]

    def __str__(self):
        return self.name


class Message(models.Model):
    """
    Модель для сообщений в чате.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Комната")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Автор")
    )
    content = models.TextField(_("Содержимое"))
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_("Ответ на")
    )
    created_at = models.DateTimeField(_("Дата создания"), default=timezone.now, db_index=True)

    # Новые поля для расширенного функционала
    is_deleted = models.BooleanField(default=False, help_text="Сообщение помечено как удаленное")
    is_edited = models.BooleanField(default=False, help_text="Сообщение было отредактировано")
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='edited_messages', help_text="Кто отредактировал сообщение")
    edited_at = models.DateTimeField(null=True, blank=True, help_text="Когда было отредактировано")

    is_forwarded = models.BooleanField(default=False, help_text="Сообщение является пересланным")
    original_message_id = models.CharField(max_length=50, null=True, blank=True,
                                         help_text="ID оригинального сообщения при пересылке")

    is_pinned = models.BooleanField(default=False, help_text="Сообщение закреплено")
    pinned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='pinned_messages', help_text="Кто закрепил сообщение")
    pinned_at = models.DateTimeField(null=True, blank=True, help_text="Когда было закреплено")

    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")
        ordering = ["created_at"]

    def __str__(self):
        return f"Сообщение от {self.author} в {self.room}"

    @property
    def is_reply(self):
        """Является ли сообщение ответом на другое сообщение"""
        return self.parent is not None

    @property
    def likes_count(self):
        """Количество лайков на сообщении"""
        return self.reactions.filter(reaction_type='like').count()

    @property
    def dislikes_count(self):
        """Количество дизлайков на сообщении"""
        return self.reactions.filter(reaction_type='dislike').count()

    def get_user_reaction(self, user):
        """Получить реакцию конкретного пользователя на сообщение"""
        try:
            reaction = self.reactions.get(user=user)
            return reaction.reaction_type
        except MessageReaction.DoesNotExist:
            return None

    def has_user_reacted(self, user):
        """Проверить, реагировал ли пользователь на сообщение"""
        return self.reactions.filter(user=user).exists()

    def get_editor_display_name(self):
        """Возвращает отображаемое имя редактора"""
        if not self.edited_by:
            return None
        return self.edited_by.display_name

    def mentions_user(self, user):
        """Проверяет, упоминается ли пользователь в сообщении"""
        if not self.content:
            return False

        # Паттерны для поиска упоминаний
        patterns = [
            f'@{user.username}',
            f'@{user.display_name}',
            f'@{user.name}' if user.name else None,
        ]

        # Убираем None значения
        patterns = [p for p in patterns if p]

        for pattern in patterns:
            if pattern.lower() in self.content.lower():
                return True
        return False

    def is_personal_notification_for(self, user):
        """Проверяет, является ли сообщение персональным уведомлением для пользователя"""
        # Ответ на сообщение пользователя
        if self.parent and self.parent.author == user:
            return True

        # Упоминание пользователя в сообщении
        if self.mentions_user(user):
            return True

        return False


class MessageReaction(models.Model):
    """
    Модель для хранения реакций пользователей на сообщения в чате.
    """
    REACTION_CHOICES = [
        ('like', _('Лайк')),
        ('dislike', _('Дизлайк')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_("Сообщение")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_reactions',
        verbose_name=_("Пользователь")
    )
    reaction_type = models.CharField(
        _("Тип реакции"),
        max_length=10,
        choices=REACTION_CHOICES
    )
    created_at = models.DateTimeField(_("Дата создания"), default=timezone.now)

    class Meta:
        verbose_name = _("Реакция на сообщение")
        verbose_name_plural = _("Реакции на сообщения")
        unique_together = ('message', 'user')  # Один пользователь - одна реакция на сообщение
        indexes = [
            models.Index(fields=['message', 'reaction_type']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.display_name} - {self.get_reaction_type_display()} на сообщение {self.message.id}"

    def save(self, *args, **kwargs):
        """Переопределяем save для логирования важных действий кармы"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Логируем новую реакцию для будущей системы кармы
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"NEW REACTION: {self.user.username} {self.reaction_type}d message by {self.message.author.username}")


class UserChatPosition(models.Model):
    """
    Модель для отслеживания позиции пользователя в чате и непрочитанных сообщений.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_positions',
        verbose_name=_("Пользователь")
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='user_positions',
        verbose_name=_("Комната")
    )
    last_read_at = models.DateTimeField(
        _("Последнее время прочтения"),
        null=True,
        blank=True,
        help_text="Время последнего прочтения сообщений в этом чате. None для новых пользователей."
    )
    last_message_id = models.UUIDField(
        _("ID последнего прочитанного сообщения"),
        null=True,
        blank=True,
        help_text="UUID последнего сообщения, которое пользователь точно прочитал"
    )
    unread_count = models.PositiveIntegerField(
        _("Количество непрочитанных"),
        default=0,
        help_text="Кешированное количество непрочитанных сообщений для быстрого доступа"
    )

    # Новые поля для системы персональных уведомлений
    personal_notifications_count = models.PositiveIntegerField(
        _("Количество персональных уведомлений"),
        default=0,
        help_text="Кешированное количество персональных уведомлений (ответы + упоминания)"
    )
    last_visit_at = models.DateTimeField(
        _("Последний визит"),
        null=True,
        blank=True,
        help_text="Время последнего визита в чат для определения правильной позиции"
    )

    updated_at = models.DateTimeField(
        _("Обновлено"),
        auto_now=True,
        help_text="Время последнего обновления позиции"
    )

    class Meta:
        verbose_name = _("Позиция пользователя в чате")
        verbose_name_plural = _("Позиции пользователей в чатах")
        unique_together = ('user', 'room')  # Одна позиция на пользователя в комнате
        indexes = [
            models.Index(fields=['user', 'room']),
            models.Index(fields=['last_read_at']),
            models.Index(fields=['unread_count']),
            models.Index(fields=['personal_notifications_count']),
            models.Index(fields=['last_visit_at']),
        ]

    def __str__(self):
        return f"{self.user.display_name} в {self.room.name} (непрочитанных: {self.unread_count}, персональных: {self.personal_notifications_count})"

    def get_unread_messages_count(self):
        """Вычисляет актуальное количество непрочитанных сообщений"""
        if not self.last_read_at:
            # 🔧 ИСПРАВЛЕНО: Для новых пользователей НЕТ непрочитанных сообщений
            # Непрочитанные появляются только ПОСЛЕ первого посещения чата
            return 0

        return self.room.messages.filter(
            created_at__gt=self.last_read_at,
            is_deleted=False
        ).count()

    def get_personal_notifications_count(self):
        """Вычисляет актуальное количество персональных уведомлений"""
        if not self.last_visit_at:
            # Для новых пользователей НЕТ персональных уведомлений
            return 0

        # Персональные уведомления - это сообщения после последнего визита, которые:
        # 1. Являются ответами на сообщения этого пользователя
        # 2. Или упоминают этого пользователя
        personal_messages = self.room.messages.filter(
            created_at__gt=self.last_visit_at,
            is_deleted=False
        ).exclude(
            author=self.user  # Исключаем собственные сообщения
        )

        count = 0
        for message in personal_messages:
            if message.is_personal_notification_for(self.user):
                count += 1

        return count

    def get_messages_below_current_position(self):
        """Возвращает количество сообщений ниже текущей позиции скролла"""
        if not self.last_read_at:
            return 0

        return self.room.messages.filter(
            created_at__gt=self.last_read_at,
            is_deleted=False
        ).count()

    def mark_as_read(self, up_to_message=None, up_to_time=None):
        """
        Отмечает сообщения как прочитанные до указанного сообщения или времени
        """
        old_last_read_at = self.last_read_at

        if up_to_message:
            self.last_message_id = up_to_message.id
            self.last_read_at = up_to_message.created_at
        elif up_to_time:
            self.last_read_at = up_to_time
        else:
            self.last_read_at = timezone.now()

        # Обновляем кешированные счетчики
        self.unread_count = self.get_unread_messages_count()
        self.personal_notifications_count = self.get_personal_notifications_count()
        self.save()

        # Логируем изменение для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Position updated for {self.user.username} in {self.room.name}: "
                   f"last_read_at {old_last_read_at} -> {self.last_read_at}, "
                   f"unread_count: {self.unread_count}, personal_notifications: {self.personal_notifications_count}")

    def mark_visit(self):
        """Отмечает визит пользователя в чат"""
        self.last_visit_at = timezone.now()
        self.save()

    def get_first_unread_message(self):
        """Возвращает первое непрочитанное сообщение или None"""
        if not self.last_read_at:
            # 🔧 ИСПРАВЛЕНО: Для новых пользователей НЕТ непрочитанных сообщений
            # Непрочитанные появляются только ПОСЛЕ первого посещения чата
            return None

        return self.room.messages.filter(
            created_at__gt=self.last_read_at,
            is_deleted=False
        ).order_by('created_at').first()

    def get_first_personal_notification(self):
        """Возвращает первое персональное уведомление или None"""
        if not self.last_visit_at:
            return None

        # Находим первое сообщение с персональным уведомлением
        personal_messages = self.room.messages.filter(
            created_at__gt=self.last_visit_at,
            is_deleted=False
        ).exclude(
            author=self.user
        ).order_by('created_at')

        for message in personal_messages:
            if message.is_personal_notification_for(self.user):
                return message

        return None

    def get_return_position(self):
        """Определяет позицию для возвращения в чат"""
        # Если есть персональные уведомления, возвращаемся к первому
        first_personal = self.get_first_personal_notification()
        if first_personal:
            return {
                'type': 'personal',
                'message_id': str(first_personal.id)
            }

        # Если есть непрочитанные сообщения, возвращаемся к первому непрочитанному
        first_unread = self.get_first_unread_message()
        if first_unread:
            return {
                'type': 'unread',
                'message_id': str(first_unread.id)
            }

        # Если нет ни персональных, ни непрочитанных, возвращаемся к концу
        return {
            'type': 'end',
            'message_id': None
        }

    @classmethod
    def get_or_create_for_user(cls, user, room):
        """Получает или создает позицию пользователя в комнате"""
        position, created = cls.objects.get_or_create(
            user=user,
            room=room,
            defaults={
                'last_read_at': None,
                'last_visit_at': None,
                'unread_count': 0,
                'personal_notifications_count': 0
            }
        )
        return position
