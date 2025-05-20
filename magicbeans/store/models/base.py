# Файл для обратной совместимости
# Импортируем соответствующие модели из их модулей
from .administrators import Administrator
from .products import SeedBank, Strain

__all__ = [
    "Administrator",
    "SeedBank",
    "Strain",
] 