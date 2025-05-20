from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group, User

from .admin_views import statistics_view
from .administrators import AdministratorAdmin
from .stock_admin import StockItemAdmin, StockMovementAdmin
from magicbeans.store.models import (
    Administrator, SeedBank, Strain, StrainImage, 
    StockItem, StockMovement, Order, OrderItem, ActionLog
)


class StoreAdminSite(admin.AdminSite):
    """
    Класс для расширения функционала административной панели
    """
    site_header = _("Magic Beans - Администрирование")
    site_title = _("Magic Beans - Администрирование")
    index_title = _("Панель управления магазином")

    def get_app_list(self, request):
        """
        Переопределяем метод получения списка приложений для добавления
        дополнительных пунктов меню в зависимости от прав пользователя
        """
        app_list = super().get_app_list(request)

        # Добавляем управление доступом только для супер-пользователей и владельцев
        if request.user.is_superuser or request.user.groups.filter(name="Владельцы").exists():
            app_list.append({
                "name": _("Управление магазином"),
                "app_label": "store_management",
                "models": [
                    {
                        "name": _("Статистика продаж"),
                        "object_name": "Statistics",
                        "admin_url": "/admin/statistics/",
                        "view_only": True,
                    },
                    {
                        "name": _("Импорт/Экспорт товаров"),
                        "object_name": "ImportExport",
                        "admin_url": "/admin/stock/import-export/",
                        "view_only": True,
                    }
                ]
            })

        return app_list

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "statistics/",
                self.admin_view(statistics_view),
                name="store_statistics"
            ),
            path(
                "stock/import-export/",
                self.admin_view(self.import_export_view),
                name="stock_import_export"
            ),
        ]
        return custom_urls + urls

    def import_export_view(self, request):
        """
        Представление для импорта/экспорта товаров
        """
        context = {
            **self.each_context(request),
            "title": _("Импорт/Экспорт товаров"),
        }
        return TemplateResponse(request, "admin/store/import_export.html", context)


# Инициализация административного сайта
store_admin_site = StoreAdminSite(name="store_admin")

# Регистрация специализированных административных моделей
store_admin_site.register(Administrator, AdministratorAdmin)
store_admin_site.register(StockItem, StockItemAdmin)
store_admin_site.register(StockMovement, StockMovementAdmin)

# Регистрация остальных моделей с базовым административным интерфейсом
store_admin_site.register(SeedBank)
store_admin_site.register(Strain)
store_admin_site.register(StrainImage)
store_admin_site.register(Order)
store_admin_site.register(OrderItem)
store_admin_site.register(ActionLog)
