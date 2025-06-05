from django.urls import path
from .views import maintenance_page_view

app_name = 'core'

urlpatterns = [
    path('maintenance/<slug:section_slug>/', maintenance_page_view, name='maintenance_page'),
    # Можно добавить URL без slug, если нужен общий fallback, но middleware должен делать редирект на URL со slug
    path('maintenance/', maintenance_page_view, name='maintenance_page_default'),
]
