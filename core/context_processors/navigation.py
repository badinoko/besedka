"""
Navigation context processor for Besedka platform
Provides unified navigation data across all pages and admin panels
"""
import logging
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from typing import Dict, Any

logger = logging.getLogger(__name__)


def navigation_context(request) -> Dict[str, Any]:
    """
    Context processor for unified navigation across the platform
    Returns navigation-related data for all templates
    """
    try:
        context: Dict[str, Any] = {
            'cart_items_count': 0,
            'unread_notifications_count': 0,
            'user_role': None,
            'user_role_badge': None,
            'navigation_items': [],
            'admin_navigation_items': [],
            'admin_panel_access': False,
        }

        # Basic user info
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            user = request.user
            context['user_role'] = get_user_role(user)
            context['admin_panel_access'] = has_admin_access(user)

            # Cart count for authenticated users
            context['cart_items_count'] = get_cart_count(request)

            # Notifications count
            context['unread_notifications_count'] = get_notifications_count(user)

            # Navigation items based on role
            context['navigation_items'] = get_navigation_items(user)
            context['user_role_badge'] = get_user_role_badge(user)
            context['admin_navigation_items'] = get_admin_navigation_items(user)

        logger.debug(f"Navigation context processed for request: {request.path}")
        return context

    except Exception as e:
        logger.error(f"Error in navigation context processor: {e}")
        # Return empty context on error to prevent page crashes
        return {
            'cart_items_count': 0,
            'unread_notifications_count': 0,
            'user_role': None,
            'user_role_badge': None,
            'navigation_items': [],
            'admin_navigation_items': [],
            'admin_panel_access': False,
        }


def get_user_role(user):
    """Determine user role for navigation display"""
    if not user or not user.is_authenticated:
        return 'guest'

    # Check specific roles
    if hasattr(user, 'role'):
        return user.role

    # Fallback role detection
    if user.is_superuser:
        return 'owner'
    elif user.is_staff:
        # Check group memberships for more specific roles
        groups = user.groups.values_list('name', flat=True)
        if 'store_owners' in groups:
            return 'store_owner'
        elif 'store_admins' in groups:
            return 'store_admin'
        elif 'moderators' in groups:
            return 'admin'
        else:
            return 'admin'

    return 'user'


def has_admin_access(user):
    """Check if user has access to any admin panel"""
    if not user or not user.is_authenticated:
        return False

    role = get_user_role(user)
    return role in ['owner', 'admin', 'store_owner', 'store_admin']


def get_cart_count(request):
    """Get shopping cart items count"""
    try:
        # Check session cart
        cart = request.session.get('cart', {})
        if cart:
            return sum(item.get('quantity', 0) for item in cart.values())

        # For authenticated users, could also check database cart
        if hasattr(request, 'user') and request.user.is_authenticated:
            # TODO: Implement database cart lookup if needed
            pass

        return 0
    except Exception as e:
        logger.warning(f"Error getting cart count: {e}")
        return 0


def get_notifications_count(user):
    """Get unread notifications count for user"""
    try:
        if not user or not user.is_authenticated:
            return 0

        # Use property from User model for consistency
        return user.unread_notifications_count

    except Exception as e:
        logger.warning(f"Error getting notifications count: {e}")
        return 0


def get_navigation_items(user):
    """Get navigation items based on user role"""
    try:
        role = get_user_role(user)

        # Base navigation items for all authenticated users
        items = [
            {'name': 'Главная', 'url': '/', 'icon': 'home'},
            {'name': 'Новости', 'url': '/', 'icon': 'newspaper'},
            {'name': 'Магазин', 'url': '/store/', 'icon': 'shopping-bag'},
            {'name': 'Гроурепорты', 'url': '/growlogs/', 'icon': 'leaf'},
            {'name': 'Галерея', 'url': '/gallery/', 'icon': 'camera'},
            {'name': 'Чат', 'url': '/chat/', 'icon': 'message-circle'},
        ]

        # Add admin items based on role
        if role == 'owner':
            items.append({'name': 'Админка', 'url': '/owner_admin/', 'icon': 'settings'})
        elif role == 'admin':
            items.append({'name': 'Модерация', 'url': '/moderator_admin/', 'icon': 'shield'})
        elif role == 'store_owner':
            items.append({'name': 'Управление магазином', 'url': '/store_owner_admin/', 'icon': 'store'})
        elif role == 'store_admin':
            items.append({'name': 'Админка магазина', 'url': '/store_admin_site/', 'icon': 'package'})

        return items

    except Exception as e:
        logger.warning(f"Error getting navigation items: {e}")
        return []


def get_user_role_badge(user):
    role = get_user_role(user)
    badge_map = {
        'owner': {'class': 'bg-success', 'text': 'Владелец'},
        'admin': {'class': 'bg-primary', 'text': 'Модератор'},
        'store_owner': {'class': 'bg-warning text-dark', 'text': 'Владелец магазина'},
        'store_admin': {'class': 'bg-info text-dark', 'text': 'Админ магазина'},
        'user': {'class': 'bg-secondary', 'text': 'Пользователь'},
        'guest': {'class': 'bg-light text-muted', 'text': 'Гость'},
    }
    return badge_map.get(role, {'class': 'bg-light text-muted', 'text': 'Гость'})


def get_admin_navigation_items(user):
    role = get_user_role(user)
    items = []
    if role == 'owner':
        items.append({'url': '/owner_admin/', 'icon': 'fa-crown', 'title': 'Админка владельца', 'type': 'admin_primary'})
        # Владелец уже может войти в админку модераторов из своей админки,
        # дублирующая ссылка не нужна (см. пользовательское требование).
        # items.append({'url': '/moderator_admin/', 'icon': 'fa-shield-alt', 'title': 'Админка модераторов', 'type': 'admin_secondary'})
    elif role == 'admin':
        items.append({'url': '/moderator_admin/', 'icon': 'fa-shield-alt', 'title': 'Админка модераторов', 'type': 'admin_primary'})
    elif role == 'store_owner':
        items.append({'url': '/store_owner_admin/', 'icon': 'fa-store', 'title': 'Админка магазина', 'type': 'admin_primary'})
        items.append({'url': '/store_admin_site/', 'icon': 'fa-box', 'title': 'Админка сотрудников', 'type': 'admin_secondary'})
    elif role == 'store_admin':
        items.append({'url': '/store_admin_site/', 'icon': 'fa-box', 'title': 'Админка магазина', 'type': 'admin_primary'})

    return items
