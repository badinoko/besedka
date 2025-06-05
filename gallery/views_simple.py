from django.views.generic import ListView
from .models import Photo


class SimpleGalleryView(ListView):
    """Упрощённое представление галереи без пагинации и лишнего функционала.
    Используется в местах, где нужен очень лёгкий вывод изображений (например, превью на главной).
    """
    model = Photo
    template_name = 'gallery/gallery_simple.html'
    context_object_name = 'photos'
    paginate_by = None  # отключаем пагинацию
