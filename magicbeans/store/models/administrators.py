from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Administrator(models.Model):
    """Модель администратора магазина."""
    name = models.CharField(_("Имя"), max_length=255)
    telegram_id = models.CharField(_("Telegram ID"), max_length=100, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administrator',
        verbose_name=_("Пользователь Django")
    )
    is_active = models.BooleanField(_("Активный"), default=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    class Meta:
        verbose_name = _("Администратор")
        verbose_name_plural = _("Администраторы")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.telegram_id})"
