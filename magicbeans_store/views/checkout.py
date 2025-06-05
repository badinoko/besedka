from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.generic import FormView, TemplateView, DetailView
from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from django.db import models
from users.models import User as CustomUser, Notification
from django.http import Http404
from django.utils.html import format_html

from ..models import Cart, Order, OrderItem, OrderStatus, ShippingMethod, PaymentMethod, ShippingAddress
from ..forms import CheckoutForm
from ..utils import get_cart
from core.models import ActionLog

# === ЗАГЛУШКА ДЛЯ TELEGRAM УВЕДОМЛЕНИЙ ===
def send_telegram_notification(telegram_username: str, message: str):
    """
    Функция-заглушка для отправки уведомлений в Telegram.
    Здесь должен быть код для взаимодействия с вашим внешним Telegram-ботом.
    Например, отправка HTTP-запроса на API вашего бота.
    """
    print(f"[TELEGRAM STUB] Уведомление для @{telegram_username}: {message}")
    # В реальной реализации:
    # try:
    #     # response = requests.post('URL_ВАШЕГО_БОТА/send_message', data={'username': telegram_username, 'message': message})
    #     # response.raise_for_status() # Проверка на ошибки HTTP
    #     # print(f"Telegram уведомление успешно отправлено для @{telegram_username}")
    # except Exception as e:
    #     # logger.error(f"Ошибка отправки Telegram уведомления для @{telegram_username}: {e}")
    #     print(f"[TELEGRAM STUB ERROR] Ошибка отправки для @{telegram_username}: {e}")
    pass

