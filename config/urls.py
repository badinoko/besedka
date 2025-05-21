from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # Главная страница
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),

    # Django Admin
    path("admin/", admin.site.urls),

    # User management
    path("users/", include("users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),

    # Store
    path("store/", include("magicbeans_store.urls", namespace="store")),
    
    # Grow logs
    path("growlogs/", include("growlogs.urls", namespace="growlogs")),
    
    # Gallery
    path("gallery/", include("gallery.urls", namespace="gallery")),
    
    # Chat
    path("chat/", include("chat.urls", namespace="chat")),
    
    # API urls
    path("api/", include("config.api_router")),

    # Your stuff: custom urls includes go here

    # Media files
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
