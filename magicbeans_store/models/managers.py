from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()

class StoreDataManager(models.Manager):
    """Менеджер для изоляции данных магазина"""

    def for_user(self, user):
        """Возвращает данные доступные пользователю"""
        if not user or not user.is_authenticated:
            # Неавторизованные пользователи видят только публичные активные данные
            return self.filter(is_active=True)

        # Проверяем роль пользователя
        user_role = getattr(user, 'role', 'user')

        if user_role in ['store_owner', 'store_admin']:
            # Полный доступ для управления магазином
            return self.all()

        elif user_role in ['owner', 'admin']:
            # Владелец платформы и модераторы видят только публичные данные
            # НЕ имеют доступа к критическим данным магазина
            return self.filter(is_active=True)

        # Остальные пользователи видят только публичные активные данные
        return self.filter(is_active=True)

    def public_data(self):
        """Публичные данные для всех"""
        return self.filter(is_active=True)

    def critical_data(self):
        """Критические данные - только для владельца и админов магазина"""
        # Этот метод используется с дополнительной проверкой в view'ах
        return self.all()

class OrderManager(StoreDataManager):
    """Специальный менеджер для заказов с повышенной безопасностью"""

    def for_user(self, user):
        """Заказы доступные пользователю"""
        if not user or not user.is_authenticated:
            return self.none()

        user_role = getattr(user, 'role', 'user')

        if user_role in ['store_owner', 'store_admin']:
            return self.all()

        elif user_role == 'user':
            qs = self.filter(user=user)
            return qs

        else:
            return self.none()

    def user_orders(self, user):
        """Заказы конкретного пользователя"""
        return self.filter(user=user).order_by('-created_at')

    def pending_orders(self):
        """Заказы ожидающие обработки (только для персонала магазина)"""
        return self.filter(status__name__in=['Новый', 'Ожидает оплаты', 'Оплачен'])

class StrainManager(StoreDataManager):
    """Менеджер для сортов с фильтрацией"""

    def available_for_order(self):
        """Сорта доступные для заказа"""
        return self.filter(
            is_active=True,
            stock_items__quantity__gt=0,
            stock_items__is_active=True
        ).distinct()

    def by_seedbank(self, seedbank_slug):
        """Сорта конкретного сидбанка"""
        return self.filter(seedbank__slug=seedbank_slug, is_active=True)

    def search(self, query):
        """Поиск по сортам"""
        if not query:
            return self.public_data()

        return self.filter(
            Q(name__icontains=query) |
            Q(genetics__icontains=query) |
            Q(description__icontains=query) |
            Q(effect__icontains=query) |
            Q(flavor__icontains=query),
            is_active=True
        )

class CartManager(models.Manager):
    """Менеджер для корзин пользователей"""

    def get_or_create_for_user(self, user):
        """Получить или создать корзину для пользователя"""
        if not user.is_authenticated:
            return None, False

        return self.get_or_create(user=user)

    def active_carts(self):
        """Активные корзины (с товарами)"""
        return self.filter(items__isnull=False).distinct()
