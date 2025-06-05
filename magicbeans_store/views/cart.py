from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from django.template.loader import render_to_string
import logging

from ..models import Cart, CartItem, StockItem, Coupon
from ..forms import ApplyCouponForm
from ..utils import get_cart

logger = logging.getLogger(__name__)

class CartView(TemplateView):
    """Просмотр корзины"""
    template_name = 'store/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, _ = get_cart(self.request)
        context['cart'] = cart
        if cart:
            context['cart_items'] = cart.items.select_related('stock_item__strain', 'stock_item__strain__seedbank')
        else:
            context['cart_items'] = []
        context['apply_coupon_form'] = ApplyCouponForm()

        # Хлебные крошки
        context['breadcrumbs'] = [
            {'title': 'Главная', 'url': '/'},
            {'title': 'Магазин', 'url': reverse('store:catalog')},
            {'title': 'Корзина', 'url': None}
        ]

        return context

class AddToCartView(View):
    """Добавление товара в корзину"""

    def post(self, request, *args, **kwargs):
        stock_item_id = request.POST.get('stock_item_id')
        quantity = int(request.POST.get('quantity', 1))

        try:
            with transaction.atomic():
                stock_item = get_object_or_404(StockItem, id=stock_item_id, is_active=True)

                if stock_item.quantity < quantity:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': f'Недостаточно товара на складе. Доступно: {stock_item.quantity}'
                        })
                    messages.error(request, f'Недостаточно товара на складе. Доступно: {stock_item.quantity}')
                    return redirect('store:strain_detail', pk=stock_item.strain.pk)

                cart, _ = get_cart(request)
                if not cart:
                    messages.error(request, 'Не удалось получить доступ к корзине.')
                    return redirect('store:strain_detail', pk=stock_item.strain.pk)

                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart,
                    stock_item=stock_item,
                    defaults={'quantity': quantity}
                )

                if not item_created:
                    new_quantity = cart_item.quantity + quantity
                    if new_quantity > stock_item.quantity:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'message': f'Недостаточно товара. В корзине: {cart_item.quantity}, доступно еще: {stock_item.quantity - cart_item.quantity}'
                            })
                        messages.error(request, f'Недостаточно товара. В корзине: {cart_item.quantity}, доступно еще: {stock_item.quantity - cart_item.quantity}')
                        return redirect('store:strain_detail', pk=stock_item.strain.pk)

                    cart_item.quantity = new_quantity
                    cart_item.save()
                    stock_item_to_update = StockItem.objects.select_for_update().get(id=stock_item.id)
                    stock_item_to_update.quantity -= quantity
                    stock_item_to_update.save(update_fields=['quantity'])

                else:
                    stock_item_to_update = StockItem.objects.select_for_update().get(id=stock_item.id)
                    if stock_item_to_update.quantity < quantity:
                        cart_item.delete()
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'message': f'Не удалось добавить товар из-за изменения наличия. Доступно: {stock_item_to_update.quantity}'
                            })
                        messages.error(request, f'Не удалось добавить товар из-за изменения наличия. Доступно: {stock_item_to_update.quantity}')
                        return redirect('store:strain_detail', pk=stock_item.strain.pk)
                    stock_item_to_update.quantity -= quantity
                    stock_item_to_update.save(update_fields=['quantity'])

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    cart_items_html = render_to_string(
                        'store/partials/cart_items_partial.html',
                        {'cart_items': cart.items.select_related('stock_item__strain', 'stock_item__strain__seedbank')}
                    )
                    cart_summary_html = render_to_string(
                        'store/partials/cart_summary_partial.html',
                        {'cart': cart}
                    )
                    current_stock_quantity = stock_item_to_update.quantity
                    return JsonResponse({
                        'success': True,
                        'message': 'Товар добавлен в корзину',
                        'cart_total_items': cart.get_total_items(),
                        'cart_total_amount': float(cart.get_total_amount()),
                        'cart_items_html': cart_items_html,
                        'cart_summary_html': cart_summary_html,
                        'discount_amount': float(cart.discount_amount),
                        'subtotal_amount': float(cart.subtotal_amount),
                        'applied_coupon_code': cart.applied_coupon.code if cart.applied_coupon else None,
                        'stock_item_id': stock_item.id,
                        'updated_stock_quantity': current_stock_quantity
                    })
                return redirect('store:strain_detail', pk=stock_item.strain.pk)

        except Exception as e:
            logger.error(f"Ошибка при добавлении товара в корзину (user: {request.user.username if request.user.is_authenticated else f'Guest Session: {request.session.session_key}'}, stock_item_id: {request.POST.get('stock_item_id')}, quantity: {request.POST.get('quantity')}): {e}", exc_info=True)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Ошибка при добавлении товара в корзину'
                })
            messages.error(request, 'Ошибка при добавлении товара в корзину')
            stock_item_id_for_fallback = request.POST.get('stock_item_id')
            if stock_item_id_for_fallback:
                try:
                    fallback_stock_item = StockItem.objects.filter(id=stock_item_id_for_fallback).first()
                    if fallback_stock_item:
                        return redirect('store:strain_detail', pk=fallback_stock_item.strain.pk)
                except: # nosec
                    pass
            return redirect(reverse('store:catalog'))

