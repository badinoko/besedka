"""
Инициализация моделей магазина.
Импортируем все модели для удобного доступа через magicbeans.store.models
"""
from magicbeans.store.models.administrators import Administrator
from magicbeans.store.models.products import SeedBank, Strain, StrainImage
from magicbeans.store.models.stock import StockItem, StockMovement
from magicbeans.store.models.orders import Order, OrderItem

__all__ = [
    'Administrator',
    'SeedBank',
    'Strain',
    'StrainImage',
    'StockItem',
    'StockMovement',
    'Order',
    'OrderItem',
]
