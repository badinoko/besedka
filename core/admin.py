from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ActionLog, MaintenanceModeSetting
from .admin_site import store_admin_site, owner_admin_site
from core.admin_mixins import BaseAdminMixin

class ActionLogAdmin(BaseAdminMixin, admin.ModelAdmin):
    """Логи действий с поддержкой кнопки ОТМЕНА"""
    list_display = ('user', 'action_type', 'timestamp', 'model_name', 'object_id', 'object_repr')
    search_fields = ('user__username', 'model_name', 'object_repr')
    list_filter = ('action_type', 'model_name', 'timestamp')
    readonly_fields = ('user', 'action_type', 'timestamp', 'model_name', 'object_id', 'object_repr')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        """Логи нельзя создавать вручную"""
        return False

    def has_change_permission(self, request, obj=None):
        """Логи нельзя изменять"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Логи может удалять только владелец платформы"""
        return request.user.is_superuser or request.user.role == 'owner'

# Регистрация в админке владельца платформы
owner_admin_site.register(ActionLog, ActionLogAdmin)

# В админке магазина не регистрируем ActionLog, так как это не относится к магазину

# Заготовка для статистики
class Statistics:
    class Meta:
        verbose_name = _('Статистика')
        verbose_name_plural = _('Статистика')

class StatisticsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = _('Статистика (раздел в разработке)')
        return super().changelist_view(request, extra_context=extra_context)

# Заготовка для бэкапов
class Backup:
    class Meta:
        verbose_name = _('Бэкапы')
        verbose_name_plural = _('Бэкапы')

class BackupAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = _('Бэкапы (раздел в разработке)')
        return super().changelist_view(request, extra_context=extra_context)

class MaintenanceModeSettingAdmin(BaseAdminMixin, admin.ModelAdmin):
    list_display = ('section_name', 'is_enabled', 'title', 'color_scheme', 'expected_recovery_time')
    list_filter = ('is_enabled', 'section_name', 'color_scheme')
    search_fields = ('section_name', 'title', 'message')
    ordering = ('section_name',)

    # Позволяем редактировать, но не добавлять и не удалять из админки
    # Новые разделы должны добавляться через SECTION_CHOICES в модели и создаваться командой
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

owner_admin_site.register(MaintenanceModeSetting, MaintenanceModeSettingAdmin)
