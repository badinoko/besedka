from django import template
from users.models import Notification
from core.context_processors.navigation import get_user_role_badge, get_admin_navigation_items

register = template.Library()

@register.inclusion_tag('core/partials/user_nav_simple.html', takes_context=True)
def user_info_badge(context):
    """
    Renders the user's name, role badge, and notification count.
    Does NOT handle navigation links to avoid circular imports.
    """
    request = context.get('request')
    user = request.user if request else None

    if not user or not user.is_authenticated:
        return {'is_authenticated': False}

    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    role_badge = get_user_role_badge(user)

    # Получаем навигацию админки из navigation_context функций
    admin_items = get_admin_navigation_items(user)

    return {
        'is_authenticated': True,
        'user': user,
        'unread_notifications_count': unread_count,
        'user_role_badge': role_badge,
        'admin_navigation_items': admin_items,
    }