class UpdateCartView(View):
    """Обновление количества товара в корзине"""

    def post(self, request, *args, **kwargs):
        request.session.save() # Убедимся, что сессия сохранена
        cart_item_id = request.POST.get('cart_item_id')
        quantity = int(request.POST.get('quantity', 1))
        cart, _ = get_cart(request)

        if not cart:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Корзина не найдена.'})
            messages.error(request, 'Корзина не найдена.')
            return redirect('store:catalog')

        try:
            with transaction.atomic():
                cart_item = get_object_or_404(
                    CartItem,
                    id=cart_item_id,
                    cart=cart
                )

                # Если количество <= 0, удаляем товар из корзины
                if quantity <= 0:
                    stock_item_to_return = cart_item.stock_item
                    stock_item_to_return.quantity += cart_item.quantity
                    stock_item_to_return.save(update_fields=['quantity'])
                    cart_item.delete()
                    message = 'Товар удален из корзины'

                    # Перезагрузка корзины из БД
                    cart = Cart.objects.get(pk=cart.pk)

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        cart_items_html = render_to_string(
                            'store/partials/cart_items_partial.html',
                            {'cart_items': cart.items.select_related('stock_item__strain', 'stock_item__strain__seedbank')}
                        )
                        cart_summary_html = render_to_string(
                            'store/partials/cart_summary_partial.html',
                            {'cart': cart}
                        )

                        return JsonResponse({
                            'success': True,
                            'message': message,
                            'cart_total_items': cart.get_total_items(),
                            'cart_total_amount': float(cart.get_total_amount()),
                            'item_total_price': 0,
                            'cart_items_html': cart_items_html,
                            'cart_summary_html': cart_summary_html,
                            'discount_amount': float(cart.discount_amount),
                            'subtotal_amount': float(cart.subtotal_amount),
                            'applied_coupon_code': cart.applied_coupon.code if cart.applied_coupon else None,
                            'stock_item_id': stock_item_to_return.id,
                            'updated_stock_quantity': stock_item_to_return.quantity,
                            'item_removed': True
                        })
                else:
                    # Обновляем количество товара
                    original_cart_quantity = cart_item.quantity
                    quantity_diff = quantity - original_cart_quantity
                    stock_item_to_update = StockItem.objects.select_for_update().get(id=cart_item.stock_item.id)

                    # Проверяем, достаточно ли товара на складе для увеличения
                    if quantity_diff > 0:
                        if stock_item_to_update.quantity < quantity_diff:
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({
                                    'success': False,
                                    'message': f'Недостаточно товара на складе. Доступно: {stock_item_to_update.quantity}',
                                    'current_quantity': original_cart_quantity
                                })
                            messages.error(request, f'Недостаточно товара на складе. Доступно: {stock_item_to_update.quantity}')
                            return redirect('store:cart_detail')

                        # Уменьшаем количество на складе
                        stock_item_to_update.quantity -= quantity_diff
                    elif quantity_diff < 0:
                        # Возвращаем товар на склад
                        stock_item_to_update.quantity += abs(quantity_diff)

                    # Сохраняем изменения
                    stock_item_to_update.save(update_fields=['quantity'])
                    cart_item.quantity = quantity
                    cart_item.save()
                    message = 'Количество обновлено'

                # Перезагрузка корзины из БД перед использованием в JsonResponse
                cart = Cart.objects.get(pk=cart.pk)

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    cart_items_html = render_to_string(
                        'store/partials/cart_items_partial.html',
                        {'cart_items': cart.items.select_related('stock_item__strain', 'stock_item__strain__seedbank')}
                    )
                    cart_summary_html = render_to_string(
                        'store/partials/cart_summary_partial.html',
                        {'cart': cart}
                    )

                    # Получаем обновленную информацию о товаре
                    updated_cart_item = None
                    if quantity > 0:
                        updated_cart_item = CartItem.objects.filter(id=cart_item_id, cart=cart).first()

                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'cart_total_items': cart.get_total_items(),
                        'cart_total_amount': float(cart.get_total_amount()),
                        'item_total_price': float(updated_cart_item.get_total()) if updated_cart_item else 0,
                        'quantity': quantity,  # Добавляем текущее количество
                        'cart_items_html': cart_items_html,
                        'cart_summary_html': cart_summary_html,
                        'discount_amount': float(cart.discount_amount),
                        'subtotal_amount': float(cart.subtotal_amount),
                        'applied_coupon_code': cart.applied_coupon.code if cart.applied_coupon else None,
                        'stock_item_id': cart_item.stock_item.id if quantity > 0 else stock_item_to_update.id,
                        'updated_stock_quantity': stock_item_to_update.quantity
                    })

                messages.success(request, message)
                return redirect(reverse('store:cart_detail'))

        except Exception as e:
            logger.error(f"Ошибка при обновлении корзины (user: {request.user.username if request.user.is_authenticated else f'Guest Session: {request.session.session_key}'}, cart_item_id: {cart_item_id}): {e}", exc_info=True)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Ошибка при обновлении корзины'
                })
            messages.error(request, 'Ошибка при обновлении корзины')
            return redirect(reverse('store:cart_detail'))

