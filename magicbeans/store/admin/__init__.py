"""
Модуль инициализации административных интерфейсов.
Регистрирует все административные классы для моделей магазина.
"""
from django.contrib import admin
from magicbeans.store.admin.administrators import AdministratorAdmin
from magicbeans.store.admin.stock_admin import StockItemAdmin, StockMovementAdmin
from magicbeans.store.models import SeedBank, Strain, StrainImage, ActionLog
# Все декораторы закомментированы - регистрация происходит в magicbeans_store/admin.py

# @admin.register(SeedBank)
# class OldSeedBankAdmin(admin.ModelAdmin):
#     list_display = ("name", "is_visible", "created_at", "updated_at")
#     search_fields = ("name",)
#     list_filter = ("is_visible",)
#     ordering = ("name",)

# @admin.register(Strain)
# class OldStrainAdmin(admin.ModelAdmin):
#     list_display = ("name", "strain_type", "seed_bank", "is_visible", "created_at", "updated_at")
#     search_fields = ("name", "seed_bank__name")
#     list_filter = ("strain_type", "seed_bank", "is_visible")
#     ordering = ("name",)

# @admin.register(StrainImage)
# class OldStrainImageAdmin(admin.ModelAdmin):
#     list_display = ("strain", "order", "image")
#     search_fields = ("strain__name",)
#     ordering = ("strain", "order")

# @admin.register(ActionLog)
# class OldActionLogAdmin(admin.ModelAdmin):
#     list_display = ("user", "action_type", "timestamp", "model_name", "object_id", "object_repr")
#     search_fields = ("user__username", "model_name", "object_repr")
#     list_filter = ("action_type", "model_name")
#     date_hierarchy = "timestamp"
