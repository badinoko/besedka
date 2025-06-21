from django.db import models
from django.utils.translation import gettext_lazy as _

class SalesReport(models.Model):
    REPORT_TYPES = [
        ('daily', _("Ежедневный")),
        ('weekly', _("Еженедельный")),
        ('monthly', _("Ежемесячный")),
        ('yearly', _("Годовой")),
        ('custom', _("Пользовательский")),
    ]

    report_type = models.CharField(
        _("Тип отчета"),
        max_length=20,
        choices=REPORT_TYPES,
        default='daily'
    )
    start_date = models.DateTimeField(_("Дата начала"))
    end_date = models.DateTimeField(_("Дата окончания"))
    total_orders = models.PositiveIntegerField(_("Всего заказов"), default=0)
    total_sales = models.DecimalField(
        _("Общая сумма продаж"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    average_order_value = models.DecimalField(
        _("Средний чек"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    report_data = models.JSONField(
        _("Данные отчета"),
        default=dict,
        help_text=_("Детальные данные отчета в формате JSON")
    )
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    class Meta:
        verbose_name = _("Отчет по продажам")
        verbose_name_plural = _("Отчеты по продажам")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.get_report_type_display()} отчет ({self.start_date.date()} - {self.end_date.date()})"

class InventoryReport(models.Model):
    REPORT_TYPES = [
        ('current', _("Текущий остаток")),
        ('movement', _("Движение товара")),
        ('low_stock', _("Низкий остаток")),
        ('custom', _("Пользовательский")),
    ]

    report_type = models.CharField(
        _("Тип отчета"),
        max_length=20,
        choices=REPORT_TYPES,
        default='current'
    )
    start_date = models.DateTimeField(_("Дата начала"))
    end_date = models.DateTimeField(_("Дата окончания"))
    total_items = models.PositiveIntegerField(_("Всего товаров"), default=0)
    total_value = models.DecimalField(
        _("Общая стоимость"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    low_stock_threshold = models.PositiveIntegerField(
        _("Порог низкого остатка"),
        default=5
    )
    report_data = models.JSONField(
        _("Данные отчета"),
        default=dict,
        help_text=_("Детальные данные отчета в формате JSON")
    )
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    class Meta:
        verbose_name = _("Отчет по складу")
        verbose_name_plural = _("Отчеты по складу")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()} ({self.created_at.date()})"
