from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Photo, PhotoComment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden, Http404, HttpResponse
from django.db.models import Q, F, Count, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
import io
import random
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from .forms import PhotoUploadForm, PhotoCommentForm, PhotoSearchForm
from core.models import ActionLog
from users.models import Notification
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from core.view_mixins import UnifiedCardMixin
from core.base_views import UnifiedListView, unified_ajax_filter
from core.constants import COMMENTS_PAGE_SIZE, UNIFIED_PAGE_SIZE
from core.utils import get_limited_top_level_comments, get_total_comments_count

User = get_user_model()

# ==========================================================================
# ДИАГНОСТИЧЕСКАЯ ФУНКЦИЯ
# ==========================================================================
def debug_gallery(request):
    """Диагностика проблем с галереей."""
    try:
        photos = Photo.objects.all()[:5]
        photo_data = []
        for photo in photos:
            photo_data.append({
                'id': photo.id,
                'title': photo.title,
                'author': photo.author.username if photo.author else 'No author',
                'image': bool(photo.image),
                'is_public': photo.is_public,
                'is_active': photo.is_active,
            })

        return JsonResponse({
            'total_photos': Photo.objects.count(),
            'sample_photos': photo_data,
            'success': True
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        })

# ==========================================================================
# AJAX-ФИЛЬТР ГАЛЕРЕИ (УНИФИЦИРОВАННАЯ РЕАЛИЗАЦИЯ)
# ==========================================================================

@require_GET
def ajax_filter(request):
    """Универсальный AJAX-обработчик галереи через unified_ajax_filter."""
    return unified_ajax_filter(GalleryView)(request)

