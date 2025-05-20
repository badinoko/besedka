# Файл с заглушкой для папки моделей
# В данной реализации мы используем один файл models.py для всех моделей
# Оставляем пустым для избежания циклических импортовм все модели из основного файла models.py для обратной совместимости
# с кодом, который ожидает импортировать из magicbeans.store.models
from .administrators import Administrator
from .products import SeedBank, Strain, StrainImage
from .stock import StockItem, StockMovement
from .orders import Order, OrderItem
from .logs import ActionLog

# Определяем список экспортируемых имен - все, что есть в основном файле models.py
__all__ = [
    "Administrator",
    "SeedBank",
    "Strain",
    "StrainImage",
    "StockItem",
    "StockMovement",
    "Order",
    "OrderItem",
    "ActionLog",
]
