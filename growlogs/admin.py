from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import GrowLog, GrowLogEntry
from core.admin_mixins import ModeratorAdminMixin

class GrowLogEntryInline(admin.TabularInline):
    model = GrowLogEntry
    extra = 0
    readonly_fields = ['created_at']

class GrowLogAdmin(ModeratorAdminMixin, admin.ModelAdmin):
    """Админка для grow logs с поддержкой кнопки ОТМЕНА"""
    list_display = ['title', 'grower', 'strain', 'is_public', 'start_date', 'created_at']
    list_filter = ['is_public', 'strain', 'start_date', 'created_at']
    search_fields = ['title', 'grower__username', 'strain__name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [GrowLogEntryInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'grower', 'strain', 'is_public')
        }),
        ('Период выращивания', {
            'fields': ('start_date', 'end_date')
        }),
        ('Содержание', {
            'fields': ('setup_description',)
        })
    )

class GrowLogEntryAdmin(ModeratorAdminMixin, admin.ModelAdmin):
    """Админка для записей grow logs с поддержкой кнопки ОТМЕНА"""
    list_display = ['growlog', 'day', 'description_preview', 'temperature', 'humidity', 'ph', 'created_at']
    list_filter = ['growlog', 'created_at']
    search_fields = ['description', 'growlog__title']
    readonly_fields = ['created_at']

    def description_preview(self, obj):
        """Показывает первые 50 символов описания"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Описание'

# НЕ регистрируем в стандартной админке Django - только в кастомных!
# admin.site.register(GrowLog, GrowLogAdmin)
# admin.site.register(GrowLogEntry, GrowLogEntryAdmin)

# Регистрируем в админке модератора для модерации
from core.admin_site import moderator_admin_site
moderator_admin_site.register(GrowLog, GrowLogAdmin)
moderator_admin_site.register(GrowLogEntry, GrowLogEntryAdmin)
