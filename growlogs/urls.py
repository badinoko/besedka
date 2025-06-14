from django.urls import path
from . import views

app_name = 'growlogs'

urlpatterns = [
    # Основные страницы
    path('', views.GrowLogListView.as_view(), name='list'),
    path('create/', views.GrowLogCreateView.as_view(), name='create'),
    path('<int:pk>/', views.GrowLogDetailView.as_view(), name='detail'),

    # Редактирование
    path('<int:pk>/edit/', views.GrowLogUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.GrowLogDeleteView.as_view(), name='delete'),

    # AJAX
    path('ajax/filter/', views.ajax_filter, name='ajax_filter'),
    path('ajax/<int:pk>/like/', views.toggle_like_growlog, name='toggle_like'),
    path('ajax/<int:pk>/comment/', views.add_growlog_comment, name='add_comment'),
]
