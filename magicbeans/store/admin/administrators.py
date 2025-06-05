from django.contrib import admin
from magicbeans.store.models import Administrator

# Декоратор закомментирован - регистрация происходит в magicbeans_store/admin.py
# @admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ("user", "can_manage_seedbanks", "can_manage_strains", "can_manage_stock", "can_view_orders")
    list_filter = ("can_manage_seedbanks", "can_manage_strains", "can_manage_stock", "can_view_orders")
    search_fields = ("user__username", "user__first_name", "user__last_name")
