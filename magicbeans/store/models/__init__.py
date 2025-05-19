# Файл с заглушкой для папки моделей
# В данной реализации мы используем один файл models.py для всех моделей
# Оставляем пустым для избежания циклических импортовм все модели из основного файла models.py для обратной совместимости
# с кодом, который ожидает импортировать из magicbeans.store.models
from magicbeans.store.models import (
    Administrator, SeedBank, Strain, StrainImage,
    StockItem, StockMovement, Order, OrderItem, ActionLog
)

# Определяем список экспортируемых имен - все, что есть в основном файле models.py
__all__ = [
    "ActionLog", "Administrator", "Order", "OrderItem", "SeedBank",
    "StockItem", "StockMovement", "Strain", "StrainImage",
]
