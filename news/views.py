from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, F, Prefetch, Sum
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
import json

from .models import Post, Category, Tag, Comment, Reaction, Poll, PollChoice, PollVote, PostView
from .forms import CommentForm
from core.view_mixins import UnifiedCardMixin
from core.base_views import UnifiedListView
from core.constants import COMMENTS_PAGE_SIZE, UNIFIED_PAGE_SIZE
from core.utils import get_limited_top_level_comments, get_total_comments_count, get_unified_cards


class HomePageView(UnifiedListView):
    """Главная страница - новостная лента"""
    model = Post
    template_name = 'base_list_page.html'
    # context_object_name наследуется из базового класса
    paginate_by = UNIFIED_PAGE_SIZE

    # УНИФИЦИРОВАННЫЕ НАСТРОЙКИ
    section_title = "Новости Сообщества"
    section_subtitle = "Самые свежие статьи, события и обновления платформы \"Беседка\""
    section_hero_class = "news-hero"
    card_type = "news"
    ajax_url_name = "news:ajax_filter"

    def get_queryset(self):
        # Базовый queryset - только опубликованные посты
        # ПРАВИЛЬНАЯ предзагрузка для избежания N+1 запросов
        queryset = Post.published.select_related('author', 'category').prefetch_related(
            'tags',
            'reactions',  # Загружаем все реакции
            Prefetch(
                'comments',
                queryset=Comment.objects.filter(parent__isnull=True) # Только корневые комментарии
            )
        )
        # Применяем фильтры
        return self.apply_filters(queryset)

    def apply_filters(self, queryset):
        """
        Переопределяем логику фильтрации, т.к. базовая в UnifiedListView
        не умеет работать с моделью Reaction.
        """
        filter_type = self.request.GET.get('filter', 'all')

        if filter_type == 'articles':
            queryset = queryset.filter(post_type='article')
        elif filter_type == 'polls':
            queryset = queryset.filter(post_type='poll')
        elif filter_type == 'videos':
            queryset = queryset.filter(post_type='video_link')
        elif filter_type == 'pinned':
            queryset = queryset.filter(is_pinned=True)

        # Сортировка
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'popular':
            # ПРАВИЛЬНАЯ аннотация для подсчета лайков из реакций
            queryset = queryset.annotate(
                likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
                comments_count_val=Count('comments')
            ).annotate(
                popularity=F('likes_count') + F('comments_count_val')
            ).order_by('-popularity', '-published_at')
        elif sort_by == 'commented':
            queryset = queryset.annotate(
                comments_count_val=Count('comments')
            ).order_by('-comments_count_val', '-published_at')
        else: # newest
            queryset = queryset.order_by('-is_pinned', '-published_at')

        return queryset

    def get_hero_stats(self):
        """Статистика для hero-секции новостей"""
        total_posts = Post.published.count()
        total_views = Post.published.aggregate(total=Sum('views_count'))['total'] or 0
        total_comments = Comment.objects.filter(post__status='published').count()

        return [
            {'value': total_posts, 'label': 'Публикаций'},
            {'value': total_views, 'label': 'Просмотров'},
            {'value': total_comments, 'label': 'Комментариев'},
        ]

    def get_hero_actions(self):
        """В новостях нет кнопок действий"""
        return []

    def get_filter_list(self):
        """Фильтры для новостей (унификация: первая кнопка — 'newest')"""
        return [
            {'id': 'newest', 'label': 'Все Статьи'},
            {'id': 'articles', 'label': 'Статьи'},
            {'id': 'polls', 'label': 'Опросы'},
            {'id': 'videos', 'label': 'Видео'},
            {'id': 'pinned', 'label': 'Закрепленные'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # hero_context оставляем, filter_context убираем (используется базовый)
        context['hero_context'] = {
            'section_title': self.section_title,
            'section_subtitle': self.section_subtitle,
            'section_hero_class': self.section_hero_class,
            'stats_list': self.get_hero_stats(),
            'actions_list': self.get_hero_actions()
        }
        # Категории и теги оставляем
        context['categories'] = Category.objects.annotate(
            posts_count=Count('post', filter=Q(post__status='published'))
        ).filter(posts_count__gt=0)
        context['popular_tags'] = Tag.objects.annotate(
            posts_count=Count('post', filter=Q(post__status='published'))
        ).filter(posts_count__gt=0).order_by('-posts_count')[:10]
        context['total_posts'] = Post.published.count()
        context['total_categories'] = Category.objects.annotate(
            posts_count=Count('post', filter=Q(post__status='published'))
        ).filter(posts_count__gt=0).count()
        context['total_views'] = Post.published.aggregate(
            total=Sum('views_count')
        )['total'] or 0
        return context


class PostDetailView(DetailView):
    """Детальная страница поста"""
    model = Post
    template_name = 'news/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_arg = 'slug'

    def get_queryset(self):
        # Показываем только опубликованные посты c предзагрузкой
        return Post.published.select_related('author', 'category').prefetch_related(
            'tags',
            'reactions',
            Prefetch('comments', queryset=Comment.objects.select_related('author').prefetch_related('reactions'))
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # Увеличиваем счетчик просмотров
        self.increment_view_count(obj)

        return obj

    def increment_view_count(self, post):
        """Увеличивает счетчик просмотров с учетом уникальности"""
        user = self.request.user if self.request.user.is_authenticated else None
        ip_address = self.get_client_ip()
        session_key = self.request.session.session_key or ''

        # Проверяем, не просматривал ли уже этот пост
        view_exists = PostView.objects.filter(
            post=post,
            user=user,
            ip_address=ip_address,
            session_key=session_key
        ).exists()

        if not view_exists:
            PostView.objects.create(
                post=post,
                user=user,
                ip_address=ip_address,
                session_key=session_key
            )
            # Инкрементируем счётчик просмотров в модели Post
            Post.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
            post.refresh_from_db(fields=['views_count'])

    def get_client_ip(self):
        """Получает IP-адрес клиента"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        selected, displayed_blocks, total_root = get_limited_top_level_comments(
            post,
            comment_relation="comments",
            block_limit=COMMENTS_PAGE_SIZE,
        )

        context['top_level_comments'] = selected
        total_comments = get_total_comments_count(post)
        # Добавляем в контекст и динамически на объект для использования в шаблоне
        context['comments_count'] = total_comments
        setattr(post, 'comments_count', total_comments)
        context['has_more_comments'] = total_root > len(selected)

        # Передаём в контекст переменные, как и в других детальных страницах,
        # чтобы унифицированный партиал comments_list работал без шаблонных вычислений
        context['comments'] = context['top_level_comments']

        context['comment_form'] = CommentForm()

        # Реакции
        context['reactions_summary'] = self.get_reactions_summary(post)

        # Если пользователь авторизован, получаем его реакцию
        if self.request.user.is_authenticated:
            user_reaction = Reaction.objects.filter(post=post, user=self.request.user).first()
            context['user_reaction'] = user_reaction.reaction_type if user_reaction else None
            # Для унифицированной системы лайков
            context['user_liked'] = user_reaction is not None and user_reaction.reaction_type == 'like'

        # Для опросов
        if post.post_type == 'poll' and hasattr(post, 'poll'):
            context['poll'] = post.poll
            context['poll_results'] = post.poll.get_results()

            # Проверяем, голосовал ли пользователь
            if self.request.user.is_authenticated:
                user_votes = PollVote.objects.filter(poll=post.poll, user=self.request.user)
                context['user_voted'] = user_votes.exists()
                context['user_vote_choices'] = [vote.choice.id for vote in user_votes]

        # Похожие посты
        context['related_posts'] = self.get_related_posts(post)

        # Статистика для унифицированной hero-секции
        context['detail_hero_stats'] = [
            {'value': post.views_count or 0, 'label': 'просмотров', 'css_class': 'views'},
            {'value': context['comments_count'], 'label': 'комментариев', 'css_class': 'comments'},
            {'value': post.reactions.count(), 'label': 'лайков', 'css_class': 'likes'},
        ]

        return context

    def get_reactions_summary(self, post):
        """Получает сводку по реакциям"""
        reactions = Reaction.objects.filter(post=post).values('reaction_type').annotate(count=Count('id'))
        return {reaction['reaction_type']: reaction['count'] for reaction in reactions}

    def get_related_posts(self, post):
        """Получает похожие посты"""
        return Post.published.filter(
            category=post.category
        ).exclude(id=post.id)[:3]

    def post(self, request, *args, **kwargs):
        """Обработка POST-запросов (комментарии)"""
        if not request.user.is_authenticated:
            messages.error(request, 'Для добавления комментария необходимо войти в систему.')
            return redirect('account_login')

        self.object = self.get_object()
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.author = request.user

            # Обработка ответа на комментарий
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = get_object_or_404(Comment, id=parent_id, post=self.object)

                    # Ограничиваем глубину вложенности до 3 уровней
                    # Разрешаем ответы, если глубина родительского комментария < 2 (т.е. максимум 2 уровня)
                    # Если у parent_comment уже есть parent и у того тоже есть parent (уровень 2), запрещаем дальнейшие ответы
                    if parent_comment.parent is not None and parent_comment.parent.parent is not None:
                        return JsonResponse({'status': 'error', 'message': 'Достигнут максимальный уровень вложенности комментариев.'}, status=400)

                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Родительский комментарий не найден'}, status=404)

            comment.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX запрос – не добавляем сообщения Django 'messages'.
                comments_html = render_to_string(
                    'includes/partials/unified_comments_list.html',
                    {
                        'top_level_comments': (
                            self.object.comments.filter(parent__isnull=True)
                            .select_related('author')
                            .prefetch_related('replies__author')
                            .order_by('-created_at')
                        ),
                    },
                    request=request
                )

                return JsonResponse({
                    'success': True,
                    'comments_html': comments_html,
                    'comment_id': comment.id,
                    'parent_id': parent_id,
                    'comments_count': get_total_comments_count(self.object),
                })
            else:
                messages.success(request, 'Комментарий добавлен!')
                return redirect(self.object.get_absolute_url() + '#comments')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Ошибка валидации формы.', 'errors': form.errors}, status=400)

            messages.error(request, 'Ошибка при добавлении комментария.')

        return self.get(request, *args, **kwargs)


class CategoryPostListView(UnifiedListView):
    """Унифицированный список постов конкретной категории"""
    model = Post
    # Используем единый шаблон для всех списковых страниц
    template_name = 'base_list_page.html'
    # context_object_name наследуется из базового класса
    paginate_by = UNIFIED_PAGE_SIZE  # Единый размер страницы

    # УНИФИЦИРОВАННЫЕ НАСТРОЙКИ HERO/КАРТОЧЕК
    card_type = 'news'
    section_hero_class = 'news-hero'

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return (
            Post.published
                .filter(category=self.category)
                .select_related('author', 'category')
                .prefetch_related('tags')
        )

    # Переопределяем фильтры – для конкретной категории они не нужны
    def get_filter_list(self):
        return []

    def get_hero_stats(self):
        posts_count = Post.published.filter(category=self.category).count()
        views_total = Post.published.filter(category=self.category).aggregate(total=Sum('views_count'))['total'] or 0
        comments_total = Comment.objects.filter(post__category=self.category, post__status='published').count()
        return [
            {'value': posts_count, 'label': 'Постов'},
            {'value': views_total, 'label': 'Просмотров'},
            {'value': comments_total, 'label': 'Комментариев'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Динамически обновляем заголовки hero-секции
        context['hero_context']['section_title'] = f"Категория: {self.category.name}"
        context['hero_context']['section_subtitle'] = (
            getattr(self.category, 'description', '') or f"Все посты из категории {self.category.name}"
        )

        # page_obj создается автоматически Django ListView
        # НЕ перезаписываем его!

        return context


class TagPostListView(UnifiedListView):
    """Унифицированный список постов по тегу"""
    model = Post
    template_name = 'base_list_page.html'
    # context_object_name наследуется из базового класса
    paginate_by = UNIFIED_PAGE_SIZE

    card_type = 'news'
    section_hero_class = 'news-hero'

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return (
            Post.published
                .filter(tags=self.tag)
                .select_related('author', 'category')
                .prefetch_related('tags')
        )

    def get_filter_list(self):
        return []

    def get_hero_stats(self):
        posts_count = Post.published.filter(tags=self.tag).count()
        views_total = (
            Post.published.filter(tags=self.tag).aggregate(total=Sum('views_count'))['total'] or 0
        )
        comments_total = Comment.objects.filter(post__tags=self.tag, post__status='published').count()
        return [
            {'value': posts_count, 'label': 'Постов'},
            {'value': views_total, 'label': 'Просмотров'},
            {'value': comments_total, 'label': 'Комментариев'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['hero_context']['section_title'] = f"Тег: #{self.tag.name}"
        context['hero_context']['section_subtitle'] = (
            f"Все посты с тегом #{self.tag.name}"
        )

        # page_obj создается автоматически Django ListView
        # НЕ перезаписываем его!

        return context


@login_required
@require_POST
def add_reaction(request):
    """AJAX-обработчик для добавления/изменения реакций"""
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        comment_id = data.get('comment_id')
        reaction_type = data.get('reaction_type')

        if not reaction_type or reaction_type not in dict(Reaction.REACTION_TYPES):
            return JsonResponse({'error': 'Неверный тип реакции'}, status=400)

        # Определяем объект реакции
        if post_id:
            post = get_object_or_404(Post, id=post_id)
            reaction, created = Reaction.objects.get_or_create(
                post=post,
                user=request.user,
                defaults={'reaction_type': reaction_type}
            )
        elif comment_id:
            comment = get_object_or_404(Comment, id=comment_id)
            reaction, created = Reaction.objects.get_or_create(
                comment=comment,
                user=request.user,
                defaults={'reaction_type': reaction_type}
            )
        else:
            return JsonResponse({'error': 'Не указан объект для реакции'}, status=400)

        # Если реакция уже существует, обновляем или удаляем
        if not created:
            if reaction.reaction_type == reaction_type:
                # Убираем реакцию
                reaction.delete()
                action = 'removed'
            else:
                # Меняем реакцию
                reaction.reaction_type = reaction_type
                reaction.save()
                action = 'changed'
        else:
            action = 'added'

        # Получаем обновленную статистику
        if post_id:
            reactions_summary = Reaction.objects.filter(post=post).values('reaction_type').annotate(count=Count('id'))
        else:
            reactions_summary = Reaction.objects.filter(comment=comment).values('reaction_type').annotate(count=Count('id'))

        reactions_data = {r['reaction_type']: r['count'] for r in reactions_summary}

        return JsonResponse({
            'success': True,
            'action': action,
            'reactions': reactions_data,
            'user_reaction': reaction_type if action != 'removed' else None
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def toggle_reaction(request):
    """AJAX-обработчик для переключения реакций на посты"""
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        reaction_type = data.get('reaction_type')

        if not post_id or not reaction_type:
            return JsonResponse({'error': 'Не указаны обязательные поля'}, status=400)

        if reaction_type not in dict(Reaction.REACTION_TYPES):
            return JsonResponse({'error': 'Неверный тип реакции'}, status=400)

        post = get_object_or_404(Post, id=post_id)

        # Проверяем, есть ли уже реакция от этого пользователя
        existing_reaction = Reaction.objects.filter(post=post, user=request.user).first()

        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Убираем реакцию
                existing_reaction.delete()
                added = False
            else:
                # Меняем тип реакции
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                added = True
        else:
            # Добавляем новую реакцию
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
            added = True

        # Получаем обновленное количество реакций этого типа
        count = Reaction.objects.filter(post=post, reaction_type=reaction_type).count()

        return JsonResponse({
            'success': True,
            'added': added,
            'count': count
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def toggle_comment_reaction(request):
    """AJAX-обработчик для переключения реакций на комментарии"""
    try:
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        reaction_type = data.get('reaction_type')

        if not comment_id or not reaction_type:
            return JsonResponse({'error': 'Не указаны обязательные поля'}, status=400)

        if reaction_type not in dict(Reaction.REACTION_TYPES):
            return JsonResponse({'error': 'Неверный тип реакции'}, status=400)

        comment = get_object_or_404(Comment, id=comment_id)

        # Проверяем, есть ли уже реакция от этого пользователя
        existing_reaction = Reaction.objects.filter(comment=comment, user=request.user).first()

        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Убираем реакцию
                existing_reaction.delete()
                added = False
            else:
                # Меняем тип реакции
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                added = True
        else:
            # Добавляем новую реакцию
            Reaction.objects.create(
                comment=comment,
                user=request.user,
                reaction_type=reaction_type
            )
            added = True

        # Получаем общее количество реакций на комментарий
        count = Reaction.objects.filter(comment=comment).count()

        return JsonResponse({
            'success': True,
            'added': added,
            'count': count
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def add_comment(request):
    """
    Обрабатывает AJAX-запросы на добавление комментариев к посту.
    Теперь возвращает полный HTML списка комментариев через
    универсальный партиал `includes/partials/unified_comments_list.html`,
    чтобы сохранялись все интерактивные элементы (кнопка «Ответить» и др.).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Требуется авторизация'}, status=401)

    form = CommentForm(request.POST)
    post_id = request.POST.get('post_id')
    parent_id = request.POST.get('parent_id')

    if not post_id:
        return JsonResponse({'status': 'error', 'message': 'Отсутствует ID поста.'}, status=400)

    if form.is_valid():
        post = get_object_or_404(Post, id=post_id, status='published')

        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user

        if parent_id:
            try:
                parent_comment = get_object_or_404(Comment, id=parent_id, post=post)

                # Ограничиваем глубину вложенности до 3 уровней
                # Разрешаем ответы, если глубина родительского комментария < 2 (т.е. максимум 2 уровня)
                # Если у parent_comment уже есть parent и у того тоже есть parent (уровень 2), запрещаем дальнейшие ответы
                if parent_comment.parent is not None and parent_comment.parent.parent is not None:
                    return JsonResponse({'status': 'error', 'message': 'Достигнут максимальный уровень вложенности комментариев.'}, status=400)

                comment.parent = parent_comment
            except Comment.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Родительский комментарий не найден'}, status=404)

        comment.save()

        # Рендерим ПОЛНЫЙ список top-level комментариев, чтобы кнопки «Ответить»
        # и другие интерактивные элементы присутствовали у всех комментариев.
        comments_html = render_to_string(
            'includes/partials/unified_comments_list.html',
            {
                'post': post,
                'top_level_comments': post.comments.filter(parent__isnull=True)
                                              .select_related('author')
                                              .prefetch_related('replies__author')
                                              .order_by('-created_at'),
            },
            request=request
        )

        return JsonResponse({
            'success': True,
            'comments_html': comments_html,
            'comment_id': comment.id,
            'comments_count': get_total_comments_count(post),
        })

    # Если форма невалидна
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@login_required
@require_POST
def vote_in_poll(request):
    """AJAX-обработчик для голосования в опросах"""
    try:
        data = json.loads(request.body)
        poll_id = data.get('poll_id')
        choice_ids = data.get('choice_ids', [])

        if not poll_id or not choice_ids:
            return JsonResponse({'error': 'Не указаны обязательные поля'}, status=400)

        poll = get_object_or_404(Poll, id=poll_id)

        # Проверяем, не голосовал ли уже пользователь
        if PollVote.objects.filter(poll=poll, user=request.user).exists():
            return JsonResponse({'error': 'Вы уже голосовали в этом опросе'}, status=400)

        # Проверяем ограничения по количеству выборов
        if not poll.multiple_choice and len(choice_ids) > 1:
            return JsonResponse({'error': 'В этом опросе можно выбрать только один вариант'}, status=400)

        # Создаем голоса
        votes_created = 0
        for choice_id in choice_ids:
            try:
                choice = PollChoice.objects.get(id=choice_id, poll=poll)
                PollVote.objects.create(
                    poll=poll,
                    user=request.user,
                    choice=choice
                )
                votes_created += 1
            except PollChoice.DoesNotExist:
                continue

        if votes_created == 0:
            return JsonResponse({'error': 'Не найдены действительные варианты для голосования'}, status=400)

        # Получаем обновленные результаты
        results = poll.get_results()

        return JsonResponse({
            'success': True,
            'results': results,
            'total_votes': poll.get_total_votes()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def search_posts(request):
    """Поиск по постам - УНИФИЦИРОВАННЫЙ через SSOT"""
    query = request.GET.get('q', '').strip()
    results = Post.objects.none()

    if query and len(query) >= 3:
        # Поиск по заголовку, контенту и тегам
        results = Post.published.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().select_related('author', 'category')[:20]

    # SSOT: используем get_unified_cards для формирования карточек
    unified_card_list = get_unified_cards(results, 'news') if results else []

    context = {
        'query': query,
        'results': results,
        'results_count': len(results),
        'unified_card_list': unified_card_list,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX запрос - возвращаем unified карточки
        results_html = render_to_string('includes/partials/_unified_cards_wrapper.html', {
            'unified_card_list': unified_card_list,
            'empty_message': 'По вашему запросу ничего не найдено. Попробуйте изменить поисковый запрос.',
        })
        return JsonResponse({
            'success': True,
            'results_html': results_html,
            'results_count': len(results)
        })

    # Обычный запрос - полная страница
    return render(request, 'news/search_results.html', context)


@require_GET
def ajax_filter(request):
    """
    Унифицированный AJAX-обработчик новостей.
    Использует core.base_views.unified_ajax_filter для полного соответствия SSOT.
    """
    from core.base_views import unified_ajax_filter  # локальный импорт, чтобы избежать циклов
    return unified_ajax_filter(HomePageView)(request)
