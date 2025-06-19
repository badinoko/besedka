"""
ЭТАЛОННЫЙ БАЗОВЫЙ КЛАСС ДЛЯ ВСЕХ СПИСКОВЫХ СТРАНИЦ ПРОЕКТА "БЕСЕДКА"
ВСЕ ListView ОБЯЗАНЫ НАСЛЕДОВАТЬСЯ ОТ ЭТОГО КЛАССА
ВЕРСИЯ: 1.0 - ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ
"""

from django.views.generic import ListView
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from core.constants import UNIFIED_PAGE_SIZE
from django.views.decorators.http import require_GET
from django.urls import reverse_lazy, reverse, NoReverseMatch
from core.utils import get_limited_top_level_comments
from core.utils import get_total_comments_count


class UnifiedListView(ListView):
    """
    ЕДИНЫЙ БАЗОВЫЙ КЛАСС ДЛЯ ВСЕХ СПИСКОВЫХ СТРАНИЦ
    Обеспечивает 100% одинаковое поведение всех разделов
    """
    template_name = 'base_list_page.html'  # ЕДИНЫЙ ШАБЛОН
    context_object_name = 'object_list'  # НЕ КОНФЛИКТУЕТ С page_obj ДЛЯ ПАГИНАЦИИ
    paginate_by = 9  # КАРТОЧКИ ВСЕГДА 3x3 = 9 ШТУК

    # ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ДЛЯ ПЕРЕОПРЕДЕЛЕНИЯ В НАСЛЕДНИКАХ
    section_title = "Заголовок секции"
    section_subtitle = "Подзаголовок секции"
    section_hero_class = "default-hero"
    card_type = "default"
    ajax_url_name = None  # str | None

    def get_hero_stats(self):
        """Переопределить в наследнике для статистики hero-секции"""
        return [
            {'icon': 'fa-list', 'count': 0, 'label': 'Всего записей'},
            {'icon': 'fa-users', 'count': 0, 'label': 'Авторы'},
            {'icon': 'fa-star', 'count': 0, 'label': 'Популярные'},
        ]

    def get_hero_actions(self):
        """Переопределить в наследнике для кнопок hero-секции"""
        return []

    def get_filter_list(self):
        """Переопределить в наследнике для фильтров"""
        return [
            {'id': 'all', 'label': 'Все', 'is_active': True}
        ]

    def get_unified_cards(self, page_obj):
        """Преобразует объекты в унифицированный формат карточек"""
        cards = []
        for item in page_obj:
            if self.card_type == 'news':
                image_url = getattr(item, 'image', None)
                if image_url and hasattr(image_url, 'url'):
                    image_url = image_url.url
                else:
                    image_url = '/static/images/placeholders/news_placeholder.jpg'
                stats = [
                    {'icon': 'fa-heart', 'count': item.likes.count() if hasattr(item, 'likes') else 0, 'css': 'likes'},
                    {'icon': 'fa-comment', 'count': get_total_comments_count(item), 'css': 'comments'},
                    {'icon': 'fa-eye', 'count': getattr(item, 'views', 0) or getattr(item, 'views_count', 0) or 0, 'css': 'views'},
                ]
                author_name = f"{item.author.get_role_icon} {item.author.display_name}" if hasattr(item, 'author') and item.author else 'Аноним'
                description = getattr(item, 'excerpt', '') or getattr(item, 'content', '')
            elif self.card_type == 'photo':
                image_url = getattr(item, 'image', None)
                if image_url and hasattr(image_url, 'url'):
                    image_url = image_url.url
                else:
                    image_url = '/static/images/placeholders/photo_placeholder.jpg'
                stats = [
                    {'icon': 'fa-heart', 'count': item.likes.count() if hasattr(item, 'likes') else 0, 'css': 'likes'},
                    {'icon': 'fa-comment', 'count': get_total_comments_count(item), 'css': 'comments'},
                    {'icon': 'fa-eye', 'count': getattr(item, 'views', 0) or getattr(item, 'views_count', 0) or 0, 'css': 'views'},
                ]
                author_name = f"{item.author.get_role_icon} {item.author.display_name}" if hasattr(item, 'author') and item.author else 'Аноним'
                description = getattr(item, 'description', '')
            elif self.card_type == 'growlog':
                image_url = getattr(item, 'main_photo', None) or getattr(item, 'image', None) or getattr(item, 'logo', None)
                if image_url and hasattr(image_url, 'url'):
                    image_url = image_url.url
                else:
                    image_url = '/static/images/placeholders/growlog_placeholder.jpg'
                stats = [
                    {'icon': 'fa-heart', 'count': item.likes.count() if hasattr(item, 'likes') else 0, 'css': 'likes'},
                    {'icon': 'fa-comment', 'count': get_total_comments_count(item), 'css': 'comments'},
                    {'icon': 'fa-eye', 'count': getattr(item, 'views', 0) or getattr(item, 'views_count', 0) or 0, 'css': 'views'},
                ]
                author_obj = getattr(item, 'grower', None) or getattr(item, 'user', None)
                if author_obj and hasattr(author_obj, 'display_name'):
                    author_name = f"{author_obj.get_role_icon} {author_obj.display_name}"
                else:
                    author_name = 'Аноним'
                description = getattr(item, 'setup_description', '') or getattr(item, 'short_description', '')
            elif self.card_type == 'store':
                # Карточки товаров (сортов семян)
                image_url = getattr(item, 'image', None)
                if image_url and hasattr(image_url, 'url'):
                    image_url = image_url.url
                else:
                    image_url = '/static/images/placeholders/store_placeholder.jpg'

                # Для магазина статистика пока не нужна, но можно вывести минимальную цену
                min_price = getattr(item, 'min_price', None)
                if not min_price and hasattr(item, 'stock_items'):
                    price_obj = item.stock_items.filter(is_active=True, quantity__gt=0).order_by('price').first()
                    min_price = price_obj.price if price_obj else None

                stats = []
                if min_price is not None:
                    stats.append({'icon': 'fa-tag', 'count': f"{min_price} ₽", 'css': 'price'})

                author_name = getattr(item, 'seedbank', None)
                if author_name and hasattr(author_name, 'name'):
                    author_name = author_name.name
                else:
                    author_name = 'Seedbank'

                description = getattr(item, 'description', '')
            elif self.card_type == 'notification':
                # Карточки уведомлений
                image_url = '/static/images/placeholders/notification_placeholder.jpg'

                # Определяем иконку по типу уведомления
                notification_icons = {
                    'system': 'fa-cog',
                    'like': 'fa-heart',
                    'comment': 'fa-comment',
                    'follow': 'fa-user-plus',
                    'mention': 'fa-at',
                    'order': 'fa-shopping-cart',
                    'chat_message': 'fa-comments',
                    'message': 'fa-bell'
                }
                icon = notification_icons.get(getattr(item, 'notification_type', ''), 'fa-bell')

                stats = [
                    {'icon': icon, 'count': getattr(item, 'get_notification_type_display_verbose', lambda: 'Уведомление')(), 'css': 'notification-type'}
                ]

                author_name = 'Система'
                description = getattr(item, 'message', '')
            else:
                image_url = '/static/images/placeholders/default_placeholder.jpg'
                stats = []
                author_name = 'Аноним'
                description = ''

            cards.append({
                'id': item.id,
                'type': self.card_type,
                'title': item.name if self.card_type == 'store' and hasattr(item, 'name') else getattr(item, 'title', getattr(item, 'name', '')),
                'description': description,
                'image_url': image_url,
                'detail_url': item.get_absolute_url() if hasattr(item, 'get_absolute_url') else '#',
                'author': {
                    'name': author_name,
                    'avatar': None,  # Можно доработать позже
                },
                'stats': stats,
                'created_at': getattr(item, 'created_at', None),
            })
        return cards

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_list = self.get_filter_list()
        # Унификация: если filter не передан, берем id первой кнопки фильтра
        current_filter = self.request.GET.get('filter')
        if not current_filter and filter_list:
            current_filter = filter_list[0]['id']
        else:
            current_filter = current_filter or 'newest'

        # ВАЖНО: Django автоматически создает page_obj при пагинации ListView
        page_obj = context.get('page_obj')

        # УНИФИЦИРОВАННЫЙ КОНТЕКСТ HERO-СЕКЦИИ
        context['hero_context'] = {
            'section_title': self.section_title,
            'section_subtitle': self.section_subtitle,
            'section_hero_class': self.section_hero_class,
            'stats_list': self.get_hero_stats(),
            'actions_list': self.get_hero_actions() if self.request.user.is_authenticated else []
        }

        # УНИФИЦИРОВАННЫЙ КОНТЕКСТ ФИЛЬТРОВ
        for filter_item in filter_list:
            filter_item['is_active'] = filter_item['id'] == current_filter
        context['filter_context'] = {'filter_list': filter_list}
        context['current_filter'] = current_filter

        # УНИФИЦИРОВАННЫЕ КАРТОЧКИ
        if page_obj:
            context['unified_card_list'] = self.get_unified_cards(page_obj)
        else:
            context['unified_card_list'] = []

        # AJAX URL для JS-обработчика
        ajax_url = None
        if self.ajax_url_name:
            try:
                ajax_url = reverse(self.ajax_url_name)
            except NoReverseMatch:
                ajax_url = None
        if not ajax_url and self.model:
            try:
                ajax_url = reverse(f"{self.model._meta.app_label}:ajax_filter")
            except NoReverseMatch:
                ajax_url = None
        context['ajax_url'] = ajax_url or ''
        context['card_type'] = self.card_type
        return context

    def apply_filters(self, queryset):
        """Применение фильтров - базовая реализация"""
        filter_type = self.request.GET.get('filter', 'newest')

        if filter_type == 'popular':
            # Сортировка по популярности (лайки + комментарии)
            queryset = queryset.annotate(
                popularity=Count('likes') + Count('comments')
            ).order_by('-popularity', '-created_at')
        elif filter_type == 'commented':
            # Сортировка по количеству комментариев
            queryset = queryset.annotate(
                comments_count=Count('comments')
            ).order_by('-comments_count', '-created_at')
        else:  # newest
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_queryset(self):
        """Базовая реализация с фильтрацией"""
        queryset = super().get_queryset()
        return self.apply_filters(queryset)


def unified_ajax_filter(view_class):
    """
    ДЕКОРАТОР для создания AJAX-обработчика на основе UnifiedListView
    Гарантирует единообразие всех AJAX-фильтров
    """
    def ajax_view(request):
        # Создаем экземпляр view
        view = view_class()
        view.request = request

        # Получаем отфильтрованный queryset
        queryset = view.get_queryset()

        # Пагинация
        paginator = Paginator(queryset, view.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Формируем контекст
        context = {
            'page_obj': page_obj,
            'card_type': view.card_type,
            'unified_card_list': view.get_unified_cards(page_obj),
            'request': request,
        }

        # Рендерим HTML
        cards_html = render_to_string(
            'includes/partials/_unified_cards_wrapper.html',
            context
        )
        pagination_html = render_to_string(
            'includes/partials/_unified_pagination.html',
            context
        )

        return JsonResponse({
            'cards_html': cards_html,
            'pagination_html': pagination_html,
            'success': True
        })

    return ajax_view
