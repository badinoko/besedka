from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model

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

    def get_editor_display_name(self):
        """Возвращает отображаемое имя редактора"""
        if not self.edited_by:
            return None
        return self.edited_by.display_name
