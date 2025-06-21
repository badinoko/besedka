from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Promotion(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', _("Процент")),
        ('fixed', _("Фиксированная сумма")),
    ]

    name = models.CharField(_("Название"), max_length=255)
    description = models.TextField(_("Описание"), blank=True)
    discount_type = models.CharField(
        _("Тип скидки"),
        max_length=20,
        choices=DISCOUNT_TYPES,
        default='percentage'
    )
    discount_value = models.DecimalField(
        _("Значение скидки"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    start_date = models.DateTimeField(_("Дата начала"))
    end_date = models.DateTimeField(_("Дата окончания"))
    is_active = models.BooleanField(_("Активна"), default=True)
    created_at = models.DateTimeField(_("Создана"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлена"), auto_now=True)

    class Meta:
        verbose_name = _("Акция")
        verbose_name_plural = _("Акции")
        ordering = ['-start_date']

    def __str__(self):
        return self.name

class Coupon(models.Model):
    code = models.CharField(_("Код купона"), max_length=50, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    discount_percentage = models.DecimalField(
        _("Процент скидки"),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    max_uses = models.PositiveIntegerField(
        _("Максимальное количество использований"),
        default=1
    )
    uses_count = models.PositiveIntegerField(
        _("Количество использований"),
        default=0
    )
    start_date = models.DateTimeField(_("Дата начала"))
    end_date = models.DateTimeField(_("Дата окончания"))
    min_order_amount = models.DecimalField(
        _("Минимальная сумма заказа"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    class Meta:
        verbose_name = _("Купон")
        verbose_name_plural = _("Купоны")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.discount_percentage}%)"

    def is_valid(self, cart=None, check_uses=True):
        """Проверяет, действителен ли купон в данный момент и для данной корзины (опционально)."""
        from django.utils import timezone # Local import to avoid circularity if models are split
        now = timezone.now()
        if not self.is_active:
            return False, _("Купон неактивен.")
        if self.start_date > now:
            return False, _("Срок действия купона еще не начался.")
        if self.end_date < now:
            return False, _("Срок действия купона истек.")
        if check_uses and self.uses_count >= self.max_uses:
            return False, _("Купон уже был использован максимальное количество раз.")
        if cart:
            # Рассчитываем предварительную сумму корзины без скидок
            # Это нужно, чтобы min_order_amount проверялся на сумму до скидки по этому купону
            subtotal = sum(item.stock_item.price * item.quantity for item in cart.items.all())
            if subtotal < self.min_order_amount:
                return False, _("Минимальная сумма заказа для этого купона: %(amount)s.") % {'amount': self.min_order_amount}
        return True, _("Купон действителен.")

    def calculate_discount(self, amount_to_discount):
        """Рассчитывает скидку для заданной суммы."""
        if self.discount_percentage > 0:
            discount = (self.discount_percentage / Decimal('100')) * amount_to_discount
            return discount.quantize(Decimal('0.01'))
        return Decimal('0.00')

    def redeem(self):
        """Погашает купон, увеличивая счетчик использований."""
        if self.uses_count < self.max_uses:
            self.uses_count += 1
            self.save(update_fields=['uses_count'])
            return True
        return False
