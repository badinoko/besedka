from django.shortcuts import render
from django.http import HttpResponse
from .models import GrowLog

def debug_growlogs(request):
    """Отладочное представление growlogs"""
    try:
        growlogs = GrowLog.objects.all()[:5]  # Берем только 5 growlogs для отладки
        return render(request, 'growlogs/growlogs_debug.html', {'growlogs': growlogs})
    except Exception as e:
        return HttpResponse(f"Ошибка: {str(e)}")

def test_growlogs(request):
    """Тестовое представление"""
    return HttpResponse("Growlogs работает!")
