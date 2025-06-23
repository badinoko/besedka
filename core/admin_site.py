from django.contrib.admin import AdminSite
from django.urls import reverse, reverse_lazy, path
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.conf import settings # Для LOGIN_URL
from django.contrib.auth.views import redirect_to_login # Для корректного редиректа
from users.views_owner_platform import ManageStoreOwnerView

class BaseCustomAdminSite(AdminSite):
    # Общие настройки для всех кастомных админок
    # Отключаем стандартный навигационный сайдбар Django Admin,
    # чтобы полностью убрать дублирующееся меню и освободить место
    # (панель навигации Беседки уже присутствует в шапке через templates/admin/base_site.html)
    enable_nav_sidebar: bool = False
    login_form = None # Используем форму от allauth
    # Убираем login_url чтобы использовать стандартную логику Django Admin

    def login(self, request, extra_context=None):
        """
        Кастомная логика логина для админок.
        Если пользователь уже авторизован, но не имеет прав - показываем ошибку.
        Если не авторизован - перенаправляем на allauth.
        """
        if request.user.is_authenticated:
            if not self.has_permission(request):
                from django.contrib import messages
                from django.shortcuts import render
                messages.error(request, 'У вас нет прав доступа к этой административной панели.')
                return render(request, 'admin/login.html', {
                    'title': 'Доступ запрещен',
                    'error_message': 'У вас нет прав доступа к этой административной панели.',
                    **self.each_context(request),
                })
            else:
                # Пользователь авторизован и имеет права - перенаправляем на главную админки
                return redirect(f'/{self.name}/')
        else:
            # Пользователь не авторизован - перенаправляем на allauth
            return redirect_to_login(
                request.get_full_path(),
                settings.LOGIN_URL
            )

class StoreOwnerSite(BaseCustomAdminSite):
    """
    Кастомный AdminSite для ВЛАДЕЛЬЦА магазина.
    Полный доступ ко всем функциям управления магазином.
    """
    site_header = _("Владелец магазина")
    site_title = _("Панель владельца")
    index_title = _("Панель владельца магазина")
    index_template = "store_owner/index.html"
    site_url = "/"
    app_name = 'store_owner_admin'
    # login_url и login_form наследуются от BaseCustomAdminSite

    def __init__(self, name='store_owner_admin'):
        super().__init__(name)
        self.name = name

    def has_permission(self, request):
        """
        ТОЛЬКО владелец магазина может получить доступ.
        Владелец платформы НЕ имеет доступа к админке магазина.
        """
        return (request.user.is_active and
                request.user.is_staff and
                request.user.role == 'store_owner')

    def index(self, request, extra_context=None):
        """
        Кастомная главная страница с кнопкой быстрого перехода в операционную админку
        """
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        User = get_user_model()

        # Получаем статистику
        store_admin_count = User.objects.filter(role='store_admin', is_active=True).count()

        sections = [
            {
                'title': '👥 Управление персоналом',
                'description': 'Назначение и управление администраторами магазина',
                'items': [
                    {
                        'title': 'Администраторы магазина',
                        'description': f'Управление сотрудниками ({store_admin_count} активных)',
                        'url': reverse(f'{self.name}:users_user_changelist'),
                        'icon': '👨‍💼'
                    },
                ]
            },
            {
                'title': '⚙️ Настройки магазина',
                'description': 'Конфигурация и управление параметрами магазина',
                'items': [
                    {
                        'title': 'Основные настройки',
                        'description': 'Настройки магазина, контактная информация',
                        'url': reverse(f'{self.name}:magicbeans_store_storesettings_changelist'),
                        'icon': '⚙️'
                    },
                    {
                        'title': 'Способы оплаты',
                        'description': 'Управление методами оплаты',
                        'url': reverse(f'{self.name}:magicbeans_store_paymentmethod_changelist'),
                        'icon': '💳'
                    },
                    {
                        'title': 'Способы доставки',
                        'description': 'Настройка доставки и тарифов',
                        'url': reverse(f'{self.name}:magicbeans_store_shippingmethod_changelist'),
                        'icon': '📦'
                    },
                ]
            },
            {
                'title': '🎯 Маркетинг и акции',
                'description': 'Управление промо-акциями и купонами',
                'items': [
                    {
                        'title': 'Промо-акции',
                        'description': 'Создание и управление акциями',
                        'url': reverse(f'{self.name}:magicbeans_store_promotion_changelist'),
                        'icon': '🎁'
                    },
                    {
                        'title': 'Купоны',
                        'description': 'Система скидочных купонов',
                        'url': reverse(f'{self.name}:magicbeans_store_coupon_changelist'),
                        'icon': '🎫'
                    },
                ]
            },
            {
                'title': '📊 Отчёты и аналитика',
                'description': 'Анализ продаж и складских остатков',
                'items': [
                    {
                        'title': 'Отчёты по продажам',
                        'description': 'Анализ выручки и продаж',
                        'url': reverse(f'{self.name}:magicbeans_store_salesreport_changelist'),
                        'icon': '💰'
                    },
                    {
                        'title': 'Складские отчёты',
                        'description': 'Остатки и движения товаров',
                        'url': reverse(f'{self.name}:magicbeans_store_inventoryreport_changelist'),
                        'icon': '📈'
                    },
                ]
            },
        ]

        context = {
            'title': self.index_title,
            'user_role_display': '🏪 Владелец магазина',
            'available_sections': sections,
            'store_admin_count': store_admin_count,
            'quick_access_url': 'http://127.0.0.1:8000/admin/login/',  # Исправленная ссылка
            **self.each_context(request),
        }

        if extra_context:
            context.update(extra_context)

        return TemplateResponse(request, self.index_template, context)

