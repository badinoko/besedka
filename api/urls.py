"""
URL маршруты для API Telegram-бота
"""

from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api'

# API v1 маршруты
v1_patterns = [
    # Аутентификация
    path('auth/telegram/', views.TelegramAuthView.as_view(), name='telegram_auth'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.user_profile, name='user_profile'),

    # Каталог
    path('catalog/seedbanks/', views.SeedBankListView.as_view(), name='seedbanks'),
    path('catalog/strains/', views.StrainListView.as_view(), name='strains'),
    path('catalog/strains/<int:id>/', views.StrainDetailView.as_view(), name='strain_detail'),

    # Заказы
    path('orders/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/my/', views.UserOrdersView.as_view(), name='user_orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),

    # Доставка и оплата
    path('shipping-methods/', views.ShippingMethodsView.as_view(), name='shipping_methods'),
    path('payment-methods/', views.PaymentMethodsView.as_view(), name='payment_methods'),

    # Промоакции и купоны
    path('promotions/', views.PromotionsView.as_view(), name='promotions'),
    path('coupons/validate/', views.validate_coupon, name='validate_coupon'),

    # Статус
    path('status/', views.api_status, name='status'),
]

urlpatterns = [
    path('v1/', include(v1_patterns)),
]
