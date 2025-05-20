"""
Модуль инициализации административных интерфейсов.
Импортирует административные классы и модели для использования в StoreAdminSite.
"""
from django.contrib import admin

# Импортируем модели через правильный путь
from magicbeans.store.models import (
    Administrator, SeedBank, Strain, StrainImage, 
    StockItem, StockMovement, Order, OrderItem, ActionLog
)

# Импортируем административные классы для их обнаружения Django
from magicbeans.store.admin.administrators import AdministratorAdmin
from magicbeans.store.admin.stock_admin import StockItemAdmin, StockMovementAdmin

# Административные классы будут автоматически зарегистрированы через StoreAdminSite в apps.py

# Определяем список экспортируемых имен
__all__ = [
    'Administrator', 'SeedBank', 'Strain', 'StrainImage',
    'StockItem', 'StockMovement', 'Order', 'OrderItem', 'ActionLog',
    'AdministratorAdmin', 'StockItemAdmin', 'StockMovementAdmin'
]
