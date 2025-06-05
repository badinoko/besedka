from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404

from ..models import Order

class MyOrdersView(LoginRequiredMixin, ListView):
    """Мои заказы"""
    model = Order
    template_name = 'store/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        """Получаем заказы пользователя"""
        queryset = Order.objects.for_user(self.request.user).select_related(
            'status', 'shipping_method', 'payment_method'
        ).prefetch_related('items__stock_item__strain__seedbank')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Статистика заказов
        user_orders = self.get_queryset()
        context['orders_stats'] = {
            'total': user_orders.count(),
            'completed': user_orders.filter(status__is_final=True).count(),
            'active': user_orders.filter(status__is_final=False).count(),
        }

        # Хлебные крошки
        context['breadcrumbs'] = [
            {'title': 'Главная', 'url': '/'},
            {'title': 'Личный кабинет', 'url': '/users/profile/'},
            {'title': 'Мои заказы', 'url': None}
        ]

        return context

class OrderDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр заказа"""
    model = Order
    template_name = 'store/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Получаем заказы пользователя"""
        return Order.objects.for_user(self.request.user)

    def get_object(self, queryset=None):
        """Получаем заказ с проверкой доступа"""
        try:
            return super().get_object(queryset)
        except Http404:
            # Проверяем, существует ли заказ вообще
            if Order.objects.filter(pk=self.kwargs.get('pk')).exists():
                messages.error(self.request, 'У вас нет доступа к этому заказу')
            else:
                messages.error(self.request, 'Заказ не найден')
            raise Http404()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Позиции заказа
        context['order_items'] = self.object.items.select_related(
            'stock_item__strain__seedbank'
        ).order_by('id')

        # История статусов (если будет реализована)
        # context['status_history'] = self.object.status_history.order_by('-created_at')

        # Хлебные крошки
        context['breadcrumbs'] = [
            {'title': 'Главная', 'url': '/'},
            {'title': 'Личный кабинет', 'url': '/users/profile/'},
            {'title': 'Мои заказы', 'url': '/store/orders/'},
            {'title': f'Заказ #{self.object.id}', 'url': None}
        ]

        return context
