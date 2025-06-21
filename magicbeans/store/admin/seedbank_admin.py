from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from magicbeans.store.models import SeedBank
from magicbeans.store.models import Strain

# Декоратор закомментирован - регистрация происходит в magicbeans_store/admin.py
# @admin.register(SeedBank)
class SeedBankAdmin(admin.ModelAdmin):
    list_display = ("name_colored", "is_visible", "website", "created_at", "updated_at", "view_strains_link")
    list_filter = ("is_visible",)
    search_fields = ("name", "website")
    actions = ["make_visible", "make_invisible"]
    ordering = ('name',)

    def name_colored(self, obj):
        if not obj.is_visible:
            return format_html('<span style="color: #888; text-decoration: line-through;">🚫 {}</span>', obj.name)
        return format_html('<span style="color: #222;">👁️ {}</span>', obj.name)
    name_colored.short_description = "Название"
    name_colored.admin_order_field = "name"

    def view_strains_link(self, obj):
        url = reverse('admin:store_strain_changelist') + f'?seed_bank__id__exact={obj.id}'
        return format_html('<a href="{}">Сорта</a>', url)
    view_strains_link.short_description = "Сорта этого сидбанка"

    def make_visible(self, request, queryset):
        queryset.update(is_visible=True)
    make_visible.short_description = "Сделать выбранные сидбанки видимыми"

    def make_invisible(self, request, queryset):
        queryset.update(is_visible=False)
    make_invisible.short_description = "Сделать выбранные сидбанки невидимыми"
