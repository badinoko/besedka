from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.template.response import TemplateResponse
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export.fields import Field
from .models import (
    SeedBank, Strain, StockItem, Order, OrderStatus,
    Promotion, Coupon, ShippingMethod, PaymentMethod,
    StoreSettings, SalesReport, InventoryReport, OrderItem,
    SBPSettings
)
from .resources import StockItemResource
from django.utils.html import format_html
from core.admin_site import store_admin_site, store_owner_site, owner_admin_site
from django.http import HttpResponseRedirect
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from core.admin_mixins import StoreAdminMixin
from django.contrib.auth import get_user_model
from django.db import models

# ======================================================================
# БАЗОВАЯ НАСТРОЙКА ДЛЯ ВСЕХ АДМИНОК МАГАЗИНА
# ======================================================================

# StoreAdminMixin теперь импортируется из core.admin_mixins

# ======================================================================
# Ресурсы для импорта/экспорта
# ======================================================================

class SeedBankResource(resources.ModelResource):
    class Meta:
        model = SeedBank
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name', 'description', 'website', 'is_active')

class StrainResource(resources.ModelResource):
    seedbank_name = Field(column_name='seedbank_name')

    def dehydrate_seedbank_name(self, strain):
        return strain.seedbank.name if strain.seedbank else ''

    class Meta:
        model = Strain
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name', 'seedbank', 'seedbank_name', 'strain_type', 'description', 'is_active')

class StockItemResource(resources.ModelResource):
    strain_name = Field(column_name='strain_name')
    seedbank_name = Field(column_name='seedbank_name')

    def dehydrate_strain_name(self, stock_item):
        return stock_item.strain.name

    def dehydrate_seedbank_name(self, stock_item):
        return stock_item.strain.seedbank.name if stock_item.strain.seedbank else ''

    class Meta:
        model = StockItem
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'strain', 'strain_name', 'seedbank_name', 'seeds_count', 'price', 'quantity', 'sku')

# ======================================================================
# ИНЛАЙН КЛАССЫ ДЛЯ СВЯЗАННЫХ МОДЕЛЕЙ
# ======================================================================

class OrderItemInline(admin.TabularInline):
    """Инлайн для позиций заказа"""
    model = OrderItem
    extra = 0
    readonly_fields = ['total']
    autocomplete_fields = ['stock_item']

# ======================================================================
# АДМИНКИ СИДБАНКОВ
# ======================================================================

