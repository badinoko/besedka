from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from django.views.generic import TemplateView
from magicbeans.store.admin.site import store_admin_site

urlpatterns = [
    # Главная страница
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),

    # Django Admin - используем кастомный административный сайт
    path(settings.ADMIN_URL, store_admin_site.urls),

    # User management
    path("users/", include("magicbeans.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),

    # Your stuff: custom urls includes go here

    # Media files
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
