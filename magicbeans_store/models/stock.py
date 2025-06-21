from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

class StockItem(models.Model):
    strain = models.ForeignKey(
        'magicbeans_store.Strain',
        on_delete=models.CASCADE,
        verbose_name=_("Сорт"),
        related_name='stock_items'
    )
    seeds_count = models.PositiveIntegerField(
        _("Количество семян"),
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        _("Цена"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveIntegerField(
        _("Количество на складе"),
        default=0
    )
    sku = models.CharField(
        _("Артикул"),
        max_length=50,
        unique=True,
        default='',
        blank=True,
        help_text=_("Генерируется автоматически при сохранении")
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    class Meta:
        verbose_name = _("Товар на складе")
        verbose_name_plural = _("Товары на складе")
        ordering = ['strain', 'seeds_count']
        unique_together = ['strain', 'seeds_count']

    def __str__(self):
        return f"{self.strain.name} - {self.seeds_count} семян"

    def save(self, *args, **kwargs):
        if not self.sku:
            # Генерируем SKU на основе сидбанка, сорта и количества семян
            self.sku = f"{self.strain.seedbank.id:03d}-{self.strain.id:03d}-{self.seeds_count:02d}"
        super().save(*args, **kwargs)
