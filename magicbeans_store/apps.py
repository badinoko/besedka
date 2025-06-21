from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MagicbeansStoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'magicbeans_store'
    verbose_name = _("Магазин")

    def ready(self):
        """
        Выполняется при запуске приложения
        """
        try:
            # Импортируем сигналы
            from . import signals  # noqa: F401

            # Импортируем admin.py для регистрации моделей в кастомных админках
            from . import admin  # noqa: F401

        except ImportError:
            # В случае ошибок импорта (например, при миграциях) просто пропускаем
            pass
