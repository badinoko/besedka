from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-key-for-dev",
)
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "testserver"]

# СТАРЫЙ MIDDLEWARE ОТ ROCKET.CHAT ИНТЕГРАЦИИ - УДАЛЕН
# MIDDLEWARE = [
#     "core.middleware.RocketChatProxyMiddleware",  # 🚀 ПРОКСИРОВАНИЕ ROCKET.CHAT ФАЙЛОВ
# ] + MIDDLEWARE

# FILE UPLOAD SETTINGS
# ------------------------------------------------------------------------------
# Увеличиваем лимиты для загрузки файлов
FILE_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# CHANNELS
# ------------------------------------------------------------------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)

# django-debug-toolbar
# ------------------------------------------------------------------------------
# Временно отключаем Debug Toolbar для проверки CSS
# INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# DEBUG_TOOLBAR_CONFIG = {
#     "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
#     "SHOW_TEMPLATE_CONTEXT": True,
# }
# INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
