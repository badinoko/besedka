from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Photo, PhotoComment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden, Http404
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
    """Современная галерея с Masonry раскладкой"""
    model = Photo
    template_name = 'gallery/gallery_modern.html'
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
            context['user_liked_photos'] = list(liked_photos)
        else:
            context['user_liked_photos'] = []

        # Статистика для hero секции
        context['total_photos'] = Photo.objects.filter(is_public=True, is_active=True).count()
        context['total_authors'] = Photo.objects.filter(is_public=True, is_active=True).values('author').distinct().count()
        context['total_likes'] = Photo.objects.filter(is_public=True, is_active=True).aggregate(
            total_likes=Count('likes')
        )['total_likes'] or 0

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
    paginate_by = 24

    def get_queryset(self):
        queryset = Photo.objects.filter(
            author=self.request.user,
            is_active=True
        )

        # Сортировка
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by == 'popular':
            queryset = queryset.annotate(likes_count=Count('likes')).order_by('-likes_count', '-created_at')
        elif sort_by == 'commented':
            queryset = queryset.annotate(comments_count=Count('comments')).order_by('-comments_count', '-created_at')
        else:
            queryset = queryset.order_by(sort_by)

        return queryset.select_related('growlog').prefetch_related('likes', 'comments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Статистика пользователя
        base_queryset = Photo.objects.filter(
            author=self.request.user,
            is_active=True
        )

        context['total_photos'] = base_queryset.count()
        context['total_public_photos'] = base_queryset.filter(is_public=True).count()
        context['total_private_photos'] = base_queryset.filter(is_public=False).count()
        context['total_likes'] = base_queryset.aggregate(
            total_likes=Count('likes')
        )['total_likes'] or 0
        context['current_sort'] = self.request.GET.get('sort', '-created_at')

        # Добавляем информацию о лайках для текущего пользователя
        liked_photos = self.request.user.liked_photos.values_list('id', flat=True)
        context['user_liked_photos'] = list(liked_photos)

        return context

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

    return JsonResponse({
        'success': True,
        'status': 'ok',
        'likes_count': photo.likes.count(),
        'liked': liked,
        'action': action
    })

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Логируем действие
        ActionLog.objects.create(
            user=self.request.user,
            action_type='photo_updated',
            model_name='Photo',
            object_id=form.instance.pk,
            object_repr=str(form.instance),
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
            action_type='photo_deleted',
            model_name='Photo',
            object_id=photo.pk,
            object_repr=str(photo),
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

class AuthorPhotosView(ListView):
    """Фотографии конкретного автора"""
    model = Photo
    template_name = 'gallery/author_photos.html'
    context_object_name = 'photos'
    paginate_by = 24

    def dispatch(self, request, *args, **kwargs):
        """Проверяем, не смотрит ли пользователь свои собственные фотографии"""
        User = get_user_model()

        username = self.kwargs['username']

        # Если пользователь авторизован и смотрит свои фотографии - перенаправляем на my-photos
        if request.user.is_authenticated and request.user.username == username:
            return redirect('gallery:my_photos')

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        User = get_user_model()

        self.author = get_object_or_404(User, username=self.kwargs['username'])

        queryset = Photo.objects.filter(
            author=self.author,
            is_public=True,
            is_active=True
        )

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

        context['author'] = self.author

        # Исправляем подсчет фотографий - используем базовый queryset без пагинации
        base_queryset = Photo.objects.filter(
            author=self.author,
            is_public=True,
            is_active=True
        )

        context['total_photos'] = base_queryset.count()
        context['total_likes'] = base_queryset.aggregate(
            total_likes=Count('likes')
        )['total_likes'] or 0
        context['current_sort'] = self.request.GET.get('sort', '-created_at')

        # Добавляем информацию о лайках для текущего пользователя
        if self.request.user.is_authenticated:
            liked_photos = self.request.user.liked_photos.values_list('id', flat=True)
            context['user_liked_photos'] = list(liked_photos)
        else:
            context['user_liked_photos'] = []

        return context

class PhotoCommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментария к фото"""
    model = PhotoComment
    form_class = PhotoCommentForm
    template_name = 'gallery/comment_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.photo = get_object_or_404(Photo, pk=kwargs['photo_pk'])
        # Проверяем доступ к фото
        if not self.photo.is_public and self.photo.author != request.user:
            raise Http404("Photo not found")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.photo = self.photo

        # Логируем действие
        ActionLog.objects.create(
            user=self.request.user,
            action='comment_create',
            details=f'Комментарий к фото "{self.photo.title}"'
        )

        messages.success(self.request, _('Комментарий добавлен успешно!'))
        return super().form_valid(form)

    def get_success_url(self):
        return self.photo.get_absolute_url()

class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование комментария"""
    model = PhotoComment
    fields = ['text']
    template_name = 'gallery/comment_edit.html'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return HttpResponseForbidden("You can only edit your own comments")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Логируем действие
        ActionLog.objects.create(
            user=self.request.user,
            action_type='comment_updated',
            model_name='PhotoComment',
            object_id=form.instance.pk,
            object_repr=str(form.instance),
            details=f'Updated comment on photo: {form.instance.photo.title}'
        )

        messages.success(self.request, 'Комментарий обновлен!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('gallery:photo_detail', kwargs={'pk': self.object.photo.pk})

class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление комментария"""
    model = PhotoComment
    template_name = 'gallery/comment_delete_confirm.html'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return HttpResponseForbidden("You can only delete your own comments")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        photo_pk = comment.photo.pk

        # Логируем действие
        ActionLog.objects.create(
            user=request.user,
            action_type='comment_deleted',
            model_name='PhotoComment',
            object_id=comment.pk,
            object_repr=str(comment),
            details=f'Deleted comment on photo: {comment.photo.title}'
        )

        messages.success(request, 'Комментарий удален!')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('gallery:photo_detail', kwargs={'pk': self.object.photo.pk})

# ============= ТЕСТОВЫЕ ДАННЫЕ ДЛЯ РАЗРАБОТКИ =============

@login_required
def create_test_data_view(request):
    """Создание тестовых данных для галереи и гроурепортов - ТОЛЬКО ДЛЯ РАЗРАБОТКИ"""

    # Проверяем права доступа (только для owner/admin)
    if not (hasattr(request.user, 'role') and request.user.role in ['owner', 'admin']):
        messages.error(request, '❌ Доступ запрещен. Только для администрации.')
        return redirect('gallery:gallery')

    if request.method == 'POST':
        try:
            # Генерируем тестовые данные
            result = generate_test_data()

            messages.success(request, f"""
                ✅ Тестовые данные созданы успешно!
                📸 Фотографий: {result['photos_created']}
                🌱 Гроурепортов: {result['growlogs_created']}
                🔔 Уведомлений: {result['notifications_created']}
            """)

        except Exception as e:
            messages.error(request, f'❌ Ошибка создания тестовых данных: {str(e)}')

    # Показываем текущую статистику
    from growlogs.models import GrowLog

    context = {
        'total_photos': Photo.objects.count(),
        'total_growlogs': GrowLog.objects.count(),
        'total_users': get_user_model().objects.count(),
        'total_notifications': Notification.objects.count(),
    }

    return render(request, 'gallery/create_test_data.html', context)


def generate_test_data():
    """Генерирует тестовые данные"""
    from growlogs.models import GrowLog, GrowLogComment

    User = get_user_model()

    # Список растений для генерации
    plant_names = [
        'White Widow', 'Northern Lights', 'Blue Dream', 'AK-47',
        'Purple Haze', 'Jack Herer', 'Sour Diesel', 'OG Kush',
        'Super Skunk', 'Amnesia Haze', 'Cheese', 'Critical'
    ]

    # Цвета для генерации фейковых изображений
    plant_colors = [
        '#2ECC71', '#27AE60', '#16A085', '#1ABC9C',
        '#3498DB', '#2980B9', '#9B59B6', '#8E44AD',
        '#F39C12', '#E67E22', '#E74C3C', '#C0392B'
    ]

    # Получаем существующих пользователей
    users = list(User.objects.filter(is_active=True))
    if not users:
        raise Exception('Нет активных пользователей')

    photos_created = 0
    growlogs_created = 0
    notifications_created = 0

    # Создаем 12 фотографий
    for i in range(12):
        # Случайный автор
        author = random.choice(users)

        # Случайное растение
        plant_name = random.choice(plant_names)

        # Генерируем фейковое изображение
        image = create_test_image(plant_name, random.choice(plant_colors))

        # Создаем фото
        photo = Photo.objects.create(
            title=f'{plant_name} - День {random.randint(1, 120)}',
            description=generate_photo_description(plant_name),
            author=author,
            is_public=True
        )

        # Сохраняем изображение
        img_file = ContentFile(image.getvalue())
        photo.image.save(f'test_photo_{i+1}.png', img_file, save=True)

        # Добавляем случайные лайки
        like_users = random.sample(users, k=random.randint(0, min(5, len(users))))
        for like_user in like_users:
            if like_user != author:  # Автор не лайкает себя
                photo.likes.add(like_user)

        # Добавляем случайные комментарии
        comment_users = random.sample(users, k=random.randint(0, 3))
        for comment_user in comment_users:
            if comment_user != author:
                PhotoComment.objects.create(
                    photo=photo,
                    author=comment_user,
                    text=generate_photo_comment()
                )

        photos_created += 1

    # Создаем 3 гроурепорта
    for i in range(3):
        # Случайный автор
        grower = random.choice(users)

        # Случайное растение
        plant_name = random.choice(plant_names)

        # Создаем гроурепорт
        growlog = GrowLog.objects.create(
            title=f'Выращивание {plant_name} #{i+1}',
            description=generate_growlog_description(plant_name),
            grower=grower,
            environment=random.choice(['indoor', 'outdoor', 'greenhouse']),
            medium=random.choice(['soil', 'hydro', 'coco', 'aero']),
            current_stage=random.choice(['seed', 'germination', 'seedling', 'vegetative', 'flowering', 'harvest']),
            is_public=True,
            strain_custom=plant_name
        )

        # Добавляем случайные лайки
        like_users = random.sample(users, k=random.randint(0, min(7, len(users))))
        for like_user in like_users:
            if like_user != grower:
                growlog.likes.add(like_user)

        # Добавляем случайные комментарии
        comment_users = random.sample(users, k=random.randint(0, 4))
        for comment_user in comment_users:
            if comment_user != grower:
                GrowLogComment.objects.create(
                    growlog=growlog,
                    author=comment_user,
                    content=generate_growlog_comment()
                )

        growlogs_created += 1

    # Создаем уведомления естественным образом
    # Создаем уведомления о новых лайках
    for photo in Photo.objects.filter(title__startswith='White Widow'):
        for like_user in photo.likes.all()[:2]:  # Берем первых 2 лайкеров
            if like_user != photo.author:
                Notification.objects.create(
                    recipient=photo.author,
                    sender=like_user,
                    title='Новый лайк в галерее!',
                    message=f'{like_user.username} лайкнул вашу фотографию "{photo.title}"',
                    notification_type='like',
                    content_object=photo
                )
                notifications_created += 1

    return {
        'photos_created': photos_created,
        'growlogs_created': growlogs_created,
        'notifications_created': notifications_created
    }


def create_test_image(plant_name, color):
    """Создает тестовое изображение растения"""
    # Создаем изображение 400x400
    img = Image.new('RGB', (400, 400), color=color)
    draw = ImageDraw.Draw(img)

    # Рисуем простую имитацию растения
    # Стебель
    draw.rectangle([190, 200, 210, 380], fill='#8B4513')

    # Листья
    for i in range(3):
        y = 150 + i * 60
        # Левый лист
        draw.ellipse([120, y, 190, y + 40], fill='#228B22')
        # Правый лист
        draw.ellipse([210, y, 280, y + 40], fill='#228B22')

    # Добавляем текст
    try:
        font = ImageFont.load_default()
    except:
        font = None

    # Название растения
    if font:
        text_bbox = draw.textbbox((0, 0), plant_name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text((200 - text_width // 2, 50), plant_name, fill='white', font=font)

    # Сохраняем в BytesIO
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return img_io


def generate_photo_description(plant_name):
    """Генерирует описание для фотографии"""
    descriptions = [
        f'Мой {plant_name} на {random.randint(20, 80)} день цветения. Очень доволен результатом!',
        f'Красивые шишки {plant_name}. Запах просто невероятный!',
        f'{plant_name} день {random.randint(1, 120)}. Растет как на дрожжах!',
        f'Первый опыт выращивания {plant_name}. Пока все идет отлично.',
        f'Харвест {plant_name} близко! Жду не дождусь попробовать.',
        f'Мой любимый сорт - {plant_name}. Всегда радует качеством.',
    ]
    return random.choice(descriptions)


def generate_growlog_description(plant_name):
    """Генерирует описание для гроурепорта"""
    descriptions = [
        f'Документирую полный цикл выращивания {plant_name}. Это мой первый опыт с этим сортом.',
        f'Эксперимент с {plant_name} в гидропонике. Делюсь опытом и наблюдениями.',
        f'Органическое выращивание {plant_name} в почве. Записываю все этапы развития.',
        f'Второй гров {plant_name}. В прошлый раз результат был отличный, повторяю.',
        f'Сравниваю разные методы на {plant_name}. Интересно увидеть разницу.',
    ]
    return random.choice(descriptions)


def generate_photo_comment():
    """Генерирует случайный комментарий для фото"""
    comments = [
        'Отличная работа! 👍',
        'Красивые шишки! Какой запах?',
        'Вау! Очень впечатляет!',
        'Сколько дней цветения?',
        'Какие удобрения используешь?',
        'Шикарный результат! 🔥',
        'Какая урожайность ожидается?',
        'Первый раз вижу такую красоту!',
        'Поделись секретом успеха!',
        'Фото просто огонь! 📸',
    ]
    return random.choice(comments)


def generate_growlog_comment():
    """Генерирует случайный комментарий для гроурепорта"""
    comments = [
        'Интересный подход! Буду следить за развитием.',
        'Какой свет используешь?',
        'Отличный старт! Удачи в выращивании!',
        'Очень познавательно! Спасибо за детали.',
        'Подписался на обновления! 👀',
        'Какая температура в боксе?',
        'Сколько растений планируешь?',
        'Крутая установка! Сам такую хочу.',
        'Какой сидбанк у семян?',
        'Жду продолжения! Очень интересно!',
    ]
    return random.choice(comments)
