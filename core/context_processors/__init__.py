# Context processors for the Besedka platform

from .navigation import navigation_context as _navigation_context

# Фолбэк на случай если основной процессор недоступен по какой-то причине

def navigation_context(request):  # type: ignore
    """Безопасная обертка вокруг _navigation_context.
    Если основной процессор выбрасывает исключение, возвращает пустой контекст,
    чтобы не ронять весь сайт."""
    try:
        return _navigation_context(request)
    except Exception:  # pragma: no cover
        import logging
        logging.getLogger(__name__).exception("navigation_context fallback triggered")
        return {
            'cart_items_count': 0,
            'unread_notifications_count': 0,
            'user_role': None,
            'user_role_badge': None,
            'navigation_items': [],
            'admin_navigation_items': [],
            'admin_panel_access': False,
        }

__all__ = ["navigation_context"]
