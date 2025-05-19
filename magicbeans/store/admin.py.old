# Импорт административных модулей
from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Импорт моделей
from .models import (
    Administrator, SeedBank, Strain, StrainImage, StockItem,
    StockMovement, Order, OrderItem, ActionLog,
)

# Импорт представлений из подмодуля admin
from .admin.admin_views import statistics_view

class StrainImageInline(admin.TabularInline):
    model = StrainImage
    extra = 1
    max_num = 5
    verbose_name = _("Фотография сорта")
    verbose_name_plural = _("Фотографии сорта")

class StockItemInline(admin.TabularInline):
    model = StockItem
    extra = 1
    verbose_name = _("Фасовка")
    verbose_name_plural = _("Фасовки")

@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ("name", "telegram_id", "is_active", "created_at")
    search_fields = ("name", "telegram_id")
    list_filter = ("is_active",)

@admin.register(SeedBank)
class SeedBankAdmin(admin.ModelAdmin):
    list_display = ("name", "logo_preview", "strains_count", "is_visible")
    search_fields = ("name",)
    list_filter = ("is_visible",)

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" height="30" />', obj.logo.url)
        return "-"
    logo_preview.short_description = _("Логотип")

    def strains_count(self, obj):
        return obj.strains.count()
    strains_count.short_description = _("Количество сортов")

@admin.register(Strain)
class StrainAdmin(admin.ModelAdmin):
    list_display = (
        "name", "seed_bank", "strain_type", "images_count",
        "stock_items_count", "is_visible",
    )
    search_fields = ("name", "seed_bank__name")
    list_filter = ("seed_bank", "strain_type", "is_visible")
    inlines = [StrainImageInline, StockItemInline]
    list_display_links = ("name",)

    def images_count(self, obj):
        return obj.images.count()
    images_count.short_description = _("Количество фотографий")

    def stock_items_count(self, obj):
        return obj.stock_items.count()
    stock_items_count.short_description = _("Количество фасовок")

@admin.register(StrainImage)
class StrainImageAdmin(admin.ModelAdmin):
    list_display = ("strain", "image_preview", "order")
    search_fields = ("strain__name",)
    list_filter = ("strain",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="30" />', obj.image.url)
        return "-"
    image_preview.short_description = _("Изображение")

@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = (
        "strain", "seeds_count", "price", "quantity",
        "is_visible", "updated_at",
    )
    search_fields = ("strain__name", "seeds_count")
    list_filter = ("strain__seed_bank", "is_visible")
    actions = ["make_visible", "make_invisible", "export_to_csv"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("statistics/", self.admin_site.admin_view(statistics_view), name="store_statistics"),
            path("import-csv/", self.admin_site.admin_view(self.import_csv), name="stock_import_csv"),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from .forms import CsvImportForm
        import csv
        import io

        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES["csv_file"]
                update_existing = form.cleaned_data["update_existing"]

                # Проверяем расширение файла
                if not csv_file.name.endswith(".csv"):
                    messages.error(request, _("Файл должен иметь расширение .csv"))
                    return redirect(".")

                # Читаем данные из файла
                try:
                    csv_data = csv_file.read().decode("utf-8")
                    reader = csv.reader(io.StringIO(csv_data))
                    # Пропускаем заголовок
                    next(reader)

                    success_count = 0
                    error_count = 0

                    for row in reader:
                        if len(row) < 6:
                            error_count += 1
                            continue

                        seedbank_name, strain_name, seeds_count, price, quantity, is_visible = row[:6]

                        # Находим или создаем сидбанк
                        seedbank, _ = SeedBank.objects.get_or_create(name=seedbank_name)

                        # Находим или создаем сорт
                        strain, _ = Strain.objects.get_or_create(
                            name=strain_name,
                            defaults={
                                "seed_bank": seedbank,
                                "strain_type": Strain.TYPE_REGULAR
                            }
                        )

                        # Преобразуем данные
                        try:
                            price = float(price.replace(",", "."))
                            quantity = int(quantity)
                            is_visible = is_visible.lower() in ["да", "yes", "true", "1"]
                        except (ValueError, TypeError):
                            error_count += 1
                            continue

                        # Находим или создаем фасовку
                        if update_existing:
                            stock_item, created = StockItem.objects.update_or_create(
                                strain=strain,
                                seeds_count=seeds_count,
                                defaults={
                                    "price": price,
                                    "quantity": quantity,
                                    "is_visible": is_visible,
                                }
                            )
                        else:
                            stock_item = StockItem.objects.create(
                                strain=strain,
                                seeds_count=seeds_count,
                                price=price,
                                quantity=quantity,
                                is_visible=is_visible,
                            )

                        success_count += 1

                    # Выводим сообщение об успешном импорте
                    messages.success(
                        request,
                        _("Успешно импортировано %(count)d фасовок. Ошибок: %(errors)d.") % {
                            "count": success_count,
                            "errors": error_count,
                        },
                    )
                except Exception as e:
                    messages.error(request, _("Ошибка при импорте: %s") % str(e))

                # Перенаправляем на список фасовок
                return redirect("..")
        else:
            form = CsvImportForm()

        context = {
            "form": form,
            "title": _("Импорт фасовок из CSV"),
            "opts": self.model._meta,
        }
        return render(request, "admin/csv_import_form.html", context)

    def make_visible(self, request, queryset):
        updated = queryset.update(is_visible=True)
        self.message_user(
            request,
            _("%(count)d фасовок отмечены как видимые.") % {"count": updated},
        )
    make_visible.short_description = _("Сделать выбранные фасовки видимыми")

    def make_invisible(self, request, queryset):
        updated = queryset.update(is_visible=False)
        self.message_user(
            request,
            _("%(count)d фасовок отмечены как невидимые.") % {"count": updated},
        )
    make_invisible.short_description = _("Сделать выбранные фасовки невидимыми")

    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from datetime import datetime

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename=stock_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        writer = csv.writer(response)
        writer.writerow(["Сидбанк", "Сорт", "Количество семян", "Цена", "Количество на складе", "Видимость"])

        for obj in queryset:
            writer.writerow([
                obj.strain.seed_bank.name,
                obj.strain.name,
                obj.seeds_count,
                obj.price,
                obj.quantity,
                "Да" if obj.is_visible else "Нет",
            ])

        return response
    export_to_csv.short_description = _("Экспорт выбранных фасовок в CSV")

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "stock_item", "movement_type", "quantity",
        "user", "timestamp", "comment",
    )
    search_fields = ("stock_item__strain__name", "comment")
    list_filter = ("movement_type", "timestamp")
    date_hierarchy = "timestamp"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("strain_name", "seeds_count", "price")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user_telegram_id", "admin", "status",
        "total", "created_at",
    )
    search_fields = ("user_telegram_id", "admin__name")
    list_filter = ("status", "created_at")
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order", "strain_name", "seeds_count",
        "quantity", "price",
    )
    search_fields = ("strain_name", "order__user_telegram_id")
    list_filter = ("order__status",)

@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp", "user", "action_type",
        "model_name", "object_repr",
    )
    search_fields = ("user__username", "object_repr", "details")
    list_filter = ("action_type", "timestamp")
    date_hierarchy = "timestamp"
    readonly_fields = (
        "user", "action_type", "timestamp", "model_name",
        "object_id", "object_repr", "details",
    )
