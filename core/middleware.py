import re
from django.conf import settings
from django.urls import resolve
from django.db.models import signals
from django.utils.deprecation import MiddlewareMixin
from magicbeans_store.models import Strain, StockItem
from growlogs.models import GrowLog
from gallery.models import Photo
import threading
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.utils.encoding import force_str
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render
from django.urls import reverse, NoReverseMatch
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.contrib import messages
from datetime import datetime # Исправлено: timezone убран
from django.utils import timezone
from users.models import UserProfile # Предполагается, что UserProfile тут
from .models import MaintenanceModeSetting
import logging  # ➕ Добавлено для логирования на лету

# Глобальная переменная для хранения текущего пользователя
_thread_locals = threading.local()

# Инициализируем модульный логгер
logger = logging.getLogger(__name__)

def get_current_user():
    """
    Возвращает текущего пользователя из request.
    """
    return getattr(_thread_locals, 'user', None)

class RequestUserMiddleware(MiddlewareMixin):
    """
    Middleware для сохранения текущего пользователя в thread local storage.
    """
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)

    def process_response(self, request, response):
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        return response

    def process_exception(self, request, exception):
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user

class ActionLogMiddleware(MiddlewareMixin):
    """
    Middleware для логирования действий пользователей.
    """
    IGNORED_PATHS = [
        r'^/admin/jsi18n/',
        r'^/static/',
        r'^/media/',
        r'^/__debug__/',
    ]

    def __init__(self, get_response=None):
        self.get_response = get_response
        # Компилируем регулярные выражения
        self.ignored_paths = [re.compile(path) for path in self.IGNORED_PATHS]

    def should_log(self, request, response):
        """Определяет, нужно ли логировать запрос."""
        # Игнорируем определенные пути
        path = request.path
        for pattern in self.ignored_paths:
            if pattern.match(path):
                return False

        # Игнорируем запросы без аутентифицированного пользователя
        if not request.user.is_authenticated:
            return False

        # Игнорируем определенные HTTP методы
        if request.method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            return False

        # Проверяем статус ответа (только успешные)
        if response.status_code >= 400:
            return False

        return True

    def process_response(self, request, response):
        # Проверяем, нужно ли логировать
        if not self.should_log(request, response):
            return response

        # Получаем информацию о запросе
        user = request.user
        path = request.path
        method = request.method

        # Определяем действие
        action_type = 'view'  # Значение по умолчанию
        if method == 'POST':
            # Проверяем на logout и login
            if '/accounts/logout/' in path:
                action_type = 'logout'
            elif '/accounts/login/' in path:
                action_type = 'login'
            else:
                action_type = 'add'
        elif method in ['PUT', 'PATCH']:
            action_type = 'edit'
        elif method == 'DELETE':
            action_type = 'delete'

        # Определяем модель и объект
        try:
            match = resolve(path)
            app_name = match.app_name or match.namespace or 'unknown'
            view_name = match.url_name or 'unknown'

            # Формируем детали
            details = {
                'method': method,
                'path': path,
                'view': f"{app_name}:{view_name}",
            }

            # Добавляем параметры POST запроса (за исключением чувствительных данных)
            if method == 'POST' and hasattr(request, 'POST'):
                post_data = {}
                for key, value in request.POST.items():
                    # Исключаем пароли и CSRF токены
                    if 'password' not in key.lower() and 'csrfmiddlewaretoken' not in key.lower():
                        post_data[key] = value
                details['post_data'] = post_data

            # Логируем действие
            from core.models import ActionLog
            ActionLog.objects.create(
                user=user,
                action_type=action_type,
                model_name=app_name,
                object_id=None,  # Не всегда можем определить ID объекта
                object_repr=view_name,
                details=json.dumps(details),
            )

            # Логируем действие в файл/консоль для оперативного отслеживания
            logger.info(
                "User '%s' performed '%s' on view '%s' (%s %s)",
                user.username,
                action_type,
                f"{app_name}:{view_name}",
                method,
                path,
            )

        except Exception as e:
            # В случае ошибки выводим в лог и не мешаем основному запросу
            logger.exception("Error logging action: %s", e)

        return response

# This is the actual signal handler that sets the _change_user on model instances
# before they are saved or deleted. This connects to pre_save and pre_delete signals.

def connect_signals():
    """Connect pre_save and pre_delete signals to set _change_user on model instances."""
    signals.pre_save.connect(set_change_user)
    signals.pre_delete.connect(set_change_user)

