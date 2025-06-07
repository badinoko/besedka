from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
import json

from .models import Post, Category, Tag, Comment, Reaction, Poll, PollChoice, PollVote, PostView
from .forms import CommentForm


class HomePageView(ListView):
    """Главная страница - новостная лента"""
    model = Post
    template_name = 'news/home.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        # Получаем только опубликованные посты
        queryset = Post.published.select_related('author', 'category').prefetch_related('tags')

        # Фильтрация по GET параметрам
        filter_type = self.request.GET.get('filter', 'all')

        if filter_type == 'articles':
            queryset = queryset.filter(post_type='article')
        elif filter_type == 'polls':
            queryset = queryset.filter(post_type='poll')
        elif filter_type == 'videos':
            queryset = queryset.filter(post_type='video')
        elif filter_type == 'pinned':
            queryset = queryset.filter(is_pinned=True)

        # Сначала закрепленные, потом обычные по дате
        return queryset.order_by('-is_pinned', '-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Добавляем категории для навигации
        context['categories'] = Category.objects.annotate(
            posts_count=Count('post', filter=Q(post__status='published'))
        ).filter(posts_count__gt=0)

        # Добавляем популярные теги
        context['popular_tags'] = Tag.objects.annotate(
            posts_count=Count('post', filter=Q(post__status='published'))
        ).filter(posts_count__gt=0).order_by('-posts_count')[:10]

        # Статистика для hero-секции
        context['total_posts'] = Post.published.count()
        context['total_categories'] = Category.objects.annotate(
            posts_count=Count('post', filter=Q(post__status='published'))
        ).filter(posts_count__gt=0).count()
        context['total_views'] = Post.published.aggregate(
            total=Count('post_views')
        )['total'] or 0

        # Текущий фильтр
        context['current_filter'] = self.request.GET.get('filter', 'all')

        return context


class PostDetailView(DetailView):
    """Детальная страница поста"""
    model = Post
    template_name = 'news/post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # Показываем только опубликованные посты
        return Post.published.select_related('author', 'category').prefetch_related('tags')

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
            # Увеличиваем счетчик
            Post.objects.filter(id=post.id).update(views_count=F('views_count') + 1)

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

        # Комментарии
        comments = Comment.objects.filter(post=post, parent=None).select_related('author').order_by('created_at')
        context['comments'] = comments
        context['comment_form'] = CommentForm()

        # Реакции
        context['reactions_summary'] = self.get_reactions_summary(post)

        # Если пользователь авторизован, получаем его реакцию
        if self.request.user.is_authenticated:
            user_reaction = Reaction.objects.filter(post=post, user=self.request.user).first()
            context['user_reaction'] = user_reaction.reaction_type if user_reaction else None

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
                    parent_comment = Comment.objects.get(id=parent_id, post=self.object)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass

            comment.save()
            messages.success(request, 'Комментарий добавлен!')

            return redirect(self.object.get_absolute_url() + '#comments')
        else:
            messages.error(request, 'Ошибка при добавлении комментария.')

        return self.get(request, *args, **kwargs)


class CategoryPostListView(ListView):
    """Список постов по категории"""
    model = Post
    template_name = 'news/category_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Post.published.filter(category=self.category).select_related('author', 'category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class TagPostListView(ListView):
    """Список постов по тегу"""
    model = Post
    template_name = 'news/tag_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return Post.published.filter(tags=self.tag).select_related('author', 'category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
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


@require_GET
def filter_news_ajax(request):
    """AJAX-обработчик для фильтрации новостей"""
    try:
        filter_type = request.GET.get('filter', 'all')
        page = request.GET.get('page', 1)

        # Базовый queryset
        queryset = Post.published.select_related('author', 'category').prefetch_related('tags')

        # Применяем фильтр
        if filter_type == 'articles':
            queryset = queryset.filter(post_type='article')
        elif filter_type == 'polls':
            queryset = queryset.filter(post_type='poll')
        elif filter_type == 'videos':
            queryset = queryset.filter(post_type='video')
        elif filter_type == 'pinned':
            queryset = queryset.filter(is_pinned=True)

        # Сортировка
        queryset = queryset.order_by('-is_pinned', '-published_at')

        # Пагинация
        paginator = Paginator(queryset, 10)
        try:
            posts_page = paginator.page(page)
        except:
            posts_page = paginator.page(1)

        # Рендерим только карточки новостей
        posts_html = render_to_string('news/partials/news_cards.html', {
            'posts': posts_page,
            'user': request.user
        })

        # Рендерим пагинацию
        pagination_html = render_to_string('news/partials/pagination.html', {
            'posts': posts_page,
            'current_filter': filter_type
        }) if posts_page.has_other_pages() else ''

        return JsonResponse({
            'success': True,
            'posts_html': posts_html,
            'pagination_html': pagination_html,
            'posts_count': posts_page.paginator.count
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def add_comment(request):
    """AJAX-обработчик для добавления комментариев"""
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')

        if not post_id or not content:
            return JsonResponse({'error': 'Не указаны обязательные поля'}, status=400)

        post = get_object_or_404(Post, id=post_id)

        # Создаем комментарий
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )

        # Если это ответ на комментарий
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id, post=post)
                comment.parent = parent_comment
                comment.save()
            except Comment.DoesNotExist:
                pass

        # Рендерим новый комментарий
        comment_html = render_to_string('news/partials/comment.html', {
            'comment': comment,
            'user': request.user
        })

        return JsonResponse({
            'success': True,
            'comment_html': comment_html,
            'comment_id': comment.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
    """Поиск по постам"""
    query = request.GET.get('q', '').strip()
    results = []

    if query and len(query) >= 2:
        # Поиск по заголовку, контенту и тегам
        posts = Post.published.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().select_related('author', 'category')[:20]

        results = posts

    context = {
        'query': query,
        'results': results,
        'results_count': len(results)
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX запрос - возвращаем только результаты
        results_html = render_to_string('news/partials/search_results.html', context)
        return JsonResponse({
            'success': True,
            'results_html': results_html,
            'results_count': len(results)
        })

    # Обычный запрос - полная страница
    return render(request, 'news/search.html', context)
