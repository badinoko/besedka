from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    # Главная страница (новостная лента)
    path('', views.HomePageView.as_view(), name='home'),

    # Детальная страница поста
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),

    # Посты по категории
    path('category/<slug:slug>/', views.CategoryPostListView.as_view(), name='category_posts'),

    # Посты по тегу
    path('tag/<slug:slug>/', views.TagPostListView.as_view(), name='tag_posts'),

    # AJAX-эндпоинты
    path('ajax/reaction/', views.add_reaction, name='add_reaction'),
    path('ajax/toggle-reaction/', views.toggle_reaction, name='toggle_reaction'),
    path('ajax/toggle-comment-reaction/', views.toggle_comment_reaction, name='toggle_comment_reaction'),
    path('ajax/add-comment/', views.add_comment, name='add_comment'),
    path('ajax/poll-vote/', views.vote_in_poll, name='vote_in_poll'),
    path('ajax/filter-news/', views.filter_news_ajax, name='filter_news_ajax'),

    # Поиск
    path('search/', views.search_posts, name='search'),
]