class SeedBankAdmin(StoreAdminMixin, ImportExportModelAdmin):
    """Админка сидбанков для администратора магазина"""
    resource_class = SeedBankResource
    list_display = ['name', 'strains_count', 'stock_items_count', 'website', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'strains_count', 'stock_items_count']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'website', 'logo', 'is_active')
        }),
        ('📊 Статистика', {
            'fields': ('strains_count', 'stock_items_count'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def strains_count(self, obj):
        """Количество сортов в сидбанке"""
        count = obj.strains.count()
        active_count = obj.strains.filter(is_active=True).count()
        if count == 0:
            return format_html('<span style="color: #999;">0 сортов</span>')

        color = '#28a745' if active_count > 0 else '#6c757d'
        return format_html(
            '<span style="color: {}; font-weight: bold;">🌿 {} сортов</span><br>'
            '<small style="color: #666;">({} активных)</small>',
            color, count, active_count
        )
    strains_count.short_description = "Сорта"
    strains_count.admin_order_field = 'strains__count'

    def stock_items_count(self, obj):
        """Количество товаров в сидбанке"""
        count = StockItem.objects.filter(strain__seedbank=obj).count()
        active_count = StockItem.objects.filter(strain__seedbank=obj, is_active=True).count()
        total_seeds = StockItem.objects.filter(
            strain__seedbank=obj, is_active=True
        ).aggregate(total=models.Sum('seeds_count'))['total'] or 0

        if count == 0:
            return format_html('<span style="color: #999;">0 товаров</span>')

        color = '#28a745' if active_count > 0 else '#6c757d'
        return format_html(
            '<span style="color: {}; font-weight: bold;">📦 {} товаров</span><br>'
            '<small style="color: #666;">({} активных, {} семян)</small>',
            color, count, active_count, total_seeds
        )
    stock_items_count.short_description = "Товары на складе"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('strains')

class SeedBankStoreOwnerAdmin(StoreAdminMixin, ImportExportModelAdmin):
    """Админка сидбанков для владельца магазина"""
    resource_class = SeedBankResource
    list_display = ['name', 'strains_count', 'stock_items_count', 'website', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def strains_count(self, obj):
        count = obj.strains.count()
        return format_html('<span style="font-weight: bold;">🌿 {} сортов</span>', count)
    strains_count.short_description = "Сорта"

    def stock_items_count(self, obj):
        count = StockItem.objects.filter(strain__seedbank=obj).count()
        return format_html('<span style="font-weight: bold;">📦 {} товаров</span>', count)
    stock_items_count.short_description = "Товары"

# ======================================================================
# АДМИНКИ СОРТОВ
# ======================================================================

class StrainAdmin(StoreAdminMixin, ImportExportModelAdmin):
    """Админка сортов для администратора магазина"""
    resource_class = StrainResource
    list_display = [
        'name', 'seedbank', 'strain_type', 'stock_count', 'total_seeds',
        'thc_content', 'cbd_content', 'is_visible'
    ]
    list_filter = [
        'strain_type', 'seedbank', 'is_active', 'flowering_time',
        'thc_content', 'cbd_content'
    ]
    search_fields = ['name', 'description', 'genetics']
    readonly_fields = ['created_at', 'updated_at', 'stock_count', 'total_seeds']
    autocomplete_fields = ['seedbank']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'seedbank', 'strain_type', 'is_active')
        }),
        ('Описание', {
            'fields': ('description',)
        }),
        ('Генетика и характеристики', {
            'fields': ('genetics', 'thc_content', 'cbd_content', 'flowering_time', 'height', 'yield_indoor', 'yield_outdoor')
        }),
        ('📊 Складская статистика', {
            'fields': ('stock_count', 'total_seeds'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def stock_count(self, obj):
        """Количество товаров этого сорта"""
        count = obj.stock_items.count()
        active_count = obj.stock_items.filter(is_active=True).count()

        if count == 0:
            return format_html('<span style="color: #999;">📦 0 товаров</span>')

        color = '#28a745' if active_count > 0 else '#6c757d'
        return format_html(
            '<span style="color: {}; font-weight: bold;">📦 {} товаров</span><br>'
            '<small style="color: #666;">({} активных)</small>',
            color, count, active_count
        )
    stock_count.short_description = "Товары на складе"

    def total_seeds(self, obj):
        """Общее количество семян этого сорта"""
        total = obj.stock_items.filter(is_active=True).aggregate(
            total=models.Sum('seeds_count')
        )['total'] or 0

        total_quantity = obj.stock_items.filter(is_active=True).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

        if total == 0:
            return format_html('<span style="color: #999;">🌱 0 семян</span>')

        return format_html(
            '<span style="color: #28a745; font-weight: bold;">🌱 {} семян</span><br>'
            '<small style="color: #666;">(в {} упаковках)</small>',
            total, total_quantity
        )
    total_seeds.short_description = "Всего семян"

    def is_visible(self, obj):
        return "✅ Видимый" if obj.is_active else "❌ Скрытый"
    is_visible.short_description = "Статус видимости"
    is_visible.admin_order_field = 'is_active'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('seedbank').prefetch_related('stock_items')

class StrainStoreOwnerAdmin(StoreAdminMixin, ImportExportModelAdmin):
    """Админка сортов для владельца магазина"""
    resource_class = StrainResource
    list_display = [
        'name', 'seedbank', 'strain_type', 'stock_count',
        'thc_content', 'cbd_content', 'flowering_time', 'is_active'
    ]
    list_filter = [
        'strain_type', 'seedbank', 'is_active', 'flowering_time',
        'thc_content', 'cbd_content'
    ]
    search_fields = ['name', 'description', 'genetics']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['seedbank']

    def stock_count(self, obj):
        count = obj.stock_items.count()
        return format_html('<span style="font-weight: bold;">📦 {} товаров</span>', count)
    stock_count.short_description = "Товары"

# ======================================================================
# АДМИНКИ ТОВАРОВ
# ======================================================================

class StockItemAdmin(StoreAdminMixin, ImportExportModelAdmin):
    """Админка товаров для администратора магазина"""
    resource_class = StockItemResource
    list_display = [
        '__str__', 'strain', 'seeds_count', 'price', 'quantity',
        'total_value', 'availability_status', 'is_active'
    ]
    list_filter = [
        'seeds_count', 'is_active', 'strain__seedbank',
        'strain__strain_type', 'created_at'
    ]
    search_fields = ['strain__name', 'strain__seedbank__name', 'sku']
    readonly_fields = ['created_at', 'updated_at', 'sku', 'total_value']
    autocomplete_fields = ['strain']

    fieldsets = (
        ('Основная информация', {
            'fields': ('strain', 'seeds_count', 'is_active')
        }),
        ('Цена и склад', {
            'fields': ('price', 'quantity', 'total_value', 'sku')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def total_value(self, obj):
        """Общая стоимость товара на складе"""
        if obj.price and obj.quantity:
            total = float(obj.price * obj.quantity)
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">💰 {} ₽</span>',
                f"{total:.2f}"
            )
        return format_html('<span style="color: #999;">—</span>')
    total_value.short_description = "Общая стоимость"

    def availability_status(self, obj):
        """Статус доступности товара"""
        if not obj.is_active:
            return format_html('<span style="color: #dc3545;">❌ Неактивен</span>')

        if obj.quantity == 0:
            return format_html('<span style="color: #ffc107;">⚠️ Нет в наличии</span>')
        elif obj.quantity <= 5:
            return format_html('<span style="color: #fd7e14;">📊 Мало ({})</span>', obj.quantity)
        else:
            return format_html('<span style="color: #28a745;">✅ В наличии ({})</span>', obj.quantity)
    availability_status.short_description = "Наличие"
    availability_status.admin_order_field = 'quantity'

class StockItemStoreOwnerAdmin(StoreAdminMixin, ImportExportModelAdmin):
    """Админка товаров для владельца магазина"""
    resource_class = StockItemResource
    list_display = [
        '__str__', 'strain', 'seeds_count', 'price',
        'quantity', 'total_value', 'is_active'
    ]
    list_filter = [
        'seeds_count', 'is_active', 'strain__seedbank',
        'strain__strain_type', 'created_at'
    ]
    search_fields = ['strain__name', 'strain__seedbank__name', 'sku']
    readonly_fields = ['created_at', 'updated_at', 'sku']
    autocomplete_fields = ['strain']

    def total_value(self, obj):
        if obj.price and obj.quantity:
            total = float(obj.price * obj.quantity)
            return format_html('<span style="font-weight: bold;">💰 {} ₽</span>', f"{total:.2f}")
        return '—'
    total_value.short_description = "Общая стоимость"

# ======================================================================
# АДМИНКИ ЗАКАЗОВ
# ======================================================================

class OrderAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Админка заказов для администратора магазина"""
    model = Order
    list_display = [
        'id', 'user', 'status', 'total_amount',
        'payment_method', 'created_at', 'can_be_cancelled'
    ]
    list_filter = [
        'status', 'payment_method', 'shipping_method', 'created_at'
    ]
    search_fields = ['id', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['cancel_selected_orders']

    fieldsets = (
        ('Информация о заказе', {
            'fields': ('user', 'status')
        }),
        ('Финансовая информация', {
            'fields': ('total_amount', 'payment_method', 'shipping_cost')
        }),
        ('Доставка', {
            'fields': ('shipping_method', 'shipping_address')
        }),
        ('Дополнительная информация', {
            'fields': ('comment',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False

    def can_be_cancelled(self, obj):
        """Отображение возможности отмены заказа"""
        return obj.can_be_cancelled
    can_be_cancelled.short_description = "Можно отменить"
    can_be_cancelled.boolean = True

    def cancel_selected_orders(self, request, queryset):
        """Массовая отмена выбранных заказов"""
        cancelled_count = 0
        failed_count = 0

        for order in queryset:
            if order.cancel_order(cancelled_by_user=request.user, reason="Отменен администратором"):
                cancelled_count += 1
            else:
                failed_count += 1

        if cancelled_count > 0:
            self.message_user(
                request,
                f"Успешно отменено заказов: {cancelled_count}. Товары возвращены на склад."
            )

        if failed_count > 0:
            self.message_user(
                request,
                f"Не удалось отменить заказов: {failed_count} (возможно, они уже в финальном статусе).",
                level='warning'
            )

    cancel_selected_orders.short_description = "Отменить выбранные заказы (с возвратом товаров на склад)"

# OrderStoreOwnerAdmin удален - владелец магазина получает доступ к заказам
# через переход в админку администраторов магазина

# ======================================================================
# ДОПОЛНИТЕЛЬНЫЕ МОДЕЛИ МАГАЗИНА
# ======================================================================

# Классы админок для дополнительных моделей
class OrderStatusAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Админка статусов заказов"""
    list_display = ['name', 'color', 'is_final', 'order']
    list_filter = ['is_final']
    search_fields = ['name', 'description']

class ShippingMethodAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Админка способов доставки"""
    list_display = ['name', 'price', 'estimated_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

class PaymentMethodAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Админка способов оплаты"""
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

class SBPSettingsAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Админка настроек СБП"""
    list_display = ['bank_name', 'account_holder', 'phone_number', 'is_active', 'updated_at']
    list_filter = ['is_active', 'bank_name']
    search_fields = ['bank_name', 'account_holder', 'phone_number']
    fieldsets = (
        ('Основные реквизиты', {
            'fields': ('bank_name', 'account_holder', 'phone_number')
        }),
        ('Дополнительные реквизиты', {
            'fields': ('bank_account', 'bik', 'inn'),
            'classes': ('collapse',)
        }),
        ('Инструкции для клиентов', {
            'fields': ('payment_instructions',)
        }),
        ('Настройки', {
            'fields': ('is_active',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

class PromotionAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Админка акций"""
    list_display = ['name', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'discount_type', 'start_date', 'end_date']
    search_fields = ['name', 'description']

class CouponAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Админка купонов"""
    list_display = ['code', 'discount_percentage', 'max_uses', 'uses_count', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['code', 'description']

class SalesReportAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Отчеты по продажам"""
    change_list_template = 'admin/store/sales_report.html'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class InventoryReportAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Отчеты по складу"""
    change_list_template = 'admin/store/inventory_report.html'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class StoreSettingsAdmin(StoreAdminMixin, admin.ModelAdmin):
    """Админка настроек магазина"""
    list_display = ['site_name', 'store_email', 'store_phone', 'maintenance_mode']

    fieldsets = (
        ('Основная информация', {
            'fields': ('site_name', 'store_email', 'store_phone', 'store_address')
        }),
        ('Настройки заказов', {
            'fields': ('min_order_amount', 'free_shipping_amount')
        }),
        ('Режим обслуживания', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
    )

    def has_add_permission(self, request):
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

# ======================================================================
# АДМИНКА ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТОРАМИ МАГАЗИНА
# ======================================================================

User = get_user_model()

class StoreAdminUserAdmin(admin.ModelAdmin):
    """Админка для управления администраторами магазина (только для store_owner)"""
    list_display = ['username', 'name', 'telegram_username', 'is_active', 'date_joined']
    list_filter = ['is_active', 'date_joined']
    search_fields = ['username', 'name', 'telegram_username']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'name', 'telegram_username')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Даты', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Показываем только пользователей с ролью store_admin"""
        qs = super().get_queryset(request)
        return qs.filter(role='store_admin')

    def has_add_permission(self, request):
        """Запрещаем создание через админку - используем отдельное представление"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Разрешаем удаление (увольнение) администраторов"""
        return True

# ======================================================================
# РЕГИСТРАЦИЯ МОДЕЛЕЙ В АДМИНКАХ ПО РОЛЯМ
# ======================================================================

# 🏪 ВЛАДЕЛЕЦ МАГАЗИНА - Стратегическое управление
# Только стратегические и управленческие модели, БЕЗ операционных

store_owner_site.register(User, StoreAdminUserAdmin)
store_owner_site.register(StoreSettings, StoreSettingsAdmin)
store_owner_site.register(SalesReport, SalesReportAdmin)
store_owner_site.register(InventoryReport, InventoryReportAdmin)
store_owner_site.register(PaymentMethod, PaymentMethodAdmin)
store_owner_site.register(ShippingMethod, ShippingMethodAdmin)
store_owner_site.register(SBPSettings, SBPSettingsAdmin)
store_owner_site.register(Promotion, PromotionAdmin)
store_owner_site.register(Coupon, CouponAdmin)

# 📦 АДМИНИСТРАТОР МАГАЗИНА - Операционное управление каталогом
# Все операционные модели только в store_admin

store_admin_site.register(SeedBank, SeedBankAdmin)
store_admin_site.register(Strain, StrainAdmin)
store_admin_site.register(StockItem, StockItemAdmin)
store_admin_site.register(OrderStatus, OrderStatusAdmin)
store_admin_site.register(Order, OrderAdmin)
store_admin_site.register(Promotion, PromotionAdmin)
store_admin_site.register(Coupon, CouponAdmin)
