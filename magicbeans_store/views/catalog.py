from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Max, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages

from ..models import Strain, SeedBank, StockItem
from ..forms import StrainFilterForm, AddToCartForm

class CatalogView(ListView):
    """Публичный каталог магазина с фильтрацией"""
    model = Strain
    template_name = 'store/catalog.html'
    context_object_name = 'strains'
    paginate_by = 12

    def get_queryset(self):
        queryset = Strain.objects.filter(is_active=True).select_related('seedbank')
        form = StrainFilterForm(self.request.GET)

        # Фильтрация по выбранному сидбанку из GET-параметра
        selected_seedbank_id = self.request.GET.get('seedbank_id')
        if selected_seedbank_id:
            try:
                queryset = queryset.filter(seedbank_id=int(selected_seedbank_id))
            except ValueError:
                # Если ID невалидный, можно просто игнорировать или показать ошибку
                pass # Пока просто игнорируем

        if form.is_valid():
            # Фильтр по названию (поиск)
            name_query = form.cleaned_data.get('name')
            if name_query:
                queryset = queryset.filter(Q(name__icontains=name_query) | Q(description__icontains=name_query))

            # Фильтр по типу генетики
            genetics = form.cleaned_data.get('genetics')
            if genetics:
                queryset = queryset.filter(strain_type__in=genetics)

            # Фильтр по тегам (если есть)
            tags = form.cleaned_data.get('tags')
            if tags:
                queryset = queryset.filter(tags__in=tags).distinct()

            # Фильтр по цене
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')
            if min_price is not None:
                queryset = queryset.annotate(current_price=Min('stock_items__price')).filter(current_price__gte=min_price)
            if max_price is not None:
                queryset = queryset.annotate(current_price=Min('stock_items__price')).filter(current_price__lte=max_price)

            # Сортировка
            sort_by = form.cleaned_data.get('sort_by')
            if sort_by:
                if sort_by == 'name_asc':
                    queryset = queryset.order_by('name')
                elif sort_by == 'name_desc':
                    queryset = queryset.order_by('-name')
                elif sort_by == 'price_asc':
                    queryset = queryset.annotate(current_price=Min('stock_items__price')).order_by('current_price')
                elif sort_by == 'price_desc':
                    queryset = queryset.annotate(current_price=Min('stock_items__price')).order_by('-current_price')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = StrainFilterForm(self.request.GET or None)
        context['seedbanks'] = SeedBank.objects.filter(is_active=True).order_by('name')

        selected_seedbank_id = self.request.GET.get('seedbank_id')
        if selected_seedbank_id:
            try:
                context['selected_seedbank_id'] = int(selected_seedbank_id)
            except ValueError:
                context['selected_seedbank_id'] = None
        else:
            context['selected_seedbank_id'] = None

        return context

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
        # context['average_rating'] = self.object.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return context

# TODO: Реализовать представления для корзины (добавление, просмотр, удаление, изменение количества)
# TODO: Реализовать представления для оформления заказа
# TODO: Реализовать представления для личного кабинета пользователя (история заказов и т.д.)
