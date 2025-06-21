from .catalog import CatalogView, StrainDetailView
from .cart import CartView, AddToCartView, UpdateCartView, RemoveFromCartView #, ApplyCouponToCartView # Купоны отключены
from .checkout import SecureCheckoutView as CheckoutView, OrderSuccessView
from .orders import MyOrdersView, OrderDetailView

__all__ = [
    'CatalogView',
    'StrainDetailView',
    'CartView',
    'AddToCartView',
    'UpdateCartView',
    'RemoveFromCartView',
    # 'ApplyCouponToCartView', # Купоны отключены
    'CheckoutView',
    'OrderSuccessView',
    'MyOrdersView',
    'OrderDetailView',
]
