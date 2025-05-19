# Переопределение модели администратора для страницы статистики
from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _

from .admin_views import statistics_view

class StoreAdminSite(admin.AdminSite):
    site_header = _("Magic Beans Administration")
    site_title = _("Magic Beans Admin")
    index_title = _("Управление магазином Magic Beans")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("statistics/", self.admin_view(statistics_view), name="store_statistics"),
        ]
        return custom_urls + urls
