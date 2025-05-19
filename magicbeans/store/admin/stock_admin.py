from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
import csv
import io

from magicbeans.store.models import StockItem, StockMovement, Strain, SeedBank
from magicbeans.store.forms import CsvImportForm
from magicbeans.store.decorators import owner_required


class StockMovementInline(admin.TabularInline):
    """Вложенная админка для отображения истории движений товара."""
    model = StockMovement
    extra = 0
    readonly_fields = ('movement_type', 'quantity', 'user', 'timestamp', 'comment')
    can_delete = False
    verbose_name = _("История движения")
    verbose_name_plural = _("История движений")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    """Административный интерфейс для управления фасовками товара."""
    list_display = (
        "strain", "seeds_count", "price", "quantity",
        "is_visible", "updated_at",
    )
    search_fields = ("strain__name", "seeds_count")
    list_filter = ("strain__seed_bank", "is_visible")
    actions = ["make_visible", "make_invisible", "export_to_csv"]
    inlines = [StockMovementInline]
    change_list_template = 'admin/store/stockitem/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-csv/", self.admin_site.admin_view(self.import_csv), name="stock_import_csv"),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        """Импортировать товары из CSV-файла."""
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
        """Сделать выбранные фасовки видимыми."""
        updated = queryset.update(is_visible=True)
        self.message_user(
            request,
            _("%(count)d фасовок отмечены как видимые.") % {"count": updated},
        )
    make_visible.short_description = _("Сделать выбранные фасовки видимыми")

    def make_invisible(self, request, queryset):
        """Сделать выбранные фасовки невидимыми."""
        updated = queryset.update(is_visible=False)
        self.message_user(
            request,
            _("%(count)d фасовок отмечены как невидимые.") % {"count": updated},
        )
    make_invisible.short_description = _("Сделать выбранные фасовки невидимыми")

    def export_to_csv(self, request, queryset):
        """Экспортировать выбранные фасовки в CSV-файл."""
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
    """Административный интерфейс для управления движениями товаров."""
    list_display = (
        "stock_item", "movement_type", "quantity",
        "user", "timestamp", "comment",
    )
    search_fields = ("stock_item__strain__name", "comment")
    list_filter = ("movement_type", "timestamp")
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        """Запрещаем добавление движений напрямую."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление движений."""
        return False
