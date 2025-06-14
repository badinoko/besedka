from django.urls import path
from . import views

app_name = 'gallery'

urlpatterns = [
    # Диагностика
    path('debug/', views.debug_gallery, name='debug'),

    # Основные страницы
    path('', views.GalleryView.as_view(), name='gallery'),
    path('upload/', views.PhotoUploadView.as_view(), name='upload'),
    path('photo/<int:pk>/', views.PhotoDetailView.as_view(), name='photo_detail'),

    # Управление фото
    path('photo/<int:pk>/edit/', views.PhotoUpdateView.as_view(), name='photo_edit'),
    path('photo/<int:pk>/delete/', views.PhotoDeleteView.as_view(), name='delete'),

    # AJAX действия
    path('ajax/filter/', views.ajax_filter, name='ajax_filter'),
    path('photo/<int:pk>/like/', views.toggle_like_photo, name='toggle_like'),

    # Комментарии
    path('photo/<int:pk>/comment/', views.add_photo_comment, name='add_comment'),
]
