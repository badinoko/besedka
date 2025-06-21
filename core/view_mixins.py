from django.db.models import Count, Q
from django.templatetags.static import static

class UnifiedCardMixin:
    """
    Миксин для унификации данных, передаваемых в шаблон карточки.

    Этот миксин перехватывает контекст ListView, находит в нем объект
    пагинации (`page_obj`) и заменяет каждый объект в нем на
    стандартизированный словарь с унифицированными полями.

    Это позволяет шаблону unified_card.html быть предельно простым
    и не содержать логики `if/else` для разных типов моделей.
    """
    def get_unified_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context.get('page_obj')
        card_type = self.get_card_type()

        if page_obj:
            unified_cards = []
            for item in page_obj:
                unified_cards.append(self.get_unified_card_data(item, card_type))

            # Заменяем стандартный page_obj на новый, с унифицированными данными
            context['unified_card_list'] = unified_cards

        return context

    def get_card_type(self):
        # Этот метод должен быть переопределен в дочернем View,
        # если card_type не передается в context_data
        return self.kwargs.get('card_type') or getattr(self, 'card_type', None)

    def get_unified_card_data(self, item, card_type):
        """
        Преобразует объект модели в унифицированный словарь.
        """
        if card_type == 'photo':
            return {
                'url': item.get_absolute_url(),
                'image_url': item.image.url if item.image else static('images/placeholders/gallery_placeholder.jpg'),
                'title': item.title or 'Без названия',
                'author_name': item.author.username,
                'author_url': '#',  # Заменить на URL профиля автора
                'stats': [
                    {'icon': 'fa-heart', 'count': item.likes.count()},
                    {'icon': 'fa-comment', 'count': item.comments.count()},
                ],
                'is_pinned': False,
                'badge_text': 'Приватное' if not getattr(item, 'is_public', True) else '',
                'badge_class': 'bg-dark',
                'content_preview': f"Автор: {item.author.username}"
            }
        elif card_type == 'news':
            return {
                'url': item.get_absolute_url(),
                'image_url': item.image.url if item.image else static('images/placeholders/news_placeholder.jpg'),
                'title': item.title,
                'author_name': item.author.username,
                'author_url': '#', # Заменить на URL профиля автора
                'stats': [
                    {'icon': 'fa-heart', 'count': item.likes.count()},
                    {'icon': 'fa-comment', 'count': item.comments.count()},
                    {'icon': 'fa-eye', 'count': item.views_count or 0},
                ],
                'is_pinned': getattr(item, 'is_pinned', False),
                'badge_text': 'Закреплено' if getattr(item, 'is_pinned', False) else '',
                'badge_class': 'bg-danger',
                'content_preview': item.content, # striptags и truncatechars будут в шаблоне
                'created_at': item.created_at,
            }
        elif card_type == 'growlog':
            primary_image = item.get_primary_image()
            return {
                'url': item.get_absolute_url(),
                'image_url': primary_image.url if primary_image else static('images/placeholders/growlog_placeholder.jpg'),
                'title': item.title,
                'author_name': item.user.username,
                'author_url': '#', # Заменить на URL профиля автора
                'stats': [
                    {'icon': 'fa-heart', 'count': item.likes.count()},
                    {'icon': 'fa-comment', 'count': item.comments.count()},
                    {'icon': 'fa-eye', 'count': item.views_count or 0},
                ],
                'is_pinned': False,
                'badge_text': item.get_status_display(),
                'badge_class': 'bg-success',
                'content_preview': f"Сорт: {item.strain.name}"
            }

        # По умолчанию возвращаем пустой словарь, чтобы избежать ошибок
        return {}

    def get_context_data(self, **kwargs):
        # Переопределяем get_context_data, чтобы он вызывал наш новый метод
        return self.get_unified_context_data(**kwargs)