class StoreAdminSite(BaseCustomAdminSite):
    """
    Кастомный AdminSite для АДМИНИСТРАТОРА магазина.
    Ограниченный доступ - помощник владельца магазина.
    """
    site_header = _("Администратор магазина")
    site_title = _("Панель администратора")
    index_title = _("Панель администратора магазина")
    index_template = "store_admin/index.html"
    site_url = "/"
    app_name = 'store_admin_site'
    # login_url и login_form наследуются от BaseCustomAdminSite

    def __init__(self, name='store_admin_site'):
        super().__init__(name)
        self.name = name

    def has_permission(self, request):
        """
        ТОЛЬКО администратор магазина И владелец магазина могут получить доступ.
        Владелец платформы НЕ имеет доступа к админке магазина.
        """
        return (request.user.is_active and
                request.user.is_staff and
                request.user.role in ('store_admin', 'store_owner'))

    def index(self, request, extra_context=None):
        """
        Кастомизированная главная страница для администратора магазина
        """
        extra_context = extra_context or {}
        user = request.user

        # Определяем доступные разделы (ограниченные)
        available_sections = []

        # 1. СКЛАД - ограниченный доступ (только soft delete)
        available_sections.append({
            'id': 'inventory',
            'title': _("📦 Склад и Товары"),
            'description': _("Управление товарами (без возможности удаления)"),
            'items': [
                {
                    'title': _("Сидбанки"),
                    'url': f'/{self.name}/magicbeans_store/seedbank/',
                    'add_url': f'/{self.name}/magicbeans_store/seedbank/add/',
                    'icon': '🌱',
                    'description': _("Добавление и редактирование сидбанков")
                },
                {
                    'title': _("Сорта"),
                    'url': f'/{self.name}/magicbeans_store/strain/',
                    'add_url': f'/{self.name}/magicbeans_store/strain/add/',
                    'icon': '🌿',
                    'description': _("Добавление и редактирование сортов")
                },
                {
                    'title': _("Товары на складе"),
                    'url': f'/{self.name}/magicbeans_store/stockitem/',
                    'add_url': f'/{self.name}/magicbeans_store/stockitem/add/',
                    'icon': '📋',
                    'description': _("Поступления и списания товаров")
                },
            ]
        })

        # 2. ЗАКАЗЫ - только просмотр и обработка
        available_sections.append({
            'id': 'orders',
            'title': _("🛒 Заказы и обработка"),
            'description': _("Обработка заказов и управление статусами"),
            'items': [
                {
                    'title': _("Заказы"),
                    'url': f'/{self.name}/magicbeans_store/order/',
                    'icon': '📦',
                    'description': _("Просмотр и обработка заказов")
                },
                {
                    'title': _("Статусы заказов"),
                    'url': f'/{self.name}/magicbeans_store/orderstatus/',
                    'add_url': f'/{self.name}/magicbeans_store/orderstatus/add/',
                    'icon': '📋',
                    'description': _("Управление статусами заказов")
                },
            ]
        })

        # 3. ПРОМОАКЦИИ И СКИДКИ - создание и редактирование
        available_sections.append({
            'id': 'promotions',
            'title': _("🎯 Промоакции и скидки"),
            'description': _("Создание акций для привлечения клиентов"),
            'items': [
                {
                    'title': _("Промоакции"),
                    'url': f'/{self.name}/magicbeans_store/promotion/',
                    'add_url': f'/{self.name}/magicbeans_store/promotion/add/',
                    'icon': '🎯',
                    'description': _("Создание и управление промоакциями")
                },
                {
                    'title': _("Купоны"),
                    'url': f'/{self.name}/magicbeans_store/coupon/',
                    'add_url': f'/{self.name}/magicbeans_store/coupon/add/',
                    'icon': '🎫',
                    'description': _("Создание промокодов и купонов")
                },
            ]
        })

        # 4. НАСТРОЙКИ ДОСТАВКИ И ОПЛАТЫ - редактирование методов
        available_sections.append({
            'id': 'settings',
            'title': _("⚙️ Настройки доставки и оплаты"),
            'description': _("Управление способами доставки и оплаты"),
            'items': [
                {
                    'title': _("Способы доставки"),
                    'url': f'/{self.name}/magicbeans_store/shippingmethod/',
                    'add_url': f'/{self.name}/magicbeans_store/shippingmethod/add/',
                    'icon': '🚚',
                    'description': _("Редактирование способов доставки")
                },
                {
                    'title': _("Способы оплаты"),
                    'url': f'/{self.name}/magicbeans_store/paymentmethod/',
                    'add_url': f'/{self.name}/magicbeans_store/paymentmethod/add/',
                    'icon': '💳',
                    'description': _("Редактирование способов оплаты")
                },
            ]
        })

        extra_context.update({
            'available_sections': available_sections,
            'user_role': user.role,
            'user_role_display': user.get_role_display(),
            'title': _("Панель администратора магазина"),
            'admin_type': 'store_admin',
            'admin_type_display': _("Администратор магазина"),
        })

        return super().index(request, extra_context)

