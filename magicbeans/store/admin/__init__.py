"""
Модуль инициализации административных интерфейсов.
Регистрирует все административные классы для моделей магазина.
"""
from django.contrib import admin
import sys
import os

# Используем абсолютный импорт из файла models.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Administrator, SeedBank, Strain, StrainImage, StockItem, StockMovement, Order, OrderItem, ActionLog

# Импортируем административные классы
from magicbeans.store.admin.administrators import AdministratorAdmin
from magicbeans.store.admin.stock_admin import StockItemAdmin, StockMovementAdmin

# Регистрируем все административные классы
admin.site.register(Administrator, AdministratorAdmin)
admin.site.register(StockItem, StockItemAdmin)
admin.site.register(StockMovement, StockMovementAdmin)

# Для моделей, у которых нет специализированных административных классов
# можно использовать стандартную регистрацию:
admin.site.register(SeedBank)
admin.site.register(Strain)
admin.site.register(StrainImage)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ActionLog)

# Определяем список экспортируемых имен
__all__ = []