class SecureCheckoutView(FormView):
    """Оформление заказа. Доступно гостям, но требует входа для завершения."""
    template_name = 'store/checkout.html'
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        cart, cart_created = get_cart(request)

        # Критическая проверка: убеждаемся, что корзина сохранена и имеет pk
        if not cart or not cart.pk:
            messages.error(request, gettext_lazy('Произошла ошибка с вашей корзиной. Попробуйте снова.'))
            return redirect('store:cart_detail')

        # Дополнительная проверка: перезагружаем корзину из БД для гарантии актуальности
        try:
            self.cart = Cart.objects.select_related('applied_coupon').prefetch_related('items__stock_item__strain').get(pk=cart.pk)
        except Cart.DoesNotExist:
            messages.error(request, gettext_lazy('Не удалось найти вашу корзину.'))
            return redirect('store:cart_detail')

        # Проверяем, что в корзине есть товары
        if not self.cart.items.exists():
            messages.error(request, gettext_lazy('Ваша корзина пуста. Пожалуйста, добавьте товары перед оформлением заказа.'))
            return redirect('store:cart_detail')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # КРИТИЧЕСКИ ВАЖНО: Убеждаемся, что корзина в контексте имеет pk и загружена из БД
        if hasattr(self, 'cart') and self.cart and self.cart.pk:
            # Используем уже загруженную корзину из dispatch с prefetch_related
            context['cart'] = self.cart
        else:
            # Аварийная загрузка корзины, если что-то пошло не так
            cart, _ = get_cart(self.request)
            if cart and cart.pk:
                context['cart'] = Cart.objects.select_related('applied_coupon').prefetch_related('items__stock_item__strain').get(pk=cart.pk)
            else:
                # Если корзина все еще без pk, создаем пустую для избежания ошибок в шаблоне
                context['cart'] = None

        context['page_title'] = gettext_lazy('Оформление заказа')
        context['shipping_methods'] = ShippingMethod.objects.filter(is_active=True)
        context['payment_methods'] = PaymentMethod.objects.filter(is_active=True)
        if not self.request.user.is_authenticated:
            context['guest_checkout_info'] = gettext_lazy(
                'Вы оформляете заказ как гость. Чтобы сохранять историю заказов, получать бонусы и пользоваться всеми возможностями "Беседки", <a href="%s" class="alert-link">зарегистрируйтесь</a> или <a href="%s" class="alert-link">войдите</a> после оформления.'
            ) % (reverse('account_signup'), reverse('account_login') + f"?next={reverse('store:checkout')}")
        return context

    def form_valid(self, form):
        # Дополнительная проверка и перезагрузка self.cart
        if hasattr(self, 'cart') and self.cart and self.cart.pk:
            try:
                self.cart = Cart.objects.get(pk=self.cart.pk)
            except Cart.DoesNotExist:
                messages.error(self.request, gettext_lazy('Корзина не найдена перед созданием заказа.'))
                return self.form_invalid(form)
        elif not hasattr(self, 'cart') or not self.cart or not self.cart.pk:
            messages.error(self.request, gettext_lazy('Критическая ошибка: корзина отсутствует или недействительна в form_valid.'))
            # Редирект на страницу корзины, так как что-то серьезно не так
            return redirect('store:cart_detail')

        user_for_order = None
        if self.request.user.is_authenticated:
            user_for_order = self.request.user

        try:
            with transaction.atomic():
                shipping_address_obj = None
                if user_for_order:
                    shipping_address_data_for_model = {
                        'user': user_for_order,
                        'full_name': form.cleaned_data['full_name'],
                        'phone_number': form.cleaned_data['phone_number'],
                        'address_line_1': form.cleaned_data['address_line_1'],
                        'address_line_2': form.cleaned_data['address_line_2'],
                        'city': form.cleaned_data['city'],
                        'state_province_region': form.cleaned_data['state_province_region'],
                        'postal_code': form.cleaned_data['postal_code'],
                        'country': form.cleaned_data['country'],
                    }
                    shipping_address_obj, created = ShippingAddress.objects.update_or_create(
                        user=user_for_order,
                        defaults=shipping_address_data_for_model
                    )

                try:
                    initial_status = OrderStatus.objects.get(name__iexact='Новый', order=0)
                except OrderStatus.DoesNotExist:
                    initial_status = OrderStatus.objects.order_by('order').first()
                    if not initial_status:
                        raise Exception("Не найдены статусы заказа для установки начального статуса.")

                # Получаем выбранный способ доставки
                selected_shipping_method = form.cleaned_data['shipping_method']

                order_data = {
                    'user': user_for_order,
                    'status': initial_status,
                    'shipping_method': selected_shipping_method,
                    'payment_method': form.cleaned_data['payment_method'],
                    'subtotal_amount': self.cart.subtotal_amount,
                    'applied_coupon': self.cart.applied_coupon,
                    'discount_amount': self.cart.discount_amount,
                    'shipping_cost': selected_shipping_method.price if selected_shipping_method else Decimal('0.00'),
                    'total_amount': Decimal('0.00'),
                    'comment': form.cleaned_data.get('comment', '')
                }

                if user_for_order:
                    order_data['shipping_address'] = shipping_address_obj
                else:
                    order_data['guest_email'] = form.cleaned_data['email']
                    order_data['guest_full_name'] = form.cleaned_data['full_name']
                    order_data['guest_phone_number'] = form.cleaned_data['phone_number']
                    order_data['guest_address_line_1'] = form.cleaned_data['address_line_1']
                    order_data['guest_address_line_2'] = form.cleaned_data['address_line_2']
                    order_data['guest_city'] = form.cleaned_data['city']
                    order_data['guest_state_province_region'] = form.cleaned_data['state_province_region']
                    order_data['guest_postal_code'] = form.cleaned_data['postal_code']
                    order_data['guest_country'] = form.cleaned_data['country']

                order = Order.objects.create(**order_data)

                for cart_item in self.cart.items.all():
                    stock_item_to_order = cart_item.stock_item
                    if stock_item_to_order.quantity < cart_item.quantity:
                        messages.error(self.request, gettext_lazy('К сожалению, количество товара "%(item_name)s" изменилось. Доступно: %(available)s. Пожалуйста, обновите корзину.') % {'item_name': stock_item_to_order.strain.name, 'available': stock_item_to_order.quantity})
                        raise ValueError(f"Insufficient stock for {stock_item_to_order.id} during checkout.")
                    OrderItem.objects.create(order=order, stock_item=stock_item_to_order, quantity=cart_item.quantity, price=stock_item_to_order.price)
                    stock_item_to_order.quantity -= cart_item.quantity
                    stock_item_to_order.save(update_fields=['quantity'])

                order.calculate_totals(save=True)
                if order.applied_coupon: pass

                self.cart.items.all().delete()
                self.cart.applied_coupon = None
                self.cart.discount_amount = Decimal('0.00')
                if self.cart.user is None and self.cart.session_key: self.cart.delete()
                else: self.cart.save()

                log_user_for_action = user_for_order
                store_staff = CustomUser.objects.filter(models.Q(role=CustomUser.Role.STORE_ADMIN) | models.Q(role=CustomUser.Role.STORE_OWNER))
                order_content_type = ContentType.objects.get_for_model(Order)
                client_identifier = f"пользователя {order.user.username}" if order.user else f"гостя (Email: {order.guest_email or 'не указан'})"
                notification_title = f"Новый заказ #{order.pk} от {client_identifier[:30]}..."
                notification_message = f"Поступил новый заказ на сумму {order.total_amount} руб. от {client_identifier}."
                for staff_member in store_staff:
                    if order.user:
                        Notification.objects.create(recipient=staff_member, sender=order.user, notification_type=Notification.NotificationType.ORDER,title=notification_title, message=notification_message, content_type=order_content_type, object_id=order.pk)
                    if staff_member.telegram_username:
                        tg_client_name = order.user.username if order.user else (order.guest_full_name or order.guest_email or "Гость")
                        tg_message = f"🛍️ Новый заказ!\nНомер: #{order.pk}\nСумма: {order.total_amount} руб.\nКлиент: {tg_client_name}\nКомментарий: {order.comment[:50] + '...' if order.comment and len(order.comment) > 50 else order.comment or '-'}"
                        send_telegram_notification(staff_member.telegram_username, tg_message)
                ActionLog.objects.create(user=log_user_for_action, action_type='order_created', model_name=Order.__name__, object_id=order.pk, object_repr=str(order), details=f'Заказ #{order.id} на сумму {order.total_amount} создан.')
                if not user_for_order:
                    self.request.session['guest_order_id'] = order.pk
                    if order.guest_email:
                        self.request.session['guest_checkout_email'] = order.guest_email
                messages.success(self.request, gettext_lazy('Ваш заказ успешно оформлен! Менеджер свяжется с вами в ближайшее время.'))
                return redirect(reverse('store:order_success_page', kwargs={'order_pk': order.pk}))

        except Exception as e:
            messages.error(self.request, gettext_lazy('Произошла ошибка при оформлении заказа ({error}). Пожалуйста, попробуйте еще раз или свяжитесь с поддержкой.').format(error=str(e)))
            return self.form_invalid(form)

