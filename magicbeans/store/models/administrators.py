from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Administrator(models.Model):
    """Модель для администраторов магазина."""
    name = models.CharField(_("Имя"), max_length=255)
    telegram_id = models.CharField(_("Telegram ID"), max_length=100, unique=True)
    is_active = models.BooleanField(_("Активный"), default=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    can_manage_products = models.BooleanField(default=True)
    can_manage_orders = models.BooleanField(default=True)
    can_manage_promotions = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Администратор")
        verbose_name_plural = _("Администраторы")
        ordering = ["-created_at"]
        app_label = 'magicbeans_store'

    def __str__(self):
        return f"{self.name} ({self.telegram_id})"