def set_change_user(sender, instance, **kwargs):
    """
    Set the _change_user on a model instance before it is saved or deleted.
    This allows the instance to know which user is making the change.
    """
    # Skip if the instance already has a _change_user attribute or
    # if the sender is not a model class we care about
    if getattr(instance, '_change_user', None) is not None:
        return

    # Get the current user from thread local storage
    current_user = get_current_user()
    if current_user:
        instance._change_user = current_user

# Connect the signals when the app is loaded
connect_signals()

class AdminRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Сначала получаем response, чтобы он был доступен, если мы не делаем редирект
        response = self.get_response(request)
        path = request.path
        user = request.user

        # Исключения - пути, которые не должны подвергаться редиректу
        excluded_paths = [
            '/users/',           # Личный кабинет и пользовательские страницы
            '/accounts/',        # Авторизация
            '/store/',           # Магазин для покупателей
            '/growlogs/',        # Гроу-логи
            '/gallery/',         # Галерея
            '/chat/',            # Чат
            '/api/',             # API
            '/static/',          # Статические файлы
            '/media/',           # Медиа файлы
            '/__debug__/',       # Debug toolbar
            '/test-navigation/', # Тестовая навигация
            '/',                 # Главная страница
        ]

        # Исключаем логин-страницы админок от редиректов
        admin_login_paths = [
            '/owner_admin/login/',
            '/moderator_admin/login/',
            '/store_owner/login/',
            '/store_admin/login/',
            '/store_admin_site/login/',
        ]

        # Проверяем, не находится ли путь в исключениях
        for excluded_path in excluded_paths:
            if path.startswith(excluded_path):
                return response

        # Проверяем логин-страницы админок
        for admin_login_path in admin_login_paths:
            if path.startswith(admin_login_path):
                return response

                # Только перенаправляем с /admin/ на соответствующие админки
        if user.is_authenticated and user.is_staff and path == '/admin/':
            user_role = getattr(user, 'role', None)

            if user_role == 'owner':
                return redirect('/owner_admin/')
            elif user_role == 'store_owner':
                return redirect('/store_owner/')
            elif user_role == 'admin':
                return redirect('/moderator_admin/')
            elif user_role == 'store_admin':
                return redirect('/store_admin_site/')

        return response # Возвращаем исходный response если не было редиректов

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        # Allowed URL names when a temporary password is active
        # 'account_login' is implicitly allowed as the user might be redirected there after logout
        allowed_url_names_for_temp_password = [
            'account_logout',
            'account_change_password',
        ]

        # Add admin logout if user is staff and needs to logout from an admin page
        # This depends on how your admin logout is named.
        # Example: 'admin:logout'
        if request.user.is_staff:
            # Attempt to resolve admin logout URL. This is a common pattern.
            try:
                admin_logout_url = reverse('admin:logout')
                if request.path == admin_logout_url: # Check if current path is admin logout
                     resolved_url_name = resolve(admin_logout_url).url_name
                     if resolved_url_name:  # Проверяем что url_name не None
                         allowed_url_names_for_temp_password.append(resolved_url_name)
            except: # nosec
                pass # admin:logout might not exist or other admin logout names used.

        current_url_name = None
        if request.resolver_match:
            current_url_name = request.resolver_match.url_name

        # Allow access to static files and media if served by Django in DEBUG
        if settings.DEBUG:
            if request.path.startswith(settings.STATIC_URL) or \
               (settings.MEDIA_URL and request.path.startswith(settings.MEDIA_URL)):
                return None

        # Check for debug toolbar
        if settings.DEBUG and request.path.startswith('/__debug__/'):
            return None

        profile = getattr(request.user, 'profile_extra', None)

        if profile and profile.temp_password:
            if profile.is_temp_password_expired():
                logout(request)
                messages.error(request, _("Ваш временный пароль истек. Пожалуйста, войдите снова и немедленно смените пароль. Если проблема сохранится, обратитесь к администратору."))
                return redirect(reverse('account_login'))

            if current_url_name not in allowed_url_names_for_temp_password:
                # Allow access to any URL under /admin/logout/ if it's not a named URL,
                # this is a fallback for admin logout.
                if request.path.startswith('/admin/logout/'):
                    return None

                messages.info(request, _("Вам необходимо сменить временный пароль."))
                return redirect(reverse('account_change_password'))

        return None

