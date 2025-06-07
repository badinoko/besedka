from django.urls import path
from . import views
from .views_simple import SimpleGalleryView
from .views_debug import debug_gallery, test_gallery

app_name = 'gallery'

urlpatterns = [
    # Основные страницы
    path('', views.GalleryView.as_view(), name='gallery'),
    path('debug/', debug_gallery, name='debug'),
    path('test/', test_gallery, name='test'),
    path('my-photos/', views.MyPhotosView.as_view(), name='my_photos'),
    path('upload/', views.PhotoUploadView.as_view(), name='upload'),
    path('photo/<int:pk>/', views.PhotoDetailView.as_view(), name='photo_detail'),
    path('author/<str:username>/', views.AuthorPhotosView.as_view(), name='author_photos'),

    # Управление фото
    path('photo/<int:pk>/edit/', views.PhotoUpdateView.as_view(), name='photo_edit'),
    path('photo/<int:pk>/delete/', views.PhotoDeleteView.as_view(), name='photo_delete'),

        # Управление комментариями
    path('photo/<int:photo_pk>/comment/add/', views.PhotoCommentCreateView.as_view(), name='add_comment'),
    path('comment/<int:pk>/edit/', views.CommentUpdateView.as_view(), name='edit_comment'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='delete_comment'),

    # AJAX действия
    path('photo/<int:pk>/like/', views.toggle_like_photo, name='photo_like'),
    path('load-more/', views.load_more_photos, name='load_more'),

    # ТЕСТОВЫЕ ДАННЫЕ - только для разработки
    path('dev/create-test-data/', views.create_test_data_view, name='create_test_data'),
]
