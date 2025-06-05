from django.urls import reverse
from django.contrib.auth import get_user_model

UserModel = get_user_model()

def navigation_context(request):
    """Добавляет навигационные элементы и количество уведомлений в контекст всех шаблонов"""
    try:
        user = request.user # Получаем пользователя
        is_authenticated = user.is_authenticated # Проверяем аутентификацию

        # Инициализируем переменные значениями по умолчанию
        navigation_items = []
        admin_navigation_items = []
        user_role_badge = None
        unread_notifications_count = 0 # По умолчанию 0

        if is_authenticated:
            # Получаем навигационные элементы для личного кабинета
            navigation_items = get_user_navigation_items(user)
            # Получаем админские навигационные элементы
            admin_navigation_items = get_admin_navigation_items(user)
            # Получаем бейдж роли
            user_role_badge = get_role_badge(user)
            # Получаем количество непрочитанных уведомлений
            # Предполагается, что у модели User есть related_name 'notifications'
            # и у Notification есть метод unread_notifications_count или похожее свойство
            # или напрямую через user.notifications.filter(is_read=False).count()
            if hasattr(user, 'notifications'): # Проверяем, что у пользователя есть менеджер уведомлений
                try:
                    unread_notifications_count = user.notifications.filter(is_read=False).count()
                except Exception as e:
                    # В случае ошибки (например, если related_name другой или модель не готова)
                    # просто оставляем 0 и не ломаем сайт
                    print(f"Error getting unread notifications count: {e}") # Можно добавить логирование
                    unread_notifications_count = 0

        return {
            'navigation_items': navigation_items,
            'admin_navigation_items': admin_navigation_items,
            'user_role_badge': user_role_badge,
            'breadcrumb_context': get_breadcrumb_context(request),
            'unread_notifications_count': unread_notifications_count # Добавляем в контекст
        }
    except Exception as e:
        # В случае любой ошибки возвращаем пустой контекст
        print(f"Error in navigation_context: {e}")
        return {
            'navigation_items': [],
            'admin_navigation_items': [],
            'user_role_badge': None,
            'breadcrumb_context': [],
            'unread_notifications_count': 0
        }

def get_user_navigation_items(user):
    """Возвращает пункты меню личного кабинета в зависимости от роли"""
    # Убедимся, что user аутентифицирован и имеет атрибут role
    if not user.is_authenticated or not hasattr(user, 'role'):
        return []

    items = [
        {'title': 'Личный кабинет', 'url': reverse('users:profile'), 'icon': 'fa-user-circle', 'type': 'personal'}
    ]

    # Добавляем "Мои гроурепорты" для всех аутентифицированных пользователей
    try:
        my_growlogs_url = reverse('growlogs:my_logs')
    except:
        my_growlogs_url = '#'  # Fallback

    items.append(
        {'title': 'Мои гроурепорты', 'url': my_growlogs_url, 'icon': 'fa-seedling', 'type': 'user_activity'}
    )

    # Добавляем специфичные для роли 'user' пункты (заказы, галерея)
    if user.role == 'user':
        try:
            my_orders_url = reverse('store:my_orders')
        except:
            my_orders_url = '#' # Fallback if URL doesn't exist
        try:
            my_gallery_url = reverse('gallery:my_photos')
        except:
            my_gallery_url = '#' # Fallback

        items.extend([
            {'title': 'Мои заказы', 'url': my_orders_url, 'icon': 'fa-shopping-bag', 'type': 'user_activity'},
            {'title': 'Моя галерея', 'url': my_gallery_url, 'icon': 'fa-images', 'type': 'user_activity'},
        ])

    return items

def get_admin_navigation_items(user):
    """Возвращает административные пункты меню в зависимости от роли"""
    # Убедимся, что user аутентифицирован и имеет атрибут role
    if not user.is_authenticated or not hasattr(user, 'role'):
        return []

    items = []

    if user.role == 'owner':
        items.extend([
            {'title': 'Админка платформы', 'url': '/owner_admin/', 'icon': 'fa-crown', 'type': 'admin_primary'},
            {'title': 'Админка модераторов', 'url': '/moderator_admin/', 'icon': 'fa-shield-alt', 'type': 'admin_secondary'},
        ])
    elif user.role == 'admin':
        items.append(
            {'title': 'Админка модерации', 'url': '/moderator_admin/', 'icon': 'fa-shield-alt', 'type': 'admin_primary'}
        )
    elif user.role == 'store_owner':
        items.extend([
            {'title': 'Панель владельца', 'url': '/store_owner/', 'icon': 'fa-store', 'type': 'admin_primary'},
            {'title': 'Админка магазина', 'url': '/store_admin_site/', 'icon': 'fa-cash-register', 'type': 'admin_secondary'},
        ])
    elif user.role == 'store_admin':
        items.append(
            {'title': 'Админка магазина', 'url': '/store_admin_site/', 'icon': 'fa-cash-register', 'type': 'admin_primary'}
        )

    return items

def get_role_badge(user):
    """Возвращает данные для отображения бейджа роли"""
    # Убедимся, что user аутентифицирован и имеет атрибут role
    if not user.is_authenticated or not hasattr(user, 'role'):
        return None

    badges = {
        'owner': {'text': '👑 Владелец', 'class': 'bg-danger text-white', 'priority': 5},
        'admin': {'text': '🎭 Модератор', 'class': 'bg-warning text-dark', 'priority': 4},
        'store_owner': {'text': '🏪 Владелец магазина', 'class': 'bg-success text-white', 'priority': 3},
        'store_admin': {'text': '📦 Админ магазина', 'class': 'bg-info text-white', 'priority': 2},
        'user': None  # Обычные пользователи без бейджа
    }
    return badges.get(user.role)

def get_breadcrumb_context(request):
    """Определяет контекст для хлебных крошек на основе текущего URL"""
    path = request.path
    breadcrumbs = []

    # Определяем базовые хлебные крошки по пути
    if path.startswith('/users/cabinet/'):
        breadcrumbs = [{'title': 'Личный кабинет', 'url': reverse('users:profile')}]

        if path.endswith('/edit/'):
            breadcrumbs.append({'title': 'Редактирование профиля', 'url': None})
        elif path.endswith('/password/'):
            breadcrumbs.append({'title': 'Смена пароля', 'url': None})

    elif path.startswith('/owner_admin/'):
        breadcrumbs = [{'title': 'Админка платформы', 'url': '/owner_admin/'}]

    elif path.startswith('/moderator_admin/'):
        breadcrumbs = [{'title': 'Админка модерации', 'url': '/moderator_admin/'}]

    elif path.startswith('/store_owner/'):
        breadcrumbs = [{'title': 'Админка владельца магазина', 'url': '/store_owner/'}]

    elif path.startswith('/store_admin_site/'):
        breadcrumbs = [{'title': 'Админка магазина', 'url': '/store_admin_site/'}]

    return breadcrumbs
