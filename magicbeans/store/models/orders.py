from django.db import models
from django.utils.translation import gettext_lazy as _

from .administrators import Administrator
from .stock import StockItem


class Order(models.Model):
    """Заказ пользователя."""
    STATUS_NEW = "new"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_NEW, _("Новый")),
        (STATUS_PROCESSING, _("В обработке")),
        (STATUS_SHIPPED, _("Отправлен")),
        (STATUS_DELIVERED, _("Доставлен")),
        (STATUS_CANCELLED, _("Отменен")),
    ]

    user_telegram_id = models.CharField(_("ID пользователя Telegram"), max_length=100)
    admin = models.ForeignKey(
        Administrator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Администратор"),
    )
    status = models.CharField(
        _("Статус"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    total = models.DecimalField(
        _("Общая сумма"), max_digits=10, decimal_places=2,
        default=0,
    )
    comment = models.TextField(_("Комментарий"), blank=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    class Meta:
        verbose_name = _("Заказ")
        verbose_name_plural = _("Заказы")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{_('Заказ')} #{self.id} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"


class OrderItem(models.Model):
    """Позиция в заказе."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Заказ"),
    )
    strain_name = models.CharField(_("Название сорта"), max_length=255)
    seeds_count = models.CharField(_("Фасовка"), max_length=20)
    quantity = models.PositiveIntegerField(_("Количество"))
    price = models.DecimalField(
        _("Цена за единицу"), max_digits=10, decimal_places=2,
    )
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name=_("Товар"),
    )

    class Meta:
        verbose_name = _("Позиция заказа")
        verbose_name_plural = _("Позиции заказов")

    def __str__(self):
        return f"{self.strain_name} ({self.seeds_count}) x{self.quantity}"
