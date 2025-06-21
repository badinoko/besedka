"""
Сериализаторы для API Telegram-бота
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from magicbeans_store.models import (
    SeedBank, Strain, StockItem, Order, OrderItem,
    ShippingMethod, PaymentMethod, Promotion, Coupon
)

User = get_user_model()


class SeedBankSerializer(serializers.ModelSerializer):
    """Сериализатор для сидбанков (категорий)"""

    class Meta:
        model = SeedBank
        fields = ['id', 'name', 'slug', 'description', 'logo', 'is_active']


class StrainSerializer(serializers.ModelSerializer):
    """Сериализатор для сортов (товаров)"""
    seedbank = SeedBankSerializer(read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)
    min_price = serializers.DecimalField(source='get_min_price', max_digits=10, decimal_places=2, read_only=True)
    has_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Strain
        fields = [
            'id', 'name', 'description', 'seedbank', 'strain_type',
            'genetics', 'thc_content', 'cbd_content', 'flowering_time',
            'height', 'yield_indoor', 'yield_outdoor', 'effect', 'flavor',
            'image_url', 'min_price', 'has_stock', 'is_active',
            'created_at', 'updated_at'
        ]


class StrainListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка сортов"""
    seedbank_name = serializers.CharField(source='seedbank.name', read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)
    min_price = serializers.DecimalField(source='get_min_price', max_digits=10, decimal_places=2, read_only=True)
    has_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Strain
        fields = [
            'id', 'name', 'strain_type', 'min_price', 'has_stock',
            'image_url', 'seedbank_name', 'thc_content', 'cbd_content'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей"""

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'telegram_id', 'role']
        read_only_fields = ['id', 'role']


class StockItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товаров на складе"""
    strain = StrainListSerializer(read_only=True)

    class Meta:
        model = StockItem
        fields = ['id', 'strain', 'seeds_count', 'price', 'quantity', 'sku', 'is_active']


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций заказа"""
    stock_item = StockItemSerializer(read_only=True)
    stock_item_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'stock_item', 'stock_item_id', 'quantity', 'price', 'total']


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказов"""
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'total_amount', 'shipping_address',
            'guest_phone_number', 'guest_email', 'comment', 'created_at', 'updated_at',
            'shipping_method', 'payment_method', 'items'
        ]
        read_only_fields = ['id', 'user', 'total_amount', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказов"""
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        write_only=True
    )

    class Meta:
        model = Order
        fields = [
            'shipping_address', 'guest_phone_number', 'guest_email', 'comment',
            'shipping_method', 'payment_method', 'items'
        ]

    def validate_items(self, value):
        """Валидация позиций заказа"""
        if not value:
            raise serializers.ValidationError("Заказ должен содержать хотя бы одну позицию")

        for item in value:
            if 'stock_item_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError("Каждая позиция должна содержать stock_item_id и quantity")

            try:
                stock_item_id = int(item['stock_item_id'])
                quantity = int(item['quantity'])
            except (ValueError, TypeError):
                raise serializers.ValidationError("stock_item_id и quantity должны быть числами")

            if quantity <= 0:
                raise serializers.ValidationError("Количество должно быть больше 0")

            # Проверяем существование товара
            try:
                stock_item = StockItem.objects.get(id=stock_item_id, is_active=True)
                if stock_item.quantity < quantity:
                    raise serializers.ValidationError(f"Недостаточно товара {stock_item} на складе")
            except StockItem.DoesNotExist:
                raise serializers.ValidationError(f"Товар с ID {stock_item_id} не найден или недоступен")

        return value

    def create(self, validated_data):
        """Создание заказа с позициями"""
        items_data = validated_data.pop('items')
        user = self.context['request'].user

        # Создаем заказ
        order = Order.objects.create(user=user, **validated_data)

        # Создаем позиции заказа
        total_amount = 0
        for item_data in items_data:
            stock_item = StockItem.objects.get(id=item_data['stock_item_id'])
            quantity = int(item_data['quantity'])
            price = stock_item.price

            order_item = OrderItem.objects.create(
                order=order,
                stock_item=stock_item,
                quantity=quantity,
                price=price
            )

            total_amount += order_item.total

        # Обновляем общую сумму заказа
        order.total_amount = total_amount
        order.save()

        return order


class ShippingMethodSerializer(serializers.ModelSerializer):
    """Сериализатор для способов доставки"""

    class Meta:
        model = ShippingMethod
        fields = ['id', 'name', 'description', 'price', 'is_active']


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Сериализатор для способов оплаты"""

    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'description', 'is_active']


class PromotionSerializer(serializers.ModelSerializer):
    """Сериализатор для промоакций"""

    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'discount_type', 'discount_value',
            'start_date', 'end_date', 'is_active'
        ]


class CouponSerializer(serializers.ModelSerializer):
    """Сериализатор для купонов"""

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'discount_percentage',
            'min_order_amount', 'max_uses', 'uses_count',
            'start_date', 'end_date', 'is_active'
        ]


class TelegramAuthSerializer(serializers.Serializer):
    """Сериализатор для аутентификации через Telegram"""
    telegram_id = serializers.CharField()
    username = serializers.CharField(required=False)
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False)
    auth_date = serializers.IntegerField()
    hash = serializers.CharField()

    def validate(self, attrs):
        """Валидация данных от Telegram"""
        import hashlib
        import hmac
        import time
        from django.conf import settings

        # Проверяем актуальность данных (не старше 24 часов)
        auth_date = attrs.get('auth_date', 0)
        if time.time() - auth_date > 86400:
            raise serializers.ValidationError("Данные аутентификации устарели")

        # Проверяем подлинность данных
        telegram_hash = attrs.pop('hash')
        data_check_list = []
        for key, value in sorted(attrs.items()):
            if key != 'hash':
                data_check_list.append(f"{key}={value}")
        data_check_string = '\n'.join(data_check_list)

        secret_key = hashlib.sha256(settings.API_TELEGRAM_BOT_TOKEN.encode()).digest()
        check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if telegram_hash != check_hash:
            raise serializers.ValidationError("Неверная подпись данных")

        return attrs