# ==========================================================================
# 1. ОСНОВНОЙ КЛАСС ОТОБРАЖЕНИЯ ГАЛЕРЕИ (УНИФИЦИРОВАН)
# ==========================================================================
class GalleryView(UnifiedListView):
    """
    Галерея фотографий - УНИФИЦИРОВАННАЯ ВЕРСИЯ
    """
    model = Photo
    template_name = 'base_list_page.html'
    # context_object_name наследуется из базового класса
    paginate_by = UNIFIED_PAGE_SIZE

    # УНИФИЦИРОВАННЫЕ НАСТРОЙКИ
    section_title = "Галерея сообщества"
    section_subtitle = "Самые яркие моменты жизни ваших растений"
    section_hero_class = "gallery-hero"
    card_type = "photo"

    def get_queryset(self):
        """Возвращает queryset с учётом выбранных фильтров.

        Ранее метод возвращал только базовый список фотографий без применения
        пользовательских фильтров/сортировки. Из-за этого кнопки фильтрации
        («Популярные», «Обсуждаемые», «Мои фото» и т.д.) не оказывали
        никакого влияния на выдачу. Теперь после формирования базового
        queryset-а мы НАВСЕГДА пропускаем его через self.apply_filters().
        """

        # Базовый queryset – только публичные активные фотографии
        queryset = (
            Photo.objects.filter(is_public=True, is_active=True)
            .exclude(image="")
            .exclude(image__isnull=True)
            .select_related("author", "growlog")
            .prefetch_related("likes", "comments")
        )

        # Применяем выбранные пользователем фильтры/сортировку
        return self.apply_filters(queryset)

    def apply_filters(self, queryset):
        """
        Применяет фильтрацию и сортировку для галереи в соответствии с
        параметрами запроса. Эта логика была перенесена из кастомного
        AJAX-обработчика для соответствия архитектуре UnifiedListView.
        """
        filter_type = self.request.GET.get('filter', 'newest')
        author_username = self.request.GET.get('author')

        # Фильтр по автору (для страницы "Все фото автора")
        if author_username:
            queryset = queryset.filter(author__username=author_username)

        # Фильтр "мои фото" или "приватные"
        elif filter_type in ['my_photos', 'private']:
            if not self.request.user.is_authenticated:
                return queryset.none()
            queryset = self.model.objects.filter(author=self.request.user, is_active=True)\
                .exclude(image='').exclude(image__isnull=True)\
                .select_related('author', 'growlog').prefetch_related('likes', 'comments')

            if filter_type == 'private':
                queryset = queryset.filter(is_public=False)

        # Сортировка для публичной галереи
        if filter_type == 'popular':
            return queryset.annotate(likes_count=Count('likes')).order_by('-likes_count', '-created_at')
        elif filter_type == 'commented':
            return queryset.annotate(comments_count=Count('comments')).order_by('-comments_count', '-created_at')
        elif filter_type == 'growlog':
            return queryset.filter(growlog__isnull=False).order_by('-created_at')
        else: # newest, my_photos, author_...
            return queryset.order_by('-created_at')

    def get_hero_stats(self):
        """Статистика для hero-секции"""
        return [
            {'value': Photo.objects.filter(is_public=True, is_active=True).count(), 'label': 'Фотографий'},
            {'value': Photo.objects.filter(is_public=True, is_active=True).values('author').distinct().count(), 'label': 'Авторов'},
            {'value': Photo.objects.filter(is_public=True, is_active=True).aggregate(total_likes=Count('likes'))['total_likes'] or 0, 'label': 'Лайков'},
        ]

    def get_hero_actions(self):
        """Кнопки действий для галереи"""
        if self.request.user.is_authenticated:
            return [
                {'url': reverse_lazy('gallery:upload'), 'label': 'Загрузить фото', 'is_primary': True, 'icon': 'fas fa-camera'},
                {'url': 'javascript:void(0);', 'label': 'Мои фото', 'is_primary': False, 'icon': 'fas fa-user', 'data_filter': 'my_photos', 'css_class': 'filter-tab-link'},
            ]
        else:
            return [
                {'url': reverse_lazy('account_login'), 'label': 'Войти', 'is_primary': True, 'icon': 'fas fa-sign-in-alt'},
            ]

    def get_filter_list(self):
        """Фильтры для галереи"""
        return [
            {'id': 'newest', 'label': 'Новые'},
            {'id': 'popular', 'label': 'Популярные'},
            {'id': 'commented', 'label': 'Обсуждаемые'},
            {'id': 'growlog', 'label': 'Из гроурепортов'},
        ]

# ==========================================================================
# 3. VIEWS ДЛЯ КОНКРЕТНОЙ ФОТОГРАФИИ И ДЕЙСТВИЙ (ЛОГИКА НЕ ИЗМЕНЕНА)
# ==========================================================================

class PhotoDetailView(DetailView):
    model = Photo
    template_name = 'gallery/photo_detail.html'
    context_object_name = 'photo'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_public and obj.author != self.request.user:
            raise Http404("Photo not found")

        # Инкрементируем счётчик просмотров не чаще одного раза за сессию,
        # чтобы предотвратить накрутку (аналогично GrowLogDetailView)
        if self.request.user != obj.author:
            viewed_key = f"viewed_photo_{obj.pk}"
            if not self.request.session.get(viewed_key, False):
                Photo.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
                obj.refresh_from_db(fields=['views_count'])
                self.request.session[viewed_key] = True

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_liked = False
        if self.request.user.is_authenticated:
            user_liked = self.object.likes.filter(id=self.request.user.id).exists()

        from core.utils import get_limited_top_level_comments
        from core.constants import COMMENTS_PAGE_SIZE

        selected, displayed_blocks, total_root = get_limited_top_level_comments(
            self.object,
            comment_relation="comments",
            block_limit=COMMENTS_PAGE_SIZE,
        )

        # Подсчитываем общее количество комментариев (root + replies)
        total_comments = get_total_comments_count(self.object)
        setattr(self.object, 'comments_count', total_comments)

        context.update({
            'comment_form': PhotoCommentForm(),
            'can_edit': self.object.author == self.request.user,
            'user_liked': user_liked,
            'top_level_comments': selected,
            'comments_count': total_comments,
            'has_more_comments': total_root > len(selected),
            'likes_count': self.object.likes.count(),
            'photo_id': self.object.id,
        })

        # Статистика для унифицированной hero-секции
        context['detail_hero_stats'] = [
            {'value': self.object.views_count or 0, 'label': 'просмотров', 'css_class': 'views'},
            {'value': total_comments, 'label': 'комментариев', 'css_class': 'comments'},
            {'value': self.object.likes.count(), 'label': 'лайков', 'css_class': 'likes'},
        ]

        return context

class PhotoUploadView(LoginRequiredMixin, CreateView):
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'gallery/photo_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Фотография успешно загружена!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('gallery:photo_detail', kwargs={'pk': self.object.pk})

class PhotoUpdateView(LoginRequiredMixin, UpdateView):
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'gallery/edit.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.author != self.request.user:
            raise Http404
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.success(self.request, 'Фотография обновлена!')
        return reverse('gallery:photo_detail', kwargs={'pk': self.object.pk})

class PhotoDeleteView(LoginRequiredMixin, DeleteView):
    model = Photo
    template_name = 'gallery/delete_confirm.html'
    success_url = reverse_lazy('gallery:gallery')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.author != self.request.user:
            raise Http404
        return obj

    def form_valid(self, form):
        self.object.is_active = False
        self.object.save()
        messages.success(self.request, 'Фотография удалена!')
        return redirect(self.success_url)

@login_required
@require_POST
def toggle_like_photo(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    photo = get_object_or_404(Photo, pk=pk)
    if photo.likes.filter(id=request.user.id).exists():
        return JsonResponse({'success': True, 'action': 'already_liked', 'likes_count': photo.likes.count()})
    else:
        photo.likes.add(request.user)
        if photo.author != request.user:
            Notification.objects.create(
                recipient=photo.author, sender=request.user, notification_type='like',
                title='Новый лайк', message=f'{request.user.username} лайкнул ваше фото "{photo.title}"'
            )
        return JsonResponse({'success': True, 'action': 'liked', 'likes_count': photo.likes.count()})

@login_required
@require_POST
def add_photo_comment(request, pk):
    """Добавление комментария или ответа к фотографии (AJAX/обычный POST)."""
    photo = get_object_or_404(Photo, pk=pk)

    if request.method == 'POST':
        parent_id = request.POST.get('parent_id')
        form = PhotoCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.photo = photo
            comment.author = request.user

            if parent_id:
                try:
                    parent_comment = PhotoComment.objects.get(pk=parent_id, photo=photo)

                    # Ограничиваем глубину вложенности до 3 уровней
                    # Блокируем, если у родительского комментария уже два предка (глубина 2)
                    if parent_comment.parent is not None and parent_comment.parent.parent is not None:
                        return JsonResponse({'success': False, 'message': 'Достигнут максимальный уровень вложенности комментариев.'}, status=400)

                    comment.parent = parent_comment
                except PhotoComment.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Родительский комментарий не найден.'}, status=404)

            comment.save()

            # Если запрос AJAX – возвращаем обновлённый HTML
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                comments_html = render_to_string(
                    'includes/partials/unified_comments_list.html',
                    {
                        'photo': photo,
                        'top_level_comments': photo.comments.filter(parent__isnull=True)
                                                         .select_related('author')
                                                         .prefetch_related('replies__author')
                                                         .order_by('-created_at'),
                    },
                    request=request
                )
                from core.utils import get_total_comments_count
                return JsonResponse({
                    'success': True,
                    'comments_html': comments_html,
                    'comment_id': comment.id,
                    'comments_count': get_total_comments_count(photo),
                })

            return redirect(photo.get_absolute_url())

    # Если форма недействительна или GET
    return redirect(photo.get_absolute_url())
