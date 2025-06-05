from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Photo
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.db.models import Q, F, Count, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from .forms import PhotoUploadForm, PhotoCommentForm, PhotoSearchForm
from core.models import ActionLog
from users.models import Notification

def photo_list(request):
    """Display list of photos."""
    photos = Photo.objects.filter(is_public=True).select_related('author')
    return render(request, "gallery/list.html", {"photos": photos})

def photo_detail(request, pk):
    """Display photo details."""
    photo = get_object_or_404(Photo, pk=pk)
    if not photo.is_public and photo.author != request.user:
        messages.error(request, _("You don't have permission to view this photo."))
        return redirect("gallery:list")
    comments = photo.comments.all().select_related('author')
    return render(request, "gallery/detail.html", {
        "photo": photo,
        "comments": comments
    })

@login_required
def photo_upload(request):
    """Upload new photo."""
    # Placeholder for form handling
    return render(request, "gallery/upload.html")

class GalleryView(ListView):
    """Галерея с Masonry раскладкой"""
    model = Photo
    template_name = 'gallery/gallery.html'
    context_object_name = 'photos'
    paginate_by = 24

    def get_queryset(self):
        queryset = Photo.objects.filter(is_public=True, is_active=True)

        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(author__username__icontains=search) |
                Q(growlog__title__icontains=search)
            )

        # Фильтры
        author = self.request.GET.get('author')
        if author:
            queryset = queryset.filter(author__username__icontains=author)

        growlog = self.request.GET.get('growlog')
        if growlog:
            queryset = queryset.filter(growlog__isnull=False)

        # Сортировка
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by == 'popular':
            queryset = queryset.annotate(likes_count=Count('likes')).order_by('-likes_count', '-created_at')
        elif sort_by == 'commented':
            queryset = queryset.annotate(comments_count=Count('comments')).order_by('-comments_count', '-created_at')
        else:
            queryset = queryset.order_by(sort_by)

        return queryset.select_related('author', 'growlog').prefetch_related('likes', 'comments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавляем информацию о лайках для текущего пользователя
        if self.request.user.is_authenticated:
            liked_photos = self.request.user.liked_photos.values_list('id', flat=True)
            context['liked_photos'] = list(liked_photos)
        else:
            context['liked_photos'] = []

        # Форма поиска
        context['search_form'] = PhotoSearchForm(self.request.GET or None)
        context['search_query'] = self.request.GET.get('search', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')

        return context

class MyPhotosView(LoginRequiredMixin, ListView):
    """Мои фотографии"""
    model = Photo
    template_name = 'gallery/my_photos.html'
    context_object_name = 'photos'
    paginate_by = 20

    def get_queryset(self):
        return Photo.objects.filter(author=self.request.user).order_by('-created_at')

class PhotoDetailView(DetailView):
    """Просмотр фото с комментариями"""
    model = Photo
    template_name = 'gallery/photo_detail.html'
    context_object_name = 'photo'

    def get_object(self):
        obj = super().get_object()

        # Проверяем доступ
        if not obj.is_public and obj.author != self.request.user:
            raise Http404("Photo not found")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Комментарии с пагинацией
        comments = self.object.comments.select_related('author').order_by('created_at')
        paginator = Paginator(comments, 10)
        page = self.request.GET.get('page')

        try:
            comments_page = paginator.page(page)
        except PageNotAnInteger:
            comments_page = paginator.page(1)
        except EmptyPage:
            comments_page = paginator.page(paginator.num_pages)

        # Проверяем лайк пользователя
        user_liked = False
        if self.request.user.is_authenticated:
            user_liked = self.object.likes.filter(id=self.request.user.id).exists()

        # Похожие фото (из того же гроу-лога или от того же автора)
        similar_photos = Photo.objects.filter(
            Q(growlog=self.object.growlog) | Q(author=self.object.author),
            is_public=True,
            is_active=True
        ).exclude(id=self.object.id)[:6]

        context.update({
            'comments': comments_page,
            'comment_form': PhotoCommentForm(),
            'can_edit': self.object.author == self.request.user,
            'user_liked': user_liked,
            'likes_count': self.object.likes.count(),
            'comments_count': self.object.comments.count(),
            'similar_photos': similar_photos,
        })
        return context

    def post(self, request, *args, **kwargs):
        """Обработка добавления комментария"""
        self.object = self.get_object()
        form = PhotoCommentForm(request.POST)

        if form.is_valid() and request.user.is_authenticated:
            comment = form.save(commit=False)
            comment.author = request.user
            comment.photo = self.object
            comment.save()

            # Уведомление автору фото
            if self.object.author != request.user:
                Notification.objects.create(
                    recipient=self.object.author,
                    sender=request.user,
                    notification_type='comment',
                    title='Новый комментарий к фото',
                    message=f'{request.user.username} прокомментировал ваше фото "{self.object.title}"'
                )

            # Логируем действие
            ActionLog.objects.create(
                user=request.user,
                action_type='comment_added',
                model_name='Photo',
                object_id=self.object.pk,
                object_repr=str(self.object),
                details=f'Пользователь {request.user.username} добавил комментарий к фото #{self.object.pk}'
            )

            messages.success(request, 'Комментарий добавлен!')
            return redirect('gallery:photo_detail', pk=self.object.pk)

        # Если форма невалидна, показываем ошибки
        context = self.get_context_data()
        context['comment_form'] = form
        return render(request, self.template_name, context)

class PhotoUploadView(LoginRequiredMixin, CreateView):
    """Загрузка фотографии"""
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'gallery/photo_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        # Логируем действие
        ActionLog.objects.create(
            user=self.request.user,
            action_type='photo_uploaded',
            model_name='Photo',
            object_id=form.instance.pk,
            object_repr=str(form.instance),
            details=f'Uploaded photo: {form.instance.title}'
        )

        messages.success(self.request, 'Фотография успешно загружена!')
        return response

    def get_success_url(self):
        return reverse('gallery:photo_detail', kwargs={'pk': self.object.pk})

def toggle_like_photo(request, pk):
    """AJAX лайк/дизлайк фотографии"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    photo = get_object_or_404(Photo, pk=pk)

    if photo.likes.filter(id=request.user.id).exists():
        photo.likes.remove(request.user)
        liked = False
        action = 'unliked'
    else:
        photo.likes.add(request.user)
        liked = True
        action = 'liked'

        # Уведомление автору (если это не он сам)
        if photo.author != request.user:
            Notification.objects.create(
                recipient=photo.author,
                sender=request.user,
                notification_type='like',
                title='Новый лайк',
                message=f'{request.user.username} лайкнул ваше фото "{photo.title}"'
            )

    # Логируем действие
    ActionLog.objects.create(
        user=request.user,
        action_type=action,
        model_name='Photo',
        object_id=photo.pk,
        object_repr=str(photo),
        details=f'Пользователь {request.user.username} {action.capitalize()} фото #{photo.pk}'
    )

    return JsonResponse({'likes_count': photo.likes.count(), 'liked': liked})

class PhotoUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование фотографии"""
    model = Photo
    form_class = PhotoUploadForm
    template_name = 'gallery/edit.html'

    def dispatch(self, request, *args, **kwargs):
        photo = self.get_object()
        if photo.author != request.user:
            return HttpResponseForbidden("You can only edit your own photos")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Логируем действие
        ActionLog.objects.create(
            user=self.request.user,
            action='photo_updated',
            details=f'Updated photo: {form.instance.title}'
        )

        messages.success(self.request, 'Фотография обновлена!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('gallery:photo_detail', kwargs={'pk': self.object.pk})

class PhotoDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление фотографии"""
    model = Photo
    template_name = 'gallery/delete_confirm.html'
    success_url = reverse_lazy('gallery:my_photos')

    def dispatch(self, request, *args, **kwargs):
        photo = self.get_object()
        if photo.author != request.user:
            return HttpResponseForbidden("You can only delete your own photos")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        photo = self.get_object()
        photo_title = photo.title

        # Soft delete
        photo.is_active = False
        photo.save()

        # Логируем действие
        ActionLog.objects.create(
            user=request.user,
            action='photo_deleted',
            details=f'Deleted photo: {photo_title}'
        )

        messages.success(request, 'Фотография удалена!')
        return redirect(self.success_url)

def load_more_photos(request):
    """AJAX подгрузка фотографий для бесконечной прокрутки"""
    page = request.GET.get('page', 1)
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', '-created_at')

    queryset = Photo.objects.filter(is_public=True, is_active=True)

    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(author__username__icontains=search)
        )

    if sort == 'popular':
        queryset = queryset.annotate(likes_count=Count('likes')).order_by('-likes_count', '-created_at')
    else:
        queryset = queryset.order_by(sort)

    paginator = Paginator(queryset.select_related('author').prefetch_related('likes'), 24)

    try:
        photos = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        return JsonResponse({'photos': [], 'has_next': False})

    # Формируем данные для JSON
    photos_data = []
    for photo in photos:
        photos_data.append({
            'id': photo.id,
            'title': photo.title,
            'image_url': photo.image.url,
            'author': photo.author.username,
            'author_url': reverse('users:detail', kwargs={'username': photo.author.username}),
            'detail_url': reverse('gallery:photo_detail', kwargs={'pk': photo.pk}),
            'likes_count': photo.likes.count(),
            'created_at': photo.created_at.strftime('%d.%m.%Y'),
        })

    return JsonResponse({
        'photos': photos_data,
        'has_next': photos.has_next(),
        'next_page': photos.next_page_number() if photos.has_next() else None
    })
