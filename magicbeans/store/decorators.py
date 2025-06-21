from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps


def owner_required(view_func=None):
    """
    Декоратор для проверки, является ли пользователь владельцем магазина.
    """
    def check_owner(user):
        """Проверка на владельца."""
        return user.is_superuser or user.groups.filter(name="Владельцы").exists()

    actual_decorator = user_passes_test(check_owner)

    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def admin_required(view_func=None):
    """
    Декоратор для проверки, является ли пользователь администратором магазина.
    """
    def check_admin(user):
        """Проверка на администратора."""
        return (user.is_superuser
                or user.groups.filter(name="Владельцы").exists()
                or user.groups.filter(name="Администраторы").exists())

    actual_decorator = user_passes_test(check_admin)

    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def permission_required_or_403(perm):
    """
    Декоратор для проверки наличия конкретного права у пользователя.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator
