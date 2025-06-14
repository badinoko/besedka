from django.urls import path
from .views import (
    HomePageView,
    PostDetailView,
    CategoryPostListView,
    TagPostListView,
    search_posts,
    add_reaction,
    toggle_reaction,
    toggle_comment_reaction,
    add_comment,
    vote_in_poll,
    ajax_filter,
)

app_name = 'news'

urlpatterns = [
    # Главная страница (новостная лента)
    path('', HomePageView.as_view(), name='home'),

    # Детальная страница поста
    path('post/<slug:slug>/', PostDetailView.as_view(), name='post_detail'),

    # Посты по категории
    path('category/<slug:slug>/', CategoryPostListView.as_view(), name='category_posts'),

    # Посты по тегу
    path('tag/<slug:slug>/', TagPostListView.as_view(), name='tag_posts'),

    # Поиск
    path('search/', search_posts, name='search_posts'),

    # AJAX
    path('ajax/add-reaction/', add_reaction, name='add_reaction'),
    path('ajax/toggle-reaction/', toggle_reaction, name='toggle_reaction'),
    path('ajax/toggle-comment-reaction/', toggle_comment_reaction, name='toggle_comment_reaction'),
    path('ajax/add-comment/', add_comment, name='add_comment'),
    path('ajax/vote/', vote_in_poll, name='vote_in_poll'),
    path('ajax/filter/', ajax_filter, name='ajax_filter'),
]
