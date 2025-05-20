from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

# from .admin_views import statistics_view  # Закомментировано, т.к. файл не существует
from .administrators import AdministratorAdmin
from .stock_admin import StockItemAdmin, StockMovementAdmin
from magicbeans.store.models import (
    Administrator, SeedBank, Strain, StrainImage, 
    StockItem, StockMovement, Order, OrderItem, ActionLog
)
from magicbeans.users.admin import CustomUserAdmin

User = get_user_model()


class StoreAdminSite(admin.AdminSite):
    """
    Класс для расширения функционала административной панели
    """
    site_header = _("Magic Beans - Администрирование")
    site_title = _("Magic Beans - Администрирование")
    index_title = _("Панель управления магазином")

    def get_app_list(self, request):
        """
        Реструктуризация админки в три логических раздела:
        1. СКЛАД - управление товарами и остатками
        2. АДМИНИСТРАТОРЫ - управление пользователями
        3. СТАТИСТИКА - аналитика и отчеты
        """
        # Получаем стандартный словарь приложений
        app_dict = self._build_app_dict(request)
        
        # Создаем полностью новый список приложений (очищаем старый)
        new_app_list = []
        
        # 1. СКЛАД
        warehouse_models = []
        # Добавляем модели складских товаров
        warehouse_models_list = ['SeedBank', 'Strain', 'StrainImage', 'StockItem', 'StockMovement', 'Order', 'OrderItem']
        
        for app_label, app_config in app_dict.items():
            for model in app_config['models']:
                if model['object_name'] in warehouse_models_list:
                    warehouse_models.append(model)
                    
        if warehouse_models:
            new_app_list.append({
                "name": _("СКЛАД"),
                "app_label": "warehouse",
                "app_url": "#",
                "has_module_perms": True,
                "models": warehouse_models
            })
            
        # 2. АДМИНИСТРАТОРЫ
        admin_models = []
        # Добавляем модели пользователей и групп
        for app_label, app_config in app_dict.items():
            for model in app_config['models']:
                if model['object_name'] in ['User', 'Group', 'Administrator', 'ActionLog']:
                    admin_models.append(model)
                    
        if admin_models:
            new_app_list.append({
                "name": _("АДМИНИСТРАТОРЫ"),
                "app_label": "administrators",
                "app_url": "#",
                "has_module_perms": True,
                "models": admin_models
            })
            
        # 3. СТАТИСТИКА
        # Добавляем статистику только для супер-пользователей и владельцев
        if request.user.is_superuser or request.user.groups.filter(name="Владельцы").exists():
            new_app_list.append({
                "name": _("СТАТИСТИКА"),
                "app_label": "statistics",
                "app_url": "#",
                "has_module_perms": True,
                "models": [
                    {
                        "name": _("Статистика продаж"),
                        "object_name": "SalesStatistics",
                        "admin_url": "/admin/statistics/sales/",
                        "view_only": True,
                        "perms": {"view": True}
                    },
                    {
                        "name": _("Импорт/Экспорт товаров"),
                        "object_name": "ImportExport",
                        "admin_url": "/admin/stock/import-export/",
                        "view_only": True,
                        "perms": {"view": True}
                    }
                ]
            })
            
        return new_app_list

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "statistics/sales/",
                self.admin_view(self.statistics_view),
                name="store_statistics"
            ),
            path(
                "stock/import-export/",
                self.admin_view(self.import_export_view),
                name="stock_import_export"
            ),
        ]
        return custom_urls + urls
    
    def statistics_view(self, request):
        """
        Представление страницы статистики продаж
        """
        context = {
            **self.each_context(request),
            "title": _("Статистика продаж"),
        }
        return TemplateResponse(request, "admin/store/statistics.html", context)

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
store_admin_site.register(User, CustomUserAdmin)
store_admin_site.register(Group)
