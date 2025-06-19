"""
API Views для Telegram-бота
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes

from magicbeans_store.models import (
    SeedBank, Strain, Order, OrderItem,
    ShippingMethod, PaymentMethod, Promotion, Coupon
)
from .serializers import (
    SeedBankSerializer, StrainSerializer, StrainListSerializer,
    OrderSerializer, OrderCreateSerializer, UserSerializer,
    ShippingMethodSerializer, PaymentMethodSerializer,
    PromotionSerializer, CouponSerializer, TelegramAuthSerializer
)

User = get_user_model()


class TelegramAuthView(APIView):
    """
    Аутентификация пользователя через Telegram
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=TelegramAuthSerializer,
        responses={200: UserSerializer},
        description="Аутентификация пользователя через Telegram данные"
    )
    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        if serializer.is_valid():
            telegram_data = serializer.validated_data
            telegram_id = telegram_data['telegram_id']

            # Находим или создаем пользователя
            try:
                user = User.objects.get(telegram_id=telegram_id)
                created = False
            except User.DoesNotExist:
                # Создаем нового пользователя
                username = telegram_data.get('username')
                if not username:
                    username = f"{telegram_data['first_name']}_{telegram_id}"

                # Проверяем уникальность username
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{telegram_id[-4:]}"

                # Формируем имя
                first_name = telegram_data['first_name']
                last_name = telegram_data.get('last_name', '')
                name = f"{first_name} {last_name}".strip() if last_name else first_name

                user = User.objects.create(
                    telegram_id=telegram_id,
                    username=username,
                    name=name,
                    role='user'
                )
                created = True

            # Генерируем JWT токены
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'user': UserSerializer(user).data,
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'created': created
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SeedBankListView(generics.ListAPIView):
    """
    Список сидбанков (категорий товаров)
    """
    queryset = SeedBank.objects.filter(is_active=True)
    serializer_class = SeedBankSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        description="Получить список всех активных сидбанков"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class StrainListView(generics.ListAPIView):
    """
    Список сортов (товаров)
    """
    serializer_class = StrainListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Strain.objects.filter(is_active=True)

        # Фильтрация по сидбанку
        seedbank_id = self.request.query_params.get('seedbank')
        if seedbank_id:
            queryset = queryset.filter(seedbank_id=seedbank_id)

        # Фильтрация по наличию
        in_stock = self.request.query_params.get('in_stock')
        if in_stock == 'true':
            queryset = [strain for strain in queryset if strain.has_stock]

        # Фильтрация по типу
        strain_type = self.request.query_params.get('strain_type')
        if strain_type:
            queryset = queryset.filter(strain_type=strain_type)

        return queryset.order_by('seedbank__name', 'name')

    @extend_schema(
        parameters=[
            OpenApiParameter('seedbank', OpenApiTypes.INT, description='ID сидбанка'),
            OpenApiParameter('in_stock', OpenApiTypes.BOOL, description='Только товары в наличии'),
            OpenApiParameter('strain_type', OpenApiTypes.STR, description='Тип сорта (regular, feminized, autoflowering)'),
        ],
        description="Получить список сортов с возможностью фильтрации"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class StrainDetailView(generics.RetrieveAPIView):
    """
    Детальная информация о сорте
    """
    queryset = Strain.objects.filter(is_active=True)
    serializer_class = StrainSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    @extend_schema(
        description="Получить детальную информацию о сорте по ID"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OrderCreateView(generics.CreateAPIView):
    """
    Создание нового заказа
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Создать новый заказ",
        request=OrderCreateSerializer,
        responses={201: OrderSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(generics.RetrieveAPIView):
    """
    Детальная информация о заказе
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Пользователь может видеть только свои заказы
        return Order.objects.filter(user=self.request.user)

    @extend_schema(
        description="Получить детальную информацию о заказе"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserOrdersView(generics.ListAPIView):
    """
    Список заказов пользователя
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    @extend_schema(
        description="Получить список заказов текущего пользователя"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ShippingMethodsView(generics.ListAPIView):
    """
    Список способов доставки
    """
    queryset = ShippingMethod.objects.filter(is_active=True)
    serializer_class = ShippingMethodSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        description="Получить список доступных способов доставки"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PaymentMethodsView(generics.ListAPIView):
    """
    Список способов оплаты
    """
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        description="Получить список доступных способов оплаты"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RocketOAuthExchangeView(APIView):
    """Endpoint for Rocket.Chat SSO OAuth token exchange.\n    Returns JWT access token and userId accepted by Rocket.Chat Custom OAuth."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        return Response({
            "accessToken": str(access_token),
            "userId": user.id,
            "token_type": "Bearer",
            "expires_in": access_token.lifetime.total_seconds(),
        })


class RocketChatIdentityView(APIView):
    """
    Identity endpoint для Rocket.Chat Custom OAuth
    Возвращает информацию о пользователе для создания/авторизации в Rocket.Chat
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": str(user.id),
            "username": user.username,
            "email": user.email if user.email else f"{user.username}@besedka.local",
            "name": getattr(user, 'name', user.username),
            "role": user.role,
            "avatar": getattr(user, 'avatar_url', ''),
            "verified": True,
            "active": True
        })


class PromotionsView(generics.ListAPIView):
    """
    Список активных промоакций
    """
    serializer_class = PromotionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        from django.utils import timezone
        return Promotion.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )

    @extend_schema(
        description="Получить список активных промоакций"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema(
    parameters=[
        OpenApiParameter('code', OpenApiTypes.STR, description='Код купона'),
    ],
    responses={200: CouponSerializer},
    description="Проверить валидность купона"
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def validate_coupon(request):
    """
    Проверка валидности купона
    """
    code = request.query_params.get('code')
    if not code:
        return Response(
            {'error': 'Код купона не указан'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from django.utils import timezone
        coupon = Coupon.objects.get(
            code=code,
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )

        # Проверяем лимит использования
        if coupon.max_uses and coupon.uses_count >= coupon.max_uses:
            return Response(
                {'error': 'Купон исчерпан'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(CouponSerializer(coupon).data)

    except Coupon.DoesNotExist:
        return Response(
            {'error': 'Купон не найден или недействителен'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    description="Получить информацию о текущем пользователе"
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """
    Информация о текущем пользователе
    """
    return Response(UserSerializer(request.user).data)


@extend_schema(
    description="Проверить статус API"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_status(request):
    """
    Статус API
    """
    return Response({
        'status': 'ok',
        'version': '1.0.0',
        'message': 'Беседка API работает'
    })