class RemoveFromCartView(View):
    """Удаление товара из корзины"""

    def post(self, request, *args, **kwargs):
        cart_item_id = request.POST.get('cart_item_id')
        cart, _ = get_cart(request)

        if not cart:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Корзина не найдена.'})
            messages.error(request, 'Корзина не найдена.')
            return redirect('store:catalog')

        try:
            cart_item = get_object_or_404(
                CartItem,
                id=cart_item_id,
                cart=cart
            )
            stock_item_id_removed = cart_item.stock_item.id
            quantity_removed = cart_item.quantity
            stock_item_affected = cart_item.stock_item
            stock_item_affected.quantity += quantity_removed
            stock_item_affected.save(update_fields=['quantity'])
            current_stock_quantity = stock_item_affected.quantity
            cart_item.delete()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                cart_items_html = render_to_string(
                    'store/partials/cart_items_partial.html',
                    {'cart_items': cart.items.select_related('stock_item__strain', 'stock_item__strain__seedbank')}
                )
                cart_summary_html = render_to_string(
                    'store/partials/cart_summary_partial.html',
                    {'cart': cart}
                )
                return JsonResponse({
                    'success': True,
                    'message': 'Товар удален из корзины',
                    'cart_total_items': cart.get_total_items(),
                    'cart_total_amount': float(cart.get_total_amount()),
                    'cart_items_html': cart_items_html,
                    'cart_summary_html': cart_summary_html,
                    'discount_amount': float(cart.discount_amount),
                    'subtotal_amount': float(cart.subtotal_amount),
                    'applied_coupon_code': cart.applied_coupon.code if cart.applied_coupon else None,
                    'stock_item_id': stock_item_id_removed,
                    'updated_stock_quantity': current_stock_quantity
                })

            messages.success(request, 'Товар удален из корзины')
            return redirect(reverse('store:cart_detail'))

        except Exception as e:
            logger.error(f"Ошибка при удалении товара из корзины (user: {request.user.username if request.user.is_authenticated else f'Guest Session: {request.session.session_key}'}, cart_item_id: {cart_item_id}): {e}", exc_info=True)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Ошибка при удалении товара'
                })
            messages.error(request, 'Ошибка при удалении товара')
            return redirect(reverse('store:cart_detail'))
