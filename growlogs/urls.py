from django.urls import path
from . import views
from .views_debug import debug_growlogs, test_growlogs

app_name = 'growlogs'

urlpatterns = [
    # Основные страницы
    path('', views.GrowLogListView.as_view(), name='list'),
    path('debug/', debug_growlogs, name='debug'),
    path('test/', test_growlogs, name='test'),
    path('my-logs/', views.MyGrowLogsView.as_view(), name='my_logs'),
    path('create/', views.GrowLogCreateView.as_view(), name='create'),
    path('<int:pk>/', views.GrowLogDetailView.as_view(), name='detail'),

    # Редактирование
    path('<int:pk>/edit/', views.GrowLogUpdateView.as_view(), name='edit'),

    # Управление записями
    path('<int:growlog_pk>/add-entry/', views.GrowLogEntryCreateView.as_view(), name='entry_create'),
    path('entry/<int:pk>/edit/', views.GrowLogEntryUpdateView.as_view(), name='entry_edit'),

    # AJAX действия
    path('<int:pk>/like/', views.toggle_like_growlog, name='toggle_like'),
    path('entry/<int:entry_id>/like/', views.toggle_entry_like, name='toggle_entry_like'),
    path('entry/<int:entry_id>/comment/', views.add_entry_comment, name='add_entry_comment'),

    # Комментарии
    path('<int:growlog_pk>/comment/', views.GrowLogCommentCreateView.as_view(), name='comment_create'),
]
