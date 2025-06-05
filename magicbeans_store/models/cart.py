from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal
from .managers import CartManager
from .marketing import Coupon

class Cart(models.Model):
    """Корзина пользователя или гостя."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Пользователь"),
        related_name='carts',
        null=True,
        blank=True
    )
    session_key = models.CharField(
        _("Ключ сессии гостя"),
        max_length=40,
        null=True,
        blank=True,
        db_index=True
    )
    created_at = models.DateTimeField(_("Создана"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлена"), auto_now=True)
    applied_coupon = models.ForeignKey(
        Coupon,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Примененный купон")
    )
    discount_amount = models.DecimalField(
        _("Сумма скидки"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Менеджер
    objects = CartManager()

    class Meta:
        verbose_name = _("Корзина")
        verbose_name_plural = _("Корзины")

    def __str__(self):
        if self.user:
            return f"Корзина пользователя {self.user.username}"
        elif self.session_key:
            return f"Корзина гостя (сессия {self.session_key[:8]}...)"
        return f"Корзина ID {self.pk}"

    @property
    def subtotal_amount(self):
        """Подсчет общей суммы корзины ДО скидок."""
        if not self.pk:
            return Decimal('0.00')
        return sum(item.get_total() for item in self.items.all())

    def get_total_amount(self):
        """Подсчет общей суммы корзины ПОСЛЕ скидок."""
        if not self.pk:
            return Decimal('0.00')
        total = self.subtotal_amount - self.discount_amount
        return max(total, Decimal('0.00')) # Убедимся, что сумма не отрицательная

    def get_total_items(self):
        """Подсчет общего количества товаров"""
        if not self.pk:
            return 0
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Очистка корзины"""
        self.items.all().delete()

class CartItem(models.Model):
    """Элемент корзины"""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        verbose_name=_("Корзина"),
        related_name='items'
    )
    stock_item = models.ForeignKey(
        'magicbeans_store.StockItem',
        on_delete=models.CASCADE,
        verbose_name=_("Товар"),
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(_("Количество"), default=1)
    added_at = models.DateTimeField(_("Добавлен"), auto_now_add=True)

    class Meta:
        verbose_name = _("Элемент корзины")
        verbose_name_plural = _("Элементы корзины")
        unique_together = ['cart', 'stock_item']

    def __str__(self):
        return f"{self.stock_item} x {self.quantity}"

    def get_total(self):
        """Получить общую стоимость позиции"""
        return self.stock_item.price * self.quantity

    def save(self, *args, **kwargs):
        # Убираем валидацию количества на складе из модели
        # Эта логика должна быть в views для правильной обработки ошибок
        super().save(*args, **kwargs)
