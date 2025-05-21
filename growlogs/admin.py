from django.contrib import admin
from .models import GrowLog, GrowLogEntry

class GrowLogEntryInline(admin.TabularInline):
    model = GrowLogEntry
    extra = 1

@admin.register(GrowLog)
class GrowLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'grower', 'strain', 'start_date', 'end_date', 'is_public', 'created_at')
    search_fields = ('title', 'grower__username', 'strain__name')
    list_filter = ('is_public', 'start_date', 'created_at')
    autocomplete_fields = ('grower', 'strain')
    inlines = [GrowLogEntryInline]

@admin.register(GrowLogEntry)
class GrowLogEntryAdmin(admin.ModelAdmin):
    list_display = ('growlog', 'day', 'temperature', 'humidity', 'ph', 'created_at')
    search_fields = ('growlog__title', 'description')
    list_filter = ('day', 'created_at')
    autocomplete_fields = ('growlog',)
