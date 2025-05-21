from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

from magicbeans.store.models import (
    Order, OrderItem, StockItem, StockMovement, SeedBank, Strain
)


@staff_member_required
def statistics_view(request):
    """
    Отображение статистики магазина, доступно только владельцам
    """
    # Если пользователь не владелец, перенаправляем на админку
    if not request.user.groups.filter(name="Владельцы").exists() and not request.user.is_superuser:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "У вас нет доступа к статистике магазина")
        return redirect('admin:index')

    # Период для статистики (по умолчанию за 30 дней)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Статистика заказов
    orders_stats = {
        'total_count': Order.objects.count(),
        'period_count': Order.objects.filter(created_at__gte=start_date).count(),
        'total_revenue': Order.objects.aggregate(total=Sum('total'))['total'] or 0,
        'period_revenue': Order.objects.filter(created_at__gte=start_date).aggregate(total=Sum('total'))['total'] or 0,
        'avg_order_value': Order.objects.aggregate(avg=Avg('total'))['avg'] or 0,
    }

    # Статистика сортов
    top_strains = OrderItem.objects.values('strain_name') \
                  .annotate(total_sales=Sum('quantity')) \
                  .order_by('-total_sales')[:10]

    # Статистика сидбанков
    top_seedbanks = SeedBank.objects.annotate(
        strains_count=Count('strains'),
        items_count=Count('strains__stock_items')
    ).order_by('-strains_count')[:10]

    # Статистика склада
    stock_stats = {
        'total_items': StockItem.objects.count(),
        'items_in_stock': StockItem.objects.filter(quantity__gt=0).count(),
        'out_of_stock': StockItem.objects.filter(quantity=0).count(),
        'total_quantity': StockItem.objects.aggregate(total=Sum('quantity'))['total'] or 0,
        'recent_movements': StockMovement.objects.order_by('-timestamp')[:10]
    }

    context = {
        'orders_stats': orders_stats,
        'top_strains': top_strains,
        'top_seedbanks': top_seedbanks,
        'stock_stats': stock_stats,
        'title': f'Статистика за последние {days} дней',
        'days': days,
    }

    return render(request, 'admin/store/statistics.html', context)
