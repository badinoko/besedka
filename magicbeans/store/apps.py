from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import contextlib
from django.contrib import admin


class StoreConfig(AppConfig):
    name = "magicbeans.store"
    verbose_name = _("Store")

    def ready(self):
        # Импортируем сигналы
        with contextlib.suppress(ImportError):
            import magicbeans.store.signals  # noqa: F401

        # Регистрируем кастомный административный сайт
        with contextlib.suppress(ImportError):
            from django.contrib import admin as django_admin
            from magicbeans.store.admin.site import StoreAdminSite

            if not isinstance(django_admin.site, StoreAdminSite):
                admin.site = StoreAdminSite(name="admin")