class OwnerAdminSite(BaseCustomAdminSite):
    """
    Кастомный AdminSite для владельца платформы "Беседка".
    Отображает управление платформой (БЕЗ деталей магазина).
    """
    site_header = _("Беседка - Управление платформой")
    site_title = _("Беседка - Административная панель")
    index_title = _("Панель управления")
    index_template = "owner_admin/index.html"
    site_url = "/"
    app_name = 'owner_admin'
    # login_url и login_form наследуются от BaseCustomAdminSite

    def __init__(self, name='owner_admin'):
        super().__init__(name)
        self.name = name

    def has_permission(self, request):
        """
        ТОЛЬКО владелец платформы может получить доступ.
        """
        return (request.user.is_active and
                request.user.is_staff and
                request.user.role == 'owner')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "manage-store-owner/",
                self.admin_view(ManageStoreOwnerView.as_view()),
                name="manage_store_owner",
            ),
            # Сюда можно будет добавить URL для деактивации, если он будет отдельным
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        """
        Кастомизированная главная страница админки владельца платформы с ролевым доступом
        """
        extra_context = extra_context or {}
        user = request.user

        # Определяем доступные разделы на основе роли пользователя
        available_sections = []

        # 1. УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ И РОЛЯМИ - только owner
        if user.role == 'owner':
            available_sections.append({
                'id': 'user_management',
                'title': _("👥 Управление пользователями и ролями"),
                'description': _("Назначение ролей пользователям через простой интерфейс"),
                'items': [
                    {
                        'title': _("Все пользователи"),
                        'url': f'/{self.name}/users/user/',
                        'add_url': f'/{self.name}/users/user/add/',
                        'icon': '👤',
                        'description': _("Назначение ролей: moderator, store_owner, store_admin")
                    },
                    {
                        'title': _("Управление Владельцем Магазина"),
                        'url': reverse_lazy(f'{self.name}:manage_store_owner'),
                        'icon': '🧑‍💼',
                        'description': _("Назначение и отзыв Владельца Магазина")
                    },
                ]
            })

        # 2. НАСТРОЙКИ ПЛАТФОРМЫ И МАГАЗИНА - только owner
        if user.role == 'owner':
            available_sections.append({
                'id': 'platform_settings',
                'title': _("⚙️ Настройки платформы и магазина"),
                'description': _("Полное управление платформой Беседка и магазином"),
                'items': [
                    {
                        'title': _("🎭 Перейти в админку модератора"),
                        'url': '/moderator_admin/',
                        'icon': '🚨',
                        'description': _("Модерация контента как ваш заместитель")
                    },
                    {
                        'title': _("Логи действий"),
                        'url': f'/{self.name}/core/actionlog/',
                        'icon': '📋',
                        'description': _("Журнал действий пользователей")
                    },
                ]
            })

        extra_context.update({
            'available_sections': available_sections,
            'user_role': user.role,
            'user_role_display': user.get_role_display(),
            'title': self.index_title,
            'admin_type': 'owner_admin',
            'admin_type_display': _("Админка владельца платформы"),
        })

        return super().index(request, extra_context)

    def each_context(self, request):
        context = super().each_context(request)
        context.update({
            'admin_type': 'owner_admin',
            'admin_type_display': _("Админка владельца платформы"),
        })
        return context

