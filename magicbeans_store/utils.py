from .models import Cart

def get_cart(request):
    """
    Получает или создает корзину для текущего пользователя (если аутентифицирован)
    или для текущей сессии (если гость). Гарантированно возвращает сохраненную корзину.
    """
    cart = None
    cart_created = False

    if request.user.is_authenticated:
        cart, cart_created = Cart.objects.get_or_create(user=request.user)
        # Если корзина пользователя была только что создана, и у него была сессионная корзина,
        # то сигнал user_logged_in должен был позаботиться о слиянии.
        # Здесь дополнительно можно проверить, есть ли у пользователя session_key от предыдущей сессии
        # и попытаться найти и объединить/удалить старую гостевую корзину, но это усложнение.
        # Пока основной механизм слияния - через сигнал user_logged_in.
    else:
        session_key = request.session.session_key
        if not session_key:
            # Если ключа сессии нет, Django создаст его при первом изменении сессии.
            # Мы можем вызвать request.session.save() или request.session.create() для его генерации.
            request.session.create() # Гарантирует создание session_key
            session_key = request.session.session_key

        # Пытаемся найти гостевую корзину, привязанную к этой сессии
        cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()

        if not cart:
            # Если не найдена, создаем новую И СОХРАНЯЕМ ЕЕ
            cart = Cart.objects.create(session_key=session_key, user=None)
            cart_created = True
        # Если cart существует, он уже имеет pk.
        # Если cart.session_key не совпадает (маловероятно после filter), можно обновить и сохранить.
        # Но основная проблема была в том, что несохраненная корзина использовалась.
        # create() уже сохраняет.

    return cart, cart_created
