from django.contrib import admin
from magicbeans.store.models import Strain, StrainImage, StockItem
from django.utils.html import format_html


class StrainImageInline(admin.TabularInline):
    model = StrainImage
    extra = 1 # Позволяет добавить одно изображение при создании сорта
    max_num = 5 # Максимум 5 изображений на сорт
    verbose_name = "Изображение"
    verbose_name_plural = "Изображения"


class StockItemInline(admin.TabularInline):
    model = StockItem
    extra = 1 # Позволяет добавить одну фасовку при создании сорта
    verbose_name = "Фасовка"
    verbose_name_plural = "Фасовки"


@admin.register(Strain)
class StrainAdmin(admin.ModelAdmin):
    list_display = ("name_colored", "seed_bank", "strain_type", "is_visible", "thc_content", "cbd_content", "flowering_time", "created_at", "updated_at")
    list_filter = ("seed_bank", "strain_type", "is_visible")
    search_fields = ("name", "seed_bank__name")
    actions = ["make_visible", "make_invisible"]
    inlines = [StrainImageInline, StockItemInline]

    def name_colored(self, obj):
        if not obj.is_visible:
            return format_html('<span style="color: #888; text-decoration: line-through;">🚫 {}</span>', obj.name)
        return format_html('<span style="color: #222;">👁️ {}</span>', obj.name)
    name_colored.short_description = "Название"
    name_colored.admin_order_field = "name"

    def make_visible(self, request, queryset):
        queryset.update(is_visible=True)
    make_visible.short_description = "Сделать выбранные сорта видимыми"

    def make_invisible(self, request, queryset):
        queryset.update(is_visible=False)
    make_invisible.short_description = "Сделать выбранные сорта невидимыми" 