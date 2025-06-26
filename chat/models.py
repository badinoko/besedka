from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils import timezone


class Room(models.Model):
    """
    Модель для представления общей комнаты чата.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Название комнаты"), max_length=100, unique=True, default='general')
    created_at = models.DateTimeField(_("Дата создания"), default=timezone.now)

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
        settings.AUTH_USER_MODEL,
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

    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")
        ordering = ["created_at"]

    def __str__(self):
        return f"Сообщение от {self.author} в {self.room}"