# Карта префиксов URL к идентификаторам разделов в MaintenanceModeSetting
# Ключ - начало URL-пути, Значение - section_name из модели MaintenanceModeSetting.SECTION_CHOICES
SECTION_URL_PREFIX_TO_SLUG_MAP = {
    '/chat/': 'chat',
    '/gallery/': 'gallery',
    '/growlogs/': 'growlogs',
    '/store/': 'store',
    # Добавьте другие разделы, если необходимо
}

# URL-имена, которые нужно исключить из проверки (например, сама страница обслуживания)
EXCLUDED_URL_NAMES = ['core:maintenance_page', 'core:maintenance_page_default']

# Префиксы URL, которые нужно исключить (например, админка)
EXCLUDED_URL_PREFIXES = [
    settings.STATIC_URL,
    settings.MEDIA_URL,
    '/admin/',
    '/owner_admin/',
    '/owner-admin/',  # дефисный вариант
    '/store_owner/',
    '/store_admin/',
    '/moderator_admin/',
    '/moderator-admin/',  # дефисный вариант
    '/internal/core/maintenance/', # Путь к самой странице обслуживания
    '/__debug__/', # Django Debug Toolbar
    '/accounts/', # Страницы аутентификации Allauth
    '/store_admin_site/',
]

class MaintenanceModeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        current_path = request.path_info

        # 1. Исключаем служебные URL и админки
        for prefix in EXCLUDED_URL_PREFIXES:
            if prefix and current_path.startswith(prefix):
                return None # Не обрабатываем

        try:
            resolved_url = resolve(current_path)
            if resolved_url.view_name in EXCLUDED_URL_NAMES:
                return None # Не обрабатываем
        except Exception:
            pass # Если URL не разрешается, продолжаем проверку по префиксам

        # 2. Определяем, к какому разделу относится текущий URL
        target_section_slug = None
        for prefix, slug in SECTION_URL_PREFIX_TO_SLUG_MAP.items():
            if current_path.startswith(prefix):
                target_section_slug = slug
                break

        if not target_section_slug:
            return None # URL не относится к отслеживаемым разделам

        # 3. Проверяем, включен ли режим обслуживания для этого раздела
        try:
            maintenance_setting = MaintenanceModeSetting.objects.get(
                section_name=target_section_slug,
                is_enabled=True
            )
            # Если режим обслуживания включен и текущий путь не является самой страницей обслуживания,
            # то перенаправляем на страницу обслуживания.
            # (проверка на то, что мы не на странице обслуживания уже сделана выше по EXCLUDED_URL_PREFIXES)

            # Формируем URL для страницы обслуживания с указанием section_slug
            maintenance_url = reverse('core:maintenance_page', kwargs={'section_slug': target_section_slug})

            # Предотвращаем бесконечный редирект, если вдруг что-то пошло не так
            # Эта проверка дублирует EXCLUDED_URL_PREFIXES, но для надежности
            if current_path == maintenance_url:
                 return None

            return redirect(maintenance_url)

        except MaintenanceModeSetting.DoesNotExist:
            # Режим обслуживания для этого раздела не найден или выключен
            return None
        except NoReverseMatch:
            # Не удалось построить URL для страницы обслуживания, это серьезная ошибка конфигурации
            # В этом случае лучше ничего не делать, чтобы не сломать сайт полностью
            # Логируем ошибку
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Could not reverse URL for maintenance page with slug {target_section_slug}. Check core.urls.")
            return None
        except Exception as e:
            # Другие возможные ошибки - используем логирование вместо print
            import logging
            logger = logging.getLogger(__name__)
            try:
                error_message = str(e)
            except UnicodeDecodeError:
                error_message = repr(e)
            except Exception:
                error_message = "Unknown error in MaintenanceModeMiddleware"
            logger.error(f"MaintenanceModeMiddleware error: {error_message}")
            return None

        return None


class DisableCSRFForOAuth(MiddlewareMixin):
    """
    Отключает CSRF проверку для OAuth эндпоинтов.
    Необходимо для работы кросс-доменных OAuth запросов из Rocket.Chat.
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Отключаем CSRF для всех OAuth путей
        if request.path.startswith('/o/'):
            setattr(request, '_dont_enforce_csrf_checks', True)

        # Также отключаем CSRF для логина если это часть OAuth flow
        # Проверяем наличие OAuth параметров в next URL
        if request.path == '/accounts/login/' and request.method == 'POST':
            next_url = request.GET.get('next', '') or request.POST.get('next', '')
            if '/o/authorize/' in next_url and 'BesedkaRocketChat2025' in next_url:
                setattr(request, '_dont_enforce_csrf_checks', True)

        return None
