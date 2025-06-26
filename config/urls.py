from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include, re_path
from django.views.generic import TemplateView, RedirectView
from core.admin_site import store_owner_site, store_admin_site, owner_admin_site, moderator_admin_site
from core.views import admin_selector, admin_redirect
from core import ajax_views as core_ajax
from oauth2_provider import urls as oauth2_urls

urlpatterns = [
    # Главная страница (плейсхолдер). Позднее будет заменена полноценным представлением.
    path("", TemplateView.as_view(template_name="home/home_placeholder.html"), name="home"),

    # Новостная лента
    path("news/", include("news.urls", namespace="news")),

    # Статические страницы
    path("pages/", include(([
        path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    ], "pages"))),

    # Тестовая страница навигации
    path("test-navigation/", TemplateView.as_view(template_name="test_navigation.html"), name="test_navigation"),

    # Главная точка входа для админки - автоматическое перенаправление по ролям
    path("admin/", admin_redirect, name="admin_redirect"),

    # Кастомные админки
    path("store_owner/", store_owner_site.urls),  # Панель владельца магазина
    path("store_admin_site/", store_admin_site.urls),  # Панель администратора магазина
    path("owner_admin/", owner_admin_site.urls),  # Админка владельца платформы
    path("moderator_admin/", moderator_admin_site.urls),  # Админка модератора

    # Селектор админок (если нужно вручную выбрать)
    path("admin-selector/", admin_selector, name="admin_selector"),

    # User management
    path("users/", include("users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),

    # OAuth2 Provider endpoints (остальные эндпоинты)
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),

    # Store
    path("store/", include("magicbeans_store.urls", namespace="store")),

    # Grow logs
    path("growlogs/", include("growlogs.urls", namespace="growlogs")),

    # Gallery
    path("gallery/", include("gallery.urls", namespace="gallery")),

    # Core app urls (maintenance page, etc.)
    path("internal/core/", include("core.urls", namespace="core")),

    # Chat - ru-RU.dj-chat_1.0
    path("chat/", include("chat.urls", namespace="chat")),

    # API urls
    path("api/", include("config.api_router")),

    path('ajax/comments/', core_ajax.load_comments, name='ajax_load_comments'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