class OrderSuccessView(DetailView):
    model = Order
    template_name = 'store/order_success.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_pk'

    def get_object(self, queryset=None):
        """Получаем заказ, проверяя права доступа для пользователя или гостя."""
        order_pk = self.kwargs.get('order_pk')  # Используем прямое имя параметра
        order = get_object_or_404(Order, pk=order_pk)

        if order.user: # Заказ принадлежит зарегистрированному пользователю
            if order.user == self.request.user:
                return order
            else:
                # Залогиненный пользователь пытается посмотреть чужой заказ
                messages.error(self.request, gettext_lazy("У вас нет доступа к этому заказу."))
                raise Http404("Order does not belong to the current user.")
        else: # Гостевой заказ, order.user is None
            guest_order_id_in_session = self.request.session.get('guest_order_id')
            if guest_order_id_in_session == order.pk:
                 # Удаляем из сессии после успешного просмотра, чтобы нельзя было повторно открыть по той же сессии
                # self.request.session.pop('guest_order_id', None)
                # self.request.session.pop('guest_checkout_email', None)
                # Пока оставим в сессии, чтобы пользователь мог обновить страницу
                return order
            else:
                messages.error(self.request, gettext_lazy("Не удалось подтвердить ваш гостевой заказ. Возможно, ваша сессия истекла."))
                raise Http404("Guest order ID mismatch or not found in session.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = gettext_lazy("Заказ успешно оформлен")

        # Добавляем настройки СБП для отображения реквизитов
        from ..models import SBPSettings
        context['sbp_settings'] = SBPSettings.get_active_settings()

        order = self.object # Получаем объект заказа (уже проверенный get_object)
        if not order.user: # Если это гостевой заказ
            guest_email = self.request.session.get('guest_checkout_email')
            if guest_email:
                signup_url = reverse('account_signup')
                login_url = reverse('account_login')
                # Пробуем передать email в форму регистрации
                # Для allauth это можно сделать через initial data в сессии или GET-параметр,
                # но это сложнее. Проще просто предложить.
                context['guest_registration_prompt'] = format_html(
                    gettext_lazy("Ваш заказ как гостя оформлен. Чтобы отслеживать его и получить доступ ко всем возможностям, <a href='{}' class='alert-link'>зарегистрируйтесь</a> с email <strong>{}</strong> или <a href='{}' class='alert-link'>войдите</a>, если у вас уже есть аккаунт."),
                    signup_url,
                    guest_email,
                    login_url
                )
            else:
                 context['guest_registration_prompt'] = format_html(
                    gettext_lazy("Ваш заказ как гостя оформлен. Чтобы отслеживать его и получить доступ ко всем возможностям, <a href='{}' class='alert-link'>зарегистрируйтесь</a> или <a href='{}' class='alert-link'>войдите</a>, если у вас уже есть аккаунт."),
                    reverse('account_signup'),
                    reverse('account_login')
                )
        return context

# Удален дублирующий CartView - используется из cart.py
