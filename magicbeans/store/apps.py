from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import contextlib


class StoreConfig(AppConfig):
    name = "magicbeans.store"
    verbose_name = _("Store")

    def ready(self):
        with contextlib.suppress(ImportError):
            import magicbeans.store.signals  # noqa: F401
