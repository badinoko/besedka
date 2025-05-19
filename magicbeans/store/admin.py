from django.contrib import admin
from .models import (
    Administrator, Producer, Type, Product, ProductPhoto, ProductPackage, Order, OrderItem,
)

class ProductPhotoInline(admin.TabularInline):
    model = Product.photos.through
    extra = 1

class ProductPackageInline(admin.TabularInline):
    model = ProductPackage
    extra = 1

@admin.register(Producer)
class ProducerAdmin(admin.ModelAdmin):
    list_display = ("name", "hidden")
    search_fields = ("name",)
    list_filter = ("hidden",)
    inlines = []

@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "type", "hidden")
    search_fields = ("name", "producer__name")
    list_filter = ("producer", "type", "hidden")
    inlines = [ProductPhotoInline, ProductPackageInline]
    filter_horizontal = ("photos",)

@admin.register(ProductPhoto)
class ProductPhotoAdmin(admin.ModelAdmin):
    list_display = ("image",)

@admin.register(ProductPackage)
class ProductPackageAdmin(admin.ModelAdmin):
    list_display = ("product", "seeds_count", "price", "stock")
    search_fields = ("product__name",)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "created_at", "admin_telegram_id", "user_telegram_id", "total",
    )
    search_fields = ("admin_telegram_id", "user_telegram_id")
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order", "product_name_snapshot", "seeds_count_snapshot",
        "quantity", "price_snapshot",
    )
    search_fields = ("product_name_snapshot",)
