"""
ЭТАЛОННЫЙ ПРИМЕР РЕАЛИЗАЦИИ СПИСКОВОЙ СТРАНИЦЫ
Показывает КАК ПРАВИЛЬНО наследоваться от UnifiedListView
"""

from django.db.models import Count
from growlogs.models import GrowLog
from core.base_views import UnifiedListView, unified_ajax_filter


class GrowLogListView(UnifiedListView):
    """
    ПРАВИЛЬНАЯ реализация списка гроурепортов
    ВСЕ ОБЯЗАТЕЛЬНЫЕ атрибуты определены
    """

    # Модель
    model = GrowLog

    # ОБЯЗАТЕЛЬНЫЕ атрибуты базового класса
    hero_title = "Гроу-репорты"
    hero_subtitle = "Дневники выращивания от нашего сообщества"
    hero_class = "growlogs"
    ajax_url_name = "growlogs:filter_ajax"
    card_type = "growlog"

    # Кастомные фильтры для гроурепортов
    def get_filters(self):
        """Переопределяем фильтры для гроурепортов"""
        return {
            'newest': {'label': 'Новые', 'icon': 'fa-clock'},
            'popular': {'label': 'Популярные', 'icon': 'fa-fire'},
            'my': {'label': 'Мои репорты', 'icon': 'fa-user'},
            'completed': {'label': 'Завершенные', 'icon': 'fa-check'},
            'active': {'label': 'Активные', 'icon': 'fa-seedling'},
        }

    def get_stats(self):
        """ОБЯЗАТЕЛЬНАЯ реализация статистики"""
        total = GrowLog.objects.count()
        active = GrowLog.objects.filter(status='active').count()
        return [
            {
                'icon': 'fa-book',
                'count': total,
                'label': 'Всего репортов',
                'aos_delay': 100
            },
            {
                'icon': 'fa-seedling',
                'count': active,
                'label': 'Активных',
                'aos_delay': 200
            },
            {
                'icon': 'fa-users',
                'count': GrowLog.objects.values('author').distinct().count(),
                'label': 'Авторов',
                'aos_delay': 300
            }
        ]

    def get_card_data(self, growlog):
        """ОБЯЗАТЕЛЬНАЯ реализация данных карточки"""
        return {
            'id': growlog.id,
            'type': 'growlog',
            'title': growlog.title,
            'description': growlog.description[:150] + '...' if len(growlog.description) > 150 else growlog.description,
            'image_url': growlog.cover_image.url if growlog.cover_image else '/static/images/placeholders/growlog_placeholder.jpg',
            'detail_url': growlog.get_absolute_url(),
            'author': {
                'name': growlog.author.username,
                'avatar': growlog.author.avatar.url if growlog.author.avatar else None,
                'url': f"/users/{growlog.author.username}/"
            },
            'stats': [
                {'icon': 'fa-heart', 'count': growlog.likes.count()},
                {'icon': 'fa-comment', 'count': growlog.comments.count()},
                {'icon': 'fa-eye', 'count': growlog.views_count or 0},
            ],
            'badges': self._get_badges(growlog),
            'created_at': growlog.created_at,
        }

    def _get_badges(self, growlog):
        """Получение бейджей для карточки"""
        badges = []
        if growlog.is_pinned:
            badges.append({
                'text': 'Закреплено',
                'class': 'bg-danger'
            })
        if growlog.status == 'completed':
            badges.append({
                'text': 'Завершен',
                'class': 'bg-success'
            })
        return badges

    def apply_filters(self, queryset):
        """Расширенная фильтрация для гроурепортов"""
        filter_type = self.request.GET.get('filter', 'newest')

        # Базовые фильтры из родителя
        if filter_type in ['newest', 'popular', 'commented']:
            return super().apply_filters(queryset)

        # Специфичные фильтры
        if filter_type == 'my' and self.request.user.is_authenticated:
            queryset = queryset.filter(author=self.request.user)
        elif filter_type == 'completed':
            queryset = queryset.filter(status='completed')
        elif filter_type == 'active':
            queryset = queryset.filter(status='active')

        return queryset.order_by('-created_at')


# AJAX обработчик создается автоматически через декоратор
growlogs_filter_ajax = unified_ajax_filter(GrowLogListView)
