from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from .managers import OrderManager
from .marketing import Coupon
from decimal import Decimal

class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Пользователь"),
        related_name='shipping_addresses'
    )
    full_name = models.CharField(_("Полное имя получателя"), max_length=255)
    phone_number = models.CharField(_("Номер телефона"), max_length=30)
    address_line_1 = models.CharField(_("Адрес (улица, дом, квартира)"), max_length=255)
    address_line_2 = models.CharField(_("Адрес (дополнительно)"), max_length=255, blank=True, null=True)
    city = models.CharField(_("Город"), max_length=100)
    state_province_region = models.CharField(_("Область/Край/Республика"), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_("Почтовый индекс"), max_length=20)
    country = models.CharField(_("Страна"), max_length=100) # Можно заменить на django_countries.fields.CountryField, если установлено
    is_default = models.BooleanField(_("Основной адрес"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Адрес доставки")
        verbose_name_plural = _("Адреса доставки")
        ordering = ['-is_default', '-updated_at']

    def __str__(self):
        return f"{self.full_name}, {self.address_line_1}, {self.city}"

class OrderStatus(models.Model):
    name = models.CharField(_("Название"), max_length=100)
    description = models.TextField(_("Описание"), blank=True)
    color = models.CharField(_("Цвет"), max_length=7, help_text=_("HEX код цвета"), default="#000000")
    is_final = models.BooleanField(_("Финальный статус"), default=False)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Статус заказа")
        verbose_name_plural = _("Статусы заказов")
        ordering = ['order']

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Пользователь"),
        related_name='orders'
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        verbose_name=_("Статус"),
        related_name='orders'
    )
    shipping_method = models.ForeignKey(
        'magicbeans_store.ShippingMethod',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Способ доставки"),
        related_name='orders'
    )
    payment_method = models.ForeignKey(
        'magicbeans_store.PaymentMethod',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Способ оплаты"),
        related_name='orders'
    )
    shipping_address = models.ForeignKey(
        ShippingAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Адрес доставки (для зарегистрированных)"),
        related_name='orders'
    )
    shipping_cost = models.DecimalField(
        _("Стоимость доставки"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    subtotal_amount = models.DecimalField(
        _("Сумма товаров (до скидки)"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
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
    total_amount = models.DecimalField(
        _("Общая сумма (с учетом скидки и доставки)"),
        max_digits=10,
        decimal_places=2
    )
    comment = models.TextField(_("Комментарий к заказу"), blank=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    # Поля для адреса и контактов гостя (если user is None)
    guest_email = models.EmailField(_("Email гостя"), blank=True, null=True)
    guest_full_name = models.CharField(_("Полное имя гостя"), max_length=255, blank=True, null=True)
    guest_phone_number = models.CharField(_("Телефон гостя"), max_length=30, blank=True, null=True)
    guest_address_line_1 = models.CharField(_("Адрес гостя (улица, дом)"), max_length=255, blank=True, null=True)
    guest_address_line_2 = models.CharField(_("Адрес гостя (дополнительно)"), max_length=255, blank=True, null=True)
    guest_city = models.CharField(_("Город гостя"), max_length=100, blank=True, null=True)
    guest_state_province_region = models.CharField(_("Область/Край гостя"), max_length=100, blank=True, null=True)
    guest_postal_code = models.CharField(_("Почтовый индекс гостя"), max_length=20, blank=True, null=True)
    guest_country = models.CharField(_("Страна гостя"), max_length=100, blank=True, null=True)

    # Менеджеры с изоляцией данных
    objects = OrderManager()

    class Meta:
        verbose_name = _("Заказ")
        verbose_name_plural = _("Заказы")
        ordering = ['-created_at']
        permissions = [
            ('view_critical_data', 'Can view critical store data'),
            ('export_customer_data', 'Can export customer data'),
        ]

    def __str__(self):
        if self.user:
            return f"Заказ #{self.id} от {self.user.username} ({self.status})"
        else:
            guest_name = self.guest_full_name or self.guest_email or _('Гость')
            return f"Заказ #{self.id} от {guest_name} ({self.status})"

    def calculate_totals(self, save=False):
        """Пересчитывает subtotal_amount и total_amount заказа."""
        self.subtotal_amount = sum(item.price * item.quantity for item in self.items.all())
        self.total_amount = self.subtotal_amount - self.discount_amount + self.shipping_cost
        if self.total_amount < Decimal('0.00'):
            self.total_amount = Decimal('0.00')

        if save:
            self.save(update_fields=['subtotal_amount', 'total_amount', 'shipping_cost'])

    @property
    def can_be_cancelled(self):
        """Можно ли отменить заказ"""
        return not self.status.is_final

    def get_total_items(self):
        """Общее количество товаров в заказе"""
        return sum(item.quantity for item in self.items.all())

    def cancel_order(self, cancelled_by_user=None, reason=""):
        """
        Отменяет заказ и возвращает товары на склад

        Args:
            cancelled_by_user: Пользователь, который отменил заказ (для логирования)
            reason: Причина отмены

        Returns:
            bool: True если отмена прошла успешно, False если заказ нельзя отменить
        """
        from django.db import transaction
        import logging

        logger = logging.getLogger(__name__)

        # Проверяем, можно ли отменить заказ
        if not self.can_be_cancelled:
            logger.warning(f"Попытка отменить заказ #{self.id}, который нельзя отменить (статус: {self.status})")
            return False

        try:
            with transaction.atomic():
                # Получаем статус "Отменен"
                cancelled_status = OrderStatus.objects.filter(name__icontains='отмен').first()
                if not cancelled_status:
                    # Создаем статус "Отменен" если его нет
                    cancelled_status = OrderStatus.objects.create(
                        name="Отменен",
                        description="Заказ отменен",
                        color="#dc3545",  # Красный цвет
                        is_final=True,
                        order=999
                    )

                # Возвращаем товары на склад
                for order_item in self.items.all():
                    stock_item = order_item.stock_item
                    stock_item.quantity += order_item.quantity
                    stock_item.save(update_fields=['quantity'])

                    logger.info(
                        f"Возвращено на склад: {order_item.quantity} шт. товара '{stock_item}' "
                        f"(заказ #{self.id}). Новый остаток: {stock_item.quantity}"
                    )

                # Обновляем статус заказа
                old_status = self.status
                self.status = cancelled_status

                # Добавляем информацию об отмене в комментарий
                cancel_info = f"\n--- ЗАКАЗ ОТМЕНЕН ---\n"
                cancel_info += f"Дата отмены: {timezone.now().strftime('%d.%m.%Y %H:%M')}\n"
                if cancelled_by_user:
                    cancel_info += f"Отменил: {cancelled_by_user}\n"
                if reason:
                    cancel_info += f"Причина: {reason}\n"
                cancel_info += f"Предыдущий статус: {old_status}\n"
                cancel_info += "Товары возвращены на склад.\n"

                self.comment = (self.comment + cancel_info) if self.comment else cancel_info
                self.save(update_fields=['status', 'comment'])

                logger.info(
                    f"Заказ #{self.id} успешно отменен. "
                    f"Статус изменен с '{old_status}' на '{cancelled_status}'. "
                    f"Отменил: {cancelled_by_user or 'Система'}"
                )

                return True

        except Exception as e:
            logger.error(f"Ошибка при отмене заказа #{self.id}: {str(e)}")
            return False

    def get_absolute_url(self):
        return reverse('store:order_detail', args=[self.id])

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name=_("Заказ"),
        related_name='items'
    )
    stock_item = models.ForeignKey(
        'magicbeans_store.StockItem',
        on_delete=models.PROTECT,
        verbose_name=_("Товар"),
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(_("Количество"))
    price = models.DecimalField(
        _("Цена за единицу"),
        max_digits=10,
        decimal_places=2
    )
    total = models.DecimalField(
        _("Общая стоимость"),
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        verbose_name = _("Позиция заказа")
        verbose_name_plural = _("Позиции заказа")

    def __str__(self):
        return f"{self.stock_item} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)

    def get_total_price(self):
        """Возвращает общую стоимость позиции"""
        return self.price * self.quantity
