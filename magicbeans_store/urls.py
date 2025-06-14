from django.urls import path
from .views import (
    CatalogView, StrainDetailView,
    CartView, AddToCartView, UpdateCartView, RemoveFromCartView, # ApplyCouponToCartView, # Купоны отключены
    MyOrdersView, OrderDetailView
)
from .views.catalog import ajax_filter
from .views.checkout import SecureCheckoutView, OrderSuccessView

app_name = "store"

urlpatterns = [
    # Каталог
    path("", CatalogView.as_view(), name="catalog"),
    path("strain/<int:pk>/", StrainDetailView.as_view(), name="strain_detail"),

    # AJAX фильтрация
    path("ajax-filter/", ajax_filter, name="ajax_filter"),

    # Поиск
    path("search/", CatalogView.as_view(), name="search"),

    # Корзина
    path("cart/", CartView.as_view(), name="cart_detail"),
    path("cart/add/", AddToCartView.as_view(), name="add_to_cart"),
    path("cart/update/", UpdateCartView.as_view(), name="update_cart"),
    path("cart/remove/", RemoveFromCartView.as_view(), name="remove_from_cart"),
    # path("cart/apply-coupon/", ApplyCouponToCartView.as_view(), name="apply_coupon"), # Купоны отключены

    # Оформление заказа
    path("checkout/", SecureCheckoutView.as_view(), name="checkout"),
    path("order/<int:order_pk>/success/", OrderSuccessView.as_view(), name="order_success_page"),

    # Заказы пользователя
    path("orders/", MyOrdersView.as_view(), name="my_orders"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order_detail"),
]
