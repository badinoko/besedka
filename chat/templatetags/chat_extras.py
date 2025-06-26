from django import template
from django.db.models import Q

register = template.Library()


@register.filter
def user(obj, user_obj):
    """
    Фильтр для получения партнера в приватном чате или количества непрочитанных сообщений
    Использование: {{ thread.get_partner|user:request.user }}
    """
    if hasattr(obj, '__call__'):
        # Если это метод (например, get_partner), вызываем его с пользователем
        return obj(user_obj)
    elif hasattr(obj, 'unread_count'):
        # Если это комната с методом unread_count
        return obj.unread_count(user_obj)
    return obj


@register.simple_tag
def get_partner(current_user, thread):
    """
    Получить партнера в приватном чате
    Использование: {% get_partner request.user thread as partner %}
    """
    return thread.get_partner(current_user)


@register.simple_tag
def unread_count(room, user):
    """
    Количество непрочитанных сообщений в комнате для пользователя
    Использование: {% unread_count room request.user as count %}
    """
    return room.unread_count(user)


@register.simple_tag
def is_unread(message, user):
    """
    Проверить, является ли сообщение непрочитанным для пользователя
    Использование: {% is_unread message request.user as unread %}
    """
    if message is not None:
        if message.author == user:
            return False
        return message.unread
    return False


@register.simple_tag
def can_access_vip_chat(user):
    """
    Проверить, может ли пользователь получить доступ к VIP чату
    Использование: {% can_access_vip_chat request.user as vip_access %}

    ВРЕМЕННО: VIP чат отключен до реализации кастомного чата
    """
    if not user or not user.is_authenticated:
        return False

    # Проверяем роль пользователя для доступа к VIP чату
    # Пока что разрешаем доступ владельцам и администраторам
    if hasattr(user, 'role'):
        return user.role in ['owner', 'store_owner', 'moderator']

    return False