class ModeratorAdminSite(BaseCustomAdminSite):
    """
    Кастомный AdminSite для администраторов платформы (модераторов).
    Отображает инструменты модерации без доступа к настройкам.
    """
    site_header = _("Беседка - Модерация")
    site_title = _("Беседка - Панель модератора")
    index_title = _("Панель модерации")
    index_template = "moderator_admin/index.html"
    site_url = "/"
    app_name = 'moderator_admin'
    # login_url и login_form наследуются от BaseCustomAdminSite

    def __init__(self, name='moderator_admin'):
        super().__init__(name)
        self.name = name

    def has_permission(self, request):
        """
        Администраторы платформы (модераторы) И владелец платформы могут получить доступ.
        Владелец может модерировать как его заместитель.
        """
        return (request.user.is_active and
                request.user.is_staff and
                request.user.role in ('moderator', 'owner'))

    def index(self, request, extra_context=None):
        """
        Простая панель модерации с быстрыми действиями
        """
        extra_context = extra_context or {}
        user = request.user

        # Быстрые действия модерации
        available_sections = []

        if user.role in ('moderator', 'owner'):
            available_sections.append({
                'id': 'quick_moderation',
                'title': _("🚨 Быстрая модерация"),
                'description': _("Инструменты для быстрого реагирования на нарушения"),
                'items': [
                    {
                        'title': _("💬 Модерация чата"),
                        'url': f'/{self.name}/chat/chatmessage/',
                        'icon': '💬',
                        'description': _("Просмотр и удаление сообщений чата")
                    },
                    {
                        'title': _("🖼️ Модерация галереи"),
                        'url': f'/{self.name}/gallery/photo/',
                        'icon': '🖼️',
                        'description': _("Просмотр и удаление фотографий")
                    },
                    {
                        'title': _("📝 Модерация grow logs"),
                        'url': f'/{self.name}/growlogs/growlog/',
                        'icon': '📝',
                        'description': _("Просмотр и модерация дневников")
                    },
                ]
            })

            available_sections.append({
                'id': 'user_actions',
                'title': _("👤 Действия с пользователями"),
                'description': _("Баны, муты и ограничения доступа"),
                'items': [
                    {
                        'title': _("🚫 Выдать бан"),
                        'url': f'/{self.name}/users/banrecord/add/',
                        'icon': '🚫',
                        'description': _("Быстро забанить пользователя")
                    },
                    {
                        'title': _("📋 Мои баны"),
                        'url': f'/{self.name}/users/banrecord/',
                        'icon': '📋',
                        'description': _("Список всех банов на платформе")
                    },
                ]
            })

        extra_context.update({
            'available_sections': available_sections,
            'user_role': user.role,
            'user_role_display': user.get_role_display(),
            'title': _("Панель модерации"),
            'admin_type': 'moderator_admin',
            'admin_type_display': _("Админка модератора"),
        })

        return super().index(request, extra_context)

# Создаем экземпляры кастомных админок
store_owner_site = StoreOwnerSite(name='store_owner_admin')
store_admin_site = StoreAdminSite(name='store_admin_site')
owner_admin_site = OwnerAdminSite(name='owner_admin')
moderator_admin_site = ModeratorAdminSite(name='moderator_admin')
