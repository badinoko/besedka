from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView
from django.db.models import Q, Min, Max, Avg, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_GET

from ..models import Strain, SeedBank, StockItem
from ..forms import StrainFilterForm, AddToCartForm
from core.base_views import UnifiedListView, unified_ajax_filter

# ==========================================================================
# AJAX-ФИЛЬТР МАГАЗИНА (УНИФИЦИРОВАННАЯ РЕАЛИЗАЦИЯ)
# ==========================================================================

@require_GET
def ajax_filter(request):
    """Универсальный AJAX-обработчик магазина через unified_ajax_filter."""
    return unified_ajax_filter(CatalogView)(request)

# ==========================================================================
# ЕДИНЫЙ КАТАЛОГ МАГАЗИНА, наследуется от UnifiedListView
# ==========================================================================
class CatalogView(UnifiedListView):
    """Публичный каталог магазина с фильтрацией"""
    model = Strain
    template_name = 'base_list_page.html'
    card_type = 'store'
    paginate_by = 9
    ajax_url_name = 'store:ajax_filter'

    section_title = "🌱 Magic Beans Store"
    section_subtitle = "Премиальные семена от ведущих сидбанков мира"
    section_hero_class = "store-hero"

    def get_queryset(self):
        """Возвращает queryset с учётом выбранных фильтров."""
        # Базовый queryset - только активные сорта
        queryset = Strain.objects.filter(is_active=True).select_related('seedbank')

        # Применяем унифицированные фильтры
        return self.apply_filters(queryset)

    def apply_filters(self, queryset):
        """Применяет фильтрацию для магазина"""
        filter_type = self.request.GET.get('filter', 'newest')

        # Унифицированные фильтры SSOT
        if filter_type == 'popular':
            # Можно сортировать по количеству заказов (когда будет реализовано)
            queryset = queryset.order_by('-created_at')
        elif filter_type == 'price_asc':
            queryset = queryset.annotate(current_price=Min('stock_items__price')).order_by('current_price')
        elif filter_type == 'price_desc':
            queryset = queryset.annotate(current_price=Min('stock_items__price')).order_by('-current_price')
        elif filter_type == 'indica':
            queryset = queryset.filter(strain_type='indica')
        else:  # newest
            queryset = queryset.order_by('-created_at')

        # Дополнительная фильтрация по форме (для совместимости)
        form = StrainFilterForm(self.request.GET)

        # Фильтрация по выбранному сидбанку из GET-параметра
        selected_seedbank_id = self.request.GET.get('seedbank_id')
        if selected_seedbank_id:
            try:
                queryset = queryset.filter(seedbank_id=int(selected_seedbank_id))
            except ValueError:
                pass

        if form.is_valid():
            # Фильтр по названию (поиск)
            name_query = form.cleaned_data.get('name')
            if name_query:
                queryset = queryset.filter(Q(name__icontains=name_query) | Q(description__icontains=name_query))

            # Фильтр по типу генетики
            genetics = form.cleaned_data.get('genetics')
            if genetics:
                queryset = queryset.filter(strain_type__in=genetics)

            # Фильтр по цене
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')
            if min_price is not None:
                queryset = queryset.annotate(current_price=Min('stock_items__price')).filter(current_price__gte=min_price)
            if max_price is not None:
                queryset = queryset.annotate(current_price=Min('stock_items__price')).filter(current_price__lte=max_price)

        return queryset

    def get_context_data(self, **kwargs):
        # Используем базовый контекст UnifiedListView
        context = super().get_context_data(**kwargs)

        # Дополнительные данные каталога (seedbanks + форма фильтрации)
        context['filter_form'] = StrainFilterForm(self.request.GET or None)
        context['seedbanks'] = SeedBank.objects.filter(is_active=True).order_by('name')

        selected_seedbank_id = self.request.GET.get('seedbank_id')
        context['selected_seedbank_id'] = int(selected_seedbank_id) if selected_seedbank_id and selected_seedbank_id.isdigit() else None

        # Для совместимости со старым шаблоном, предоставляем переменную strains
        context['strains'] = context['page_obj']

        return context

    def get_filter_list(self):
        """Унифицированные AJAX-фильтры каталога (соответствуют стандартам SSOT)"""
        return [
            {'id': 'newest', 'label': 'Новые'},
            {'id': 'popular', 'label': 'Популярные'},
            {'id': 'price_asc', 'label': 'Дешевые'},
            {'id': 'price_desc', 'label': 'Дорогие'},
            {'id': 'indica', 'label': 'Индика'},
        ]

    def get_hero_stats(self):
        """Статистика для hero-секции магазина"""
        total_strains = Strain.objects.filter(is_active=True).count()
        total_seedbanks = SeedBank.objects.filter(is_active=True).count()
        avg_price = StockItem.objects.filter(is_active=True, quantity__gt=0).aggregate(avg=Avg('price')).get('avg') or 0
        return [
            {'icon': 'fa-seedling', 'count': total_strains, 'label': 'сортов'},
            {'icon': 'fa-industry', 'count': total_seedbanks, 'label': 'сидбанков'},
            {'icon': 'fa-tag', 'count': f"{int(avg_price)} ₽" if avg_price else '—', 'label': 'средняя цена'},
        ]

class StrainDetailView(DetailView):
    """Детальная страница сорта"""
    model = Strain
    template_name = 'store/strain_detail.html'
    context_object_name = 'strain'

    def get_queryset(self):
        # Показывать только активные сорта
        return super().get_queryset().filter(is_active=True).select_related('seedbank').prefetch_related('stock_items')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stock_items = self.object.stock_items.filter(is_active=True, quantity__gt=0).order_by('seeds_count')

        stock_items_with_forms = []
        for stock_item in stock_items:
            stock_items_with_forms.append({
                'item': stock_item,
                'form': AddToCartForm(initial={'stock_item_id': stock_item.id, 'quantity': 1})
            })

        context['stock_items_with_forms'] = stock_items_with_forms

        # -----------------------------
        # УНИФИЦИРОВАННАЯ HERO-СЕКЦИЯ
        # -----------------------------
        from django.db.models import Sum, Min  # локальный импорт, чтобы избежать циклов

        total_variants = stock_items.count()
        total_packs_available = stock_items.aggregate(total=Sum('quantity'))['total'] or 0
        min_price = stock_items.aggregate(min=Min('price'))['min'] if stock_items else None

        context['detail_hero_stats'] = [
            {
                'value': total_variants,
                'label': self.request._('вариантов') if hasattr(self.request, '_') else 'вариантов',
                'css_class': 'variants',
                'icon': 'fa-box-open',
            },
            {
                'value': total_packs_available,
                'label': self.request._('упаковок') if hasattr(self.request, '_') else 'упаковок',
                'css_class': 'stock',
                'icon': 'fa-box',
            },
            {
                'value': f"{int(min_price)} ₽" if min_price else '—',
                'label': self.request._('от цены') if hasattr(self.request, '_') else 'от цены',
                'css_class': 'price',
                'icon': 'fa-tag',
            },
        ]

        return context

# TODO: Реализовать представления для корзины (добавление, просмотр, удаление, изменение количества)
# TODO: Реализовать представления для оформления заказа
# TODO: Реализовать представления для личного кабинета пользователя (история заказов и т.д.)
