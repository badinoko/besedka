"""
Константы проекта "Беседка"
"""

# Унифицированный размер страницы для пагинации
UNIFIED_PAGE_SIZE = 12

# Максимальный размер загружаемых изображений (в байтах)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# Таймауты для различных операций (в секундах)
CACHE_TIMEOUT = 60 * 15  # 15 минут
SESSION_TIMEOUT = 60 * 60 * 24  # 24 часа

# Лимиты для пользователей
MAX_GROWLOGS_PER_USER = 100
MAX_PHOTOS_PER_USER = 1000
MAX_COMMENTS_PER_DAY = 50

# Статусы для гроу-репортов
GROWLOG_STATUS_CHOICES = [
    ('active', 'Активный'),
    ('completed', 'Завершен'),
    ('paused', 'Приостановлен'),
    ('cancelled', 'Отменен'),
]

# Типы уведомлений
NOTIFICATION_TYPES = [
    ('like', 'Лайк'),
    ('comment', 'Комментарий'),
    ('follow', 'Подписка'),
    ('mention', 'Упоминание'),
    ('system', 'Системное'),
]

COMMENTS_PAGE_SIZE = 20
