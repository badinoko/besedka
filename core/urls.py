from django.urls import path
from .views import maintenance_page_view, unified_list_ajax_filter, unified_like_api

app_name = 'core'

urlpatterns = [
    # Глобальный AJAX обработчик для всех списковых страниц
    path('ajax/filter/<str:section_name>/', unified_list_ajax_filter, name='unified_ajax_filter'),

    # Унифицированный API для лайков всех типов объектов
    path('ajax/like/', unified_like_api, name='unified_like_api'),

    # Страница "на техобслуживании"
    path('maintenance/<slug:section_slug>/', maintenance_page_view, name='maintenance_page'),
    # Можно добавить URL без slug, если нужен общий fallback, но middleware должен делать редирект на URL со slug
    path('maintenance/', maintenance_page_view, name='maintenance_page_default'),
]
