from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

class ShippingMethod(models.Model):
    name = models.CharField(_("Название"), max_length=100)
    description = models.TextField(_("Описание"), blank=True)
    price = models.DecimalField(
        _("Стоимость"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    estimated_days = models.CharField(
        _("Примерное время доставки"),
        max_length=50,
        help_text=_("Например: 1-3 дня")
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Способ доставки")
        verbose_name_plural = _("Способы доставки")
        ordering = ['order']

    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    name = models.CharField(_("Название"), max_length=100)
    description = models.TextField(_("Описание"), blank=True)
    instructions = models.TextField(
        _("Инструкции по оплате"),
        blank=True,
        help_text=_("Инструкции, которые будут показаны клиенту при выборе этого способа оплаты")
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Способ оплаты")
        verbose_name_plural = _("Способы оплаты")
        ordering = ['order']

    def __str__(self):
        return self.name

class StoreSettings(models.Model):
    site_name = models.CharField(_("Название сайта"), max_length=255)
    store_email = models.EmailField(_("Email магазина"))
    store_phone = models.CharField(_("Телефон магазина"), max_length=50)
    store_address = models.TextField(_("Адрес магазина"), blank=True)
    min_order_amount = models.DecimalField(
        _("Минимальная сумма заказа"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    free_shipping_amount = models.DecimalField(
        _("Сумма для бесплатной доставки"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    maintenance_mode = models.BooleanField(
        _("Режим обслуживания"),
        default=False,
        help_text=_("Если включено, сайт будет недоступен для посетителей")
    )
    maintenance_message = models.TextField(
        _("Сообщение о техническом обслуживании"),
        blank=True
    )

    class Meta:
        verbose_name = _("Настройки магазина")
        verbose_name_plural = _("Настройки магазина")

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Убеждаемся, что существует только одна запись настроек
        if not self.pk and StoreSettings.objects.exists():
            return
        super().save(*args, **kwargs)

class SBPSettings(models.Model):
    """Настройки СБП для владельца магазина"""

    # Основные реквизиты
    bank_name = models.CharField(
        _("Название банка"),
        max_length=200,
        help_text=_("Например: Сбербанк, ВТБ, Тинькофф")
    )
    account_holder = models.CharField(
        _("Получатель платежа"),
        max_length=200,
        help_text=_("ФИО или название организации")
    )
    phone_number = models.CharField(
        _("Номер телефона для СБП"),
        max_length=20,
        help_text=_("Номер телефона, привязанный к СБП")
    )

    # Дополнительные реквизиты
    bank_account = models.CharField(
        _("Номер счета"),
        max_length=50,
        blank=True,
        help_text=_("Номер банковского счета (опционально)")
    )
    bik = models.CharField(
        _("БИК банка"),
        max_length=9,
        blank=True,
        help_text=_("БИК банка (опционально)")
    )
    inn = models.CharField(
        _("ИНН"),
        max_length=12,
        blank=True,
        help_text=_("ИНН получателя (опционально)")
    )

    # Инструкции для клиентов
    payment_instructions = models.TextField(
        _("Инструкции по оплате"),
        default="""Для оплаты заказа через СБП:
1. Наш менеджер свяжется с вами и предоставит реквизиты для оплаты
2. Откройте приложение вашего банка
3. Найдите функцию 'Переводы' или 'СБП'
4. Введите номер телефона получателя или отсканируйте QR-код
5. Укажите сумму заказа и подтвердите платеж
6. Сообщите менеджеру о совершенном платеже""",
        help_text=_("Инструкции, которые будут показаны клиенту при выборе СБП")
    )

    # Настройки отображения
    is_active = models.BooleanField(
        _("Активны"),
        default=True,
        help_text=_("Показывать ли эти настройки клиентам")
    )

    # Служебные поля
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Настройки СБП")
        verbose_name_plural = _("Настройки СБП")

    def __str__(self):
        return f"Настройки СБП - {self.bank_name}"

    @classmethod
    def get_active_settings(cls):
        """Получить активные настройки СБП"""
        return cls.objects.filter(is_active=True).first()
