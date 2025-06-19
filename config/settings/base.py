from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables
env = environ.Env()
env.read_env(str(BASE_DIR / ".env"))

# Определяем REDIS_URL из переменных окружения
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

# Application definition
DJANGO_APPS = [
    # Кастомные темы для админки
    "admin_interface",
    "colorfield",
    # Стандартные приложения Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_extensions",
    # "debug_toolbar",  # Django Debug Toolbar - ОТКЛЮЧЕН для продакшн-готовности
    "import_export",  # Django Import-Export
    "guardian",       # Django Guardian для тонких прав доступа
    "channels",       # Django Channels для WebSocket (чат)
    "oauth2_provider",  # Django OAuth Toolkit для Rocket.Chat SSO
    # "django_private_chat2.apps.DjangoPrivateChat2Config",  # Готовый чат - временно отключен
    # "admin_charts",   # Django Admin Charts - временно отключаем пока не решим проблему
]

LOCAL_APPS = [
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "pages.apps.PagesConfig",
    "magicbeans_store.apps.MagicbeansStoreConfig",
    "growlogs.apps.GrowlogsConfig",
    "gallery.apps.GalleryConfig",
    "chat.apps.ChatConfig",  # 🚀 Новый чат сообщества (ru-RU.dj-chat_1.0)
    "api.apps.ApiConfig",
    "news.apps.NewsConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# X_FRAME_OPTIONS для admin_interface
X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # "debug_toolbar.middleware.DebugToolbarMiddleware",  # Django Debug Toolbar Middleware - ОТКЛЮЧЕН
    "core.middleware.MaintenanceModeMiddleware", # <--- Режим технического обслуживания
    "core.middleware.AdminRedirectMiddleware",  # 🚨 ПРИНУДИТЕЛЬНОЕ ПЕРЕНАПРАВЛЕНИЕ АДМИНОК
    "core.middleware.ForcePasswordChangeMiddleware",  # <--- ДОБАВЛЕНО
    "core.middleware.RequestUserMiddleware",  # Middleware for tracking request user
    "core.middleware.ActionLogMiddleware",  # Middleware for logging user actions
    "oauth2_provider.middleware.OAuth2TokenMiddleware",  # OAuth2 для Rocket.Chat SSO
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "core.middleware.DisableCSRFForOAuth",  # Отключаем CSRF для OAuth запросов
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.navigation_context",  # 🚀 Unified navigation context
                "magicbeans_store.context_processors.cart_item_count",
            ],
            "builtins": [
                "django.templatetags.i18n",
                "core.templatetags.translate_alias",  # 👈 Alias tag library to support `{% translate %}`
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres:///besedka")
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = str(BASE_DIR / "staticfiles")
STATICFILES_DIRS = [str(BASE_DIR / "static")]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR / "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "news:home"
LOGOUT_REDIRECT_URL = "news:home"
LOGIN_URL = "account_login"

# AllAuth Configuration
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"

# Разрешаем мгновенный логаут по GET (важно для автотестов и UX)
ACCOUNT_LOGOUT_ON_GET = True

# Django Guardian
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Django Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

# Sites
SITE_ID = 1

# Telegram Login Widget settings
TELEGRAM_BOT_NAME = env("TELEGRAM_BOT_NAME", default="")
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")

# Crispy Forms Settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# DJANGO ADMIN ALLAUTH
# ------------------------------------------------------------------------------
DJANGO_ADMIN_FORCE_ALLAUTH = False

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL. Default to "admin".
ADMIN_URL = "admin/"

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'core.middleware': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Django Debug Toolbar
INTERNAL_IPS = ["127.0.0.1"]

# Django REST Framework
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# JWT Settings
# ------------------------------------------------------------------------------
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
}

# drf-spectacular Settings
# ------------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    'TITLE': 'Беседка API',
            'DESCRIPTION': 'API для интеграции с Telegram-ботом магазина',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
}

# API Settings
# ------------------------------------------------------------------------------
API_VERSION = 'v1'
API_TELEGRAM_BOT_TOKEN = env("API_TELEGRAM_BOT_TOKEN", default="")  # Отдельный токен для API

# OAuth2 Provider (Rocket.Chat SSO)
# ------------------------------------------------------------------------------
OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 36000,
    "AUTHORIZATION_CODE_EXPIRE_SECONDS": 300,
    "OAUTH2_VALIDATOR_CLASS": "oauth2_provider.oauth2_validators.OAuth2Validator",
    "SCOPES": {
        "rocketchat": "Access Rocket.Chat via OAuth2",
    },
}

# Rocket.Chat Security Settings
# ------------------------------------------------------------------------------
# CSP настройки для iframe Rocket.Chat
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Разрешаем iframe для Rocket.Chat

# CSRF для OAuth редиректов из Rocket.Chat
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
]

# Отключаем проверку CSRF referer для локальной разработки
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# В production включить HSTS
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CSP для Rocket.Chat iframe
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'"]  # 'unsafe-inline' для allauth
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
CSP_FONT_SRC = ["'self'", "https://fonts.gstatic.com"]
CSP_IMG_SRC = ["'self'", "data:"]
CSP_FRAME_SRC = ["'self'", "http://127.0.0.1:3000"]  # Rocket.Chat iframe
CSP_CONNECT_SRC = ["'self'", "ws://127.0.0.1:8001", "wss://127.0.0.1:8001"]  # WebSocket для Daphne

# Rocket.Chat Environment Variables
# ------------------------------------------------------------------------------
ROCKETCHAT_API_URL = env("ROCKETCHAT_API_URL", default="http://127.0.0.1:3000")
ROCKETCHAT_ADMIN_TOKEN = env("ROCKETCHAT_ADMIN_TOKEN", default="")
ROCKETCHAT_ADMIN_USER_ID = env("ROCKETCHAT_ADMIN_USER_ID", default="")

# Django Allauth
# ------------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
]

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 after confirming the site works
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True)

# Content Security Policy
CSP_FRAME_SRC = ["'self'", "http://127.0.0.1:3000"]  # Rocket.Chat iframe
CSP_DEFAULT_SRC = ["'self'"]

# Rocket.Chat
ROCKETCHAT_API_URL = env("ROCKETCHAT_API_URL", default="http://127.0.0.1:3000")

# Your stuff...
# ------------------------------------------------------------------------------
