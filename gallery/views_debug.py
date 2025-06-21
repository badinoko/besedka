from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from .models import Photo


def debug_gallery(request):
    """Простое отладочное представление галереи."""
    try:
        photos = Photo.objects.all()[:8]  # показываем несколько снимков для быстрой проверки
        return render(request, 'gallery/gallery_debug.html', {'photos': photos})
    except Exception as exc:
        return HttpResponse(f"Ошибка: {exc}")


def test_gallery(request):
    """Тестовое представление, подтверждающее работоспособность маршрутов галереи."""
    return HttpResponse("Gallery работает!")
