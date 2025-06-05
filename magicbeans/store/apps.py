from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StoreConfig(AppConfig):
    name = "magicbeans.store"
    verbose_name = _("Store")

    def ready(self):
        """
        Регистрируем модели в админке магазина после загрузки всех приложений.
        """
        # Импортируем сигналы
        import magicbeans.store.signals  # noqa: F401

        # Регистрируем модели в админке магазина
        from core.admin_site import store_admin_site
        from magicbeans.store.models import (
            Administrator, SeedBank, Strain, StrainImage,
            StockItem, StockMovement, Order, OrderItem
        )
        from magicbeans.store.admin.administrators import AdministratorAdmin
        from magicbeans.store.admin.stock_admin import StockItemAdmin, StockMovementAdmin

        store_admin_site.register(Administrator, AdministratorAdmin)
        store_admin_site.register(SeedBank)
        store_admin_site.register(Strain)
        store_admin_site.register(StrainImage)
        store_admin_site.register(StockItem, StockItemAdmin)
        store_admin_site.register(StockMovement, StockMovementAdmin)
        store_admin_site.register(Order)
        store_admin_site.register(OrderItem)