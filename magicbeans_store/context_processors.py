from .models import Cart
from .utils import get_cart

def cart_item_count(request):
    count = 0
    cart, _ = get_cart(request)
    if cart:
        count = cart.get_total_items()
    # For guest users, cart count might be handled by session, or always 0 if guest cart not implemented
    # Assuming guest cart is not the immediate priority, focusing on authenticated user first.
    return {'cart_items_count': count}
