from django.contrib import admin
from magicbeans.store.models import Administrator


@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ("name", "telegram_id", "is_active", "created_at")
    search_fields = ("name", "telegram_id")
    list_filter = ("is_active",)
    date_hierarchy = "created_at"
