from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import contextlib
from django.contrib import admin


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'magicbeans.store'
    verbose_name = _('Магазин')

    def ready(self):
        # Импортируем сигналы
        with contextlib.suppress(ImportError):
            import magicbeans.store.signals  # noqa: F401

        # Регистрируем кастомный административный сайт
        with contextlib.suppress(ImportError):
            from django.contrib import admin as django_admin
            from magicbeans.store.admin.site import store_admin_site

            # Заменяем стандартный административный сайт на наш кастомный
            if not isinstance(django_admin.site, type(store_admin_site)):
                admin.site = store_admin_site
