from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.urls import reverse_lazy
from core.base_views import UnifiedListView

from ..models import Order

class MyOrdersView(LoginRequiredMixin, UnifiedListView):
    """Унифицированный список заказов пользователя"""
    model = Order
    template_name = 'base_list_page.html'
    context_object_name = 'orders'
    paginate_by = 12

    card_type = 'order'
    section_hero_class = 'store-hero'

    def get_queryset(self):
        return (
            Order.objects.for_user(self.request.user)
            .select_related('status', 'shipping_method', 'payment_method')
            .prefetch_related('items__stock_item__strain__seedbank')
            .order_by('-created_at')
        )

    def get_filter_list(self):
        return []

    def get_hero_stats(self):
        qs = self.get_queryset()
        return [
            {'value': qs.count(), 'label': 'Всего'},
            {'value': qs.filter(status__is_final=True).count(), 'label': 'Завершено'},
            {'value': qs.filter(status__is_final=False).count(), 'label': 'В процессе'},
        ]

    def get_unified_cards(self, page_obj):
        cards = []
        for order in page_obj:
            # Находим главное изображение: первая позиция заказа
            first_item = order.items.select_related('stock_item__strain').first()
            if first_item and first_item.stock_item.strain.image and hasattr(first_item.stock_item.strain.image, 'url'):
                image_url = first_item.stock_item.strain.image.url
            else:
                image_url = '/static/images/placeholders/store_placeholder.jpg'

            status_label = order.status.name if order.status else 'Новый'

            cards.append({
                'id': order.id,
                'type': 'order',
                'title': f'Заказ #{order.id}',
                'description': f'Статус: {status_label}',
                'image_url': image_url,
                'detail_url': reverse_lazy('store:order_detail', kwargs={'pk': order.id}),
                'author': {'name': self.request.user.username, 'avatar': self.request.user.avatar.url if getattr(self.request.user, 'avatar', None) else None},
                'stats': [
                    {'icon': 'fa-calendar', 'count': order.created_at.strftime('%d.%m.%Y'), 'css': 'date'},
                    {'icon': 'fa-tag', 'count': f"{order.total_price} ₽", 'css': 'price'},
                ],
                'created_at': order.created_at,
            })
        return cards

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
