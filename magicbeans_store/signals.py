from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order, OrderItem
from django.contrib.auth.signals import user_logged_in
from .models import Cart, CartItem
from .utils import get_cart

import logging
logger = logging.getLogger(__name__)

@receiver(pre_save, sender=OrderItem)
def calculate_order_item_total(sender, instance, **kwargs):
    """
    Автоматически рассчитывает общую стоимость позиции заказа
    """
    instance.total = instance.price * instance.quantity

@receiver(post_save, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """
    Обновляет общую сумму заказа при изменении позиций
    """
    order = instance.order
    total = sum(item.total for item in order.items.all())
    if order.shipping_cost:
        total += order.shipping_cost
    Order.objects.filter(id=order.id).update(total_amount=total)

@receiver(user_logged_in)
def merge_guest_cart_to_user_cart(sender, request, user, **kwargs):
    """
    При входе пользователя переносит товары из гостевой сессионной корзины
    в его постоянную корзину.
    """
    guest_session_key = request.session.get('_cart_session_key_before_login') # Ключ, который мы можем сохранить перед логином

    # Пытаемся получить гостевую корзину по обычному session_key, если она еще не обработана
    # Это для случая, если _cart_session_key_before_login не был установлен
    current_session_key = request.session.session_key

    guest_cart = None
    try:
        if guest_session_key:
            guest_cart = Cart.objects.filter(session_key=guest_session_key, user__isnull=True).first()
            logger.info(f"Attempting to merge cart for session_key (before login): {guest_session_key}")

        if not guest_cart and current_session_key: # Если по старому ключу не нашли, пробуем по текущему
            guest_cart = Cart.objects.filter(session_key=current_session_key, user__isnull=True).first()
            logger.info(f"Attempting to merge cart for current session_key: {current_session_key}")

        if guest_cart and guest_cart.items.exists():
            user_cart, created = Cart.objects.get_or_create(user=user)
            logger.info(f"User {user.username} logged in. Guest cart ID: {guest_cart.id if guest_cart else 'None'}. User cart ID: {user_cart.id}, Created: {created}")

            if user_cart == guest_cart: # Это не должно произойти, если user__isnull=True работало правильно
                logger.warning(f"User cart and guest cart are the same (ID: {user_cart.id}). No merge needed, but investigate why.")
                guest_cart.user = user # Присваиваем пользователя, если это была его корзина без user
                guest_cart.session_key = None # Очищаем session_key
                guest_cart.save()
                return

            for guest_item in guest_cart.items.all():
                user_item, item_created = CartItem.objects.get_or_create(
                    cart=user_cart,
                    stock_item=guest_item.stock_item,
                    defaults={'quantity': guest_item.quantity}
                )
                if not item_created:
                    # Товар уже есть в корзине пользователя, обновляем количество
                    # Можно выбрать: суммировать, заменить или оставить как есть.
                    # Для простоты, пока будем суммировать, но не превышая остаток на складе.
                    # Эта логика может потребовать блокировки stock_item для избежания гонок.
                    # Пока оставляем простое суммирование, т.к. это редкий кейс при правильной очистке гостевой корзины.
                    user_item.quantity += guest_item.quantity
                    # TODO: Add stock check here if summing quantities to avoid exceeding stock.
                    user_item.save()
                logger.info(f"Merged item {guest_item.stock_item} (qty: {guest_item.quantity}) to user {user.username}'s cart. New user item qty: {user_item.quantity}")

            logger.info(f"Deleting guest cart ID: {guest_cart.id} after merging.")
            guest_cart.delete() # Удаляем гостевую корзину после переноса

            # Очищаем сохраненный ключ сессии
            if guest_session_key and '_cart_session_key_before_login' in request.session:
                del request.session['_cart_session_key_before_login']

        elif guest_cart: # Гостевая корзина есть, но пуста
            logger.info(f"Guest cart ID: {guest_cart.id} found but is empty. Deleting.")
            guest_cart.delete()

    except Cart.DoesNotExist:
        logger.info(f"No guest cart found to merge for user {user.username}.")
    except Exception as e:
        logger.error(f"Error merging guest cart for user {user.username}: {e}", exc_info=True)

# Нужно будет где-то перед логином сохранять session_key, если мы хотим надежно его получить
# Например, в view, который обрабатывает POST запроса на логин, или в middleware.
# Или, если `get_cart` всегда присваивает session_key гостевой корзине, то можно найти ее по
# request.session.session_key до того, как сессия ротируется при логине.

# В allauth сигнал user_logged_in передает request. Поэтому мы можем попытаться найти
# гостевую корзину по request.session.session_key *до* того, как allauth мог изменить сессию.
# Однако, get_cart уже привязывает корзину к сессии, так что этого должно быть достаточно.
