import logging
from django.core.cache import cache
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from django.conf import settings # For User model if not using get_user_model directly

# Предполагается, что User модель настроена через AUTH_USER_MODEL в settings
from django.contrib.auth import get_user_model

# Импорт моделей из соответствующих приложений
# Если пути к моделям или имена полей отличаются, их нужно будет скорректировать
from growlogs.models import GrowLog
from gallery.models import Photo
# from chat.models import ChatMessage, ChatBan, ChatReport # Старый чат удален
from magicbeans_store.models import Order, StockItem # Убедитесь, что модель StockItem находится здесь

User = get_user_model()

logger = logging.getLogger(__name__)

class PlatformMonitor:
    """Мониторинг состояния платформы и магазина."""

    CACHE_TIMEOUT_STATS = 300 # 5 минут

    @staticmethod
    def get_platform_stats():
        """Статистика платформы (для владельца)."""
        cache_key = 'platform_overall_stats'
        stats = cache.get(cache_key)
        if not stats:
            try:
                active_today_threshold = timezone.now() - timedelta(days=1)
                stats = {
                    'users': {
                        'total': User.objects.count(),
                        'active_today': User.objects.filter(
                            last_login__gte=active_today_threshold
                        ).count(),
                        'by_role': list(User.objects.values('role').annotate(count=Count('id')).order_by('-count'))
                    },
                    'content': {
                        'growlogs_total': GrowLog.objects.count(),
                        'growlogs_public': GrowLog.objects.filter(is_public=True).count(),
                        'photos_total': Photo.objects.count(),
                        'photos_public': Photo.objects.filter(is_public=True).count(),
                    },
                    'moderation': {
                        # Статистика модерации будет добавлена позже с новым чатом
                    }
                }
                cache.set(cache_key, stats, PlatformMonitor.CACHE_TIMEOUT_STATS)
            except Exception as e:
                logger.error(f"Error calculating platform stats: {e}")
                stats = {} # Возвращаем пустой словарь в случае ошибки
        return stats

    @staticmethod
    def get_store_stats():
        """Статистика магазина (для владельца магазина)."""
        cache_key = 'store_overall_stats'
        stats = cache.get(cache_key)
        if not stats:
            try:
                today_date = timezone.now().date()
                month_ago_date = timezone.now() - timedelta(days=30)

                # Получаем статусы заказов
                try:
                    from magicbeans_store.models import OrderStatus
                    completed_statuses = OrderStatus.objects.filter(
                        name__in=['Доставлен', 'Завершен', 'Выполнен']
                    ).values_list('id', flat=True)
                    pending_statuses = OrderStatus.objects.filter(
                        name__in=['Новый', 'Обработка', 'Оплачен', 'Упакован']
                    ).values_list('id', flat=True)
                except Exception:
                    # Если модель OrderStatus недоступна, используем пустые списки
                    completed_statuses = []
                    pending_statuses = []

                stats = {
                    'sales': {
                        'today_revenue': Order.objects.filter(
                            created_at__date=today_date,
                            status__id__in=completed_statuses
                        ).aggregate(total=Sum('total_amount'))['total'] or 0,
                        'month_revenue': Order.objects.filter(
                            created_at__gte=month_ago_date,
                            status__id__in=completed_statuses
                        ).aggregate(total=Sum('total_amount'))['total'] or 0,
                        'today_orders_count': Order.objects.filter(created_at__date=today_date).count(),
                        'month_orders_count': Order.objects.filter(created_at__gte=month_ago_date).count(),
                    },
                    'inventory': {
                        'total_stock_items': StockItem.objects.filter(is_active=True).count(),
                        'low_stock_items': StockItem.objects.filter(is_active=True, quantity__lt=10).count(),
                        'out_of_stock_items': StockItem.objects.filter(is_active=True, quantity=0).count(),
                    },
                    'orders_status': {
                        'pending_processing': Order.objects.filter(status__id__in=pending_statuses).count(),
                        'shipped': Order.objects.filter(status__name__icontains='Отправлен').count(),
                        'completed': Order.objects.filter(status__id__in=completed_statuses).count(),
                        'cancelled': Order.objects.filter(status__name__icontains='Отменен').count(),
                    }
                }
                cache.set(cache_key, stats, PlatformMonitor.CACHE_TIMEOUT_STATS)
            except Exception as e:
                logger.error(f"Error calculating store stats: {e}")
                stats = {}
        return stats
