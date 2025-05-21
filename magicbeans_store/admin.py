from django.contrib import admin
from .models import SeedBank, Strain, StockItem

@admin.register(SeedBank)
class SeedBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Strain)
class StrainAdmin(admin.ModelAdmin):
    list_display = ('name', 'breeder', 'genetics', 'flowering_time', 'thc_content', 'created_at')
    search_fields = ('name', 'genetics', 'description')
    list_filter = ('breeder', 'flowering_time', 'created_at')
    autocomplete_fields = ('breeder',)

@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('strain', 'seeds_count', 'price', 'discount', 'final_price', 'in_stock', 'created_at')
    search_fields = ('strain__name',)
    list_filter = ('in_stock', 'seeds_count', 'created_at')
    autocomplete_fields = ('strain',)
    list_editable = ('in_stock', 'price', 'discount')
    readonly_fields = ('final_price',)
