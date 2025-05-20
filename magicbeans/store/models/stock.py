from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .products import Strain


class StockItem(models.Model):
    """Модель фасовки (упаковки) сорта с указанием количества семян и цены."""
    strain = models.ForeignKey(
        Strain,
        on_delete=models.CASCADE,
        related_name="stock_items",
        verbose_name=_("Сорт"),
    )
    seeds_count = models.CharField(
        _("Количество семян"), max_length=20,
        help_text=_("Например: 1, 3, 5, 10, 5+2, и т.д."),
    )
    price = models.DecimalField(
        _("Цена"), max_digits=10, decimal_places=2,
    )
    quantity = models.PositiveIntegerField(
        _("Количество на складе"), default=0,
    )
    is_visible = models.BooleanField(_("Отображается"), default=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    class Meta:
        verbose_name = _("Фасовка")
        verbose_name_plural = _("Фасовки")
        ordering = ["seeds_count"]
        constraints = [
            models.UniqueConstraint(
                fields=["strain", "seeds_count"],
                name="unique_strain_seeds_count",
            ),
        ]

    def __str__(self):
        return f"{self.strain.name} - {self.seeds_count}"


class StockMovement(models.Model):
    """Журнал движения товара на складе."""
    MOVEMENT_IN = "in"
    MOVEMENT_OUT = "out"

    MOVEMENT_CHOICES = [
        (MOVEMENT_IN, _("Поступление")),
        (MOVEMENT_OUT, _("Списание")),
    ]

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name="movements",
        verbose_name=_("Товар"),
    )
    quantity = models.PositiveIntegerField(_("Количество"))
    movement_type = models.CharField(
        _("Тип движения"),
        max_length=10,
        choices=MOVEMENT_CHOICES,
    )
    comment = models.TextField(_("Комментарий"), blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Пользователь"),
        related_name="stock_movements",
    )
    timestamp = models.DateTimeField(_("Время"), auto_now_add=True)

    class Meta:
        verbose_name = _("Движение товара")
        verbose_name_plural = _("Движения товара")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.stock_item} x{self.quantity}"

    def save(self, *args, **kwargs):
        # Обновляем количество товара на складе
        if self.movement_type == self.MOVEMENT_IN:
            self.stock_item.quantity += self.quantity
        else:  # MOVEMENT_OUT
            self.stock_item.quantity = max(0, self.stock_item.quantity - self.quantity)
        self.stock_item.save()
        super().save(*args, **kwargs)
