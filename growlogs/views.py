from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.db.models import Count
from django.db.models import F
from django.template.loader import render_to_string  # Для рендеринга HTML фрагментов в AJAX

from .models import GrowLog, GrowLogComment
from .forms import GrowLogCreateForm as GrowLogForm, GrowLogCommentForm
from core.base_views import UnifiedListView, unified_ajax_filter
from core.constants import COMMENTS_PAGE_SIZE
from core.utils import get_limited_top_level_comments, get_total_comments_count

# ==========================================================================
# 1. ОСНОВНОЙ КЛАСС ОТОБРАЖЕНИЯ ГРОУРЕПОРТОВ (УНИФИЦИРОВАН)
# ==========================================================================
class GrowLogListView(UnifiedListView):
    """
    Список гроу-репортов - УНИФИЦИРОВАННАЯ ВЕРСИЯ
    """
    model = GrowLog
    template_name = 'base_list_page.html'
    context_object_name = 'page_obj'
    paginate_by = 9

    # УНИФИЦИРОВАННЫЕ НАСТРОЙКИ
    section_title = "Гроурепорты сообщества"
    section_subtitle = "Делитесь опытом выращивания и изучайте техники других гроверов"
    section_hero_class = "growlogs-hero"
    card_type = "growlog"

    def get_queryset(self):
        """Возвращает queryset с учётом фильтров.

        Ранее метод возвращал только базовый список активных гроурепортов, не
        учитывая выбранный фильтр («Популярные», «Обсуждаемые», «Мои
        репорты»). Теперь результат обязательно пропускается через
        self.apply_filters().
        """

        base_qs = (
            GrowLog.objects.filter(is_active=True)
            .select_related("grower", "strain")
        )

        return self.apply_filters(base_qs)

    def apply_filters(self, queryset):
        """Применяет фильтрацию для гроурепортов."""
        filter_type = self.request.GET.get('filter', 'all')

        if filter_type == 'popular':
            queryset = queryset.annotate(likes_count=Count('likes')).order_by('-likes_count', '-created_at')
        elif filter_type == 'commented':
            queryset = queryset.annotate(comments_count=Count('comments')).order_by('-comments_count', '-created_at')
        elif filter_type == 'my_growlogs' and self.request.user.is_authenticated:
            queryset = queryset.filter(grower=self.request.user).order_by('-created_at')
        else: # all
            queryset = queryset.order_by('-created_at')
        return queryset

    def get_hero_stats(self):
        """Статистика для hero-секции"""
        active_growlogs = GrowLog.objects.filter(is_active=True)
        return [
            {'value': active_growlogs.count(), 'label': 'Репортов'},
            {'value': active_growlogs.values('grower').distinct().count(), 'label': 'Гроверов'},
        ]

    def get_hero_actions(self):
        """Кнопки действий для гроу-репортов"""
        if self.request.user.is_authenticated:
            return [
                {'url': reverse_lazy('growlogs:create'), 'label': 'Создать репорт', 'is_primary': True, 'icon': 'fas fa-plus-circle'},
            ]
        else:
            return []

    def get_filter_list(self):
        """Фильтры для гроу-репортов"""
        filter_list = [
            {'id': 'all', 'label': 'Все репорты'},
            {'id': 'popular', 'label': 'Популярные'},
            {'id': 'commented', 'label': 'Обсуждаемые'},
        ]
        if self.request.user.is_authenticated:
            filter_list.append({'id': 'my_growlogs', 'label': 'Мои репорты'})
        return filter_list

# ==========================================================================
# 2. AJAX-ОБРАБОТЧИК ФИЛЬТРАЦИИ (НОВЫЙ, УНИФИЦИРОВАННЫЙ)
# ==========================================================================
@require_GET
def ajax_filter(request):
    """Унифицированный AJAX-обработчик для списка гроурепортов (SSOT)."""
    return unified_ajax_filter(GrowLogListView)(request)

# ==========================================================================
# 3. VIEWS ДЛЯ КОНКРЕТНОГО ГРОУРЕПОРТА И ДЕЙСТВИЙ
# ==========================================================================

class GrowLogDetailView(DetailView):
    model = GrowLog
    template_name = 'growlogs/detail.html'
    context_object_name = 'growlog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = GrowLogCommentForm()
        if self.request.user.is_authenticated:
            context['user_liked'] = self.object.likes.filter(pk=self.request.user.pk).exists()
        else:
            context['user_liked'] = False

        # Получаем ограниченный набор комментариев верхнего уровня с учётом вложенных
        selected, displayed_blocks, total_root = get_limited_top_level_comments(
            self.object,
            comment_relation="comments",
            block_limit=COMMENTS_PAGE_SIZE,
        )

        context['top_level_comments'] = selected

        # Полное количество комментариев (включая ответы) для счётчиков в интерфейсе
        total_comments = get_total_comments_count(self.object)
        context['comments_count'] = total_comments
        setattr(self.object, 'comments_count', total_comments)

        # Показываем кнопку «Показать ещё», только если остались невыведенные КОРНЕВЫЕ комментарии.
        context['has_more_comments'] = total_root > len(selected)

        # Для совместимости со старым кодом (если где-то используется)
        context['comments'] = context['top_level_comments']

        # Статистика для унифицированной hero-секции
        context['detail_hero_stats'] = [
            {'value': self.object.entries.count(), 'label': 'дней', 'css_class': 'days'},
            {'value': self.object.likes.count(), 'label': 'лайков', 'css_class': 'likes'},
            {'value': total_comments, 'label': 'комментариев', 'css_class': 'comments'},
        ]

        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Инкрементируем счётчик просмотров только один раз за сессию
        viewed_key = f"viewed_growlog_{obj.pk}"
        if not self.request.session.get(viewed_key, False) and self.request.user != obj.grower:
            GrowLog.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
            obj.refresh_from_db(fields=['views_count'])
            self.request.session[viewed_key] = True
        return obj

class GrowLogCreateView(LoginRequiredMixin, CreateView):
    model = GrowLog
    form_class = GrowLogForm
    template_name = 'growlogs/form.html'
    success_url = reverse_lazy('growlogs:list')

    def form_valid(self, form):
        form.instance.grower = self.request.user
        messages.success(self.request, "Гроу-репорт успешно создан!")
        return super().form_valid(form)

class GrowLogUpdateView(LoginRequiredMixin, UpdateView):
    model = GrowLog
    form_class = GrowLogForm
    template_name = 'growlogs/form.html'

    def get_queryset(self):
        # Только владелец может редактировать свой репорт
        if self.request.user.is_authenticated:
            return GrowLog.objects.filter(grower=self.request.user)
        return GrowLog.objects.none()

    def get_success_url(self):
        messages.success(self.request, "Гроу-репорт обновлен.")
        return reverse_lazy('growlogs:detail', kwargs={'pk': self.object.pk})

class GrowLogDeleteView(LoginRequiredMixin, DeleteView):
    model = GrowLog
    template_name = 'growlogs/delete_confirm.html'
    success_url = reverse_lazy('growlogs:list')

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return GrowLog.objects.filter(grower=self.request.user)
        return GrowLog.objects.none()

    def form_valid(self, form):
        messages.success(self.request, "Гроу-репорт удален.")
        return super().form_valid(form)

@login_required
@require_POST
def toggle_like_growlog(request, pk):
    """
    AJAX-обработчик для лайков. Лайк НЕОБРАТИМ согласно BESEDKA_UI_STANDARDS.md.
    """
    growlog = get_object_or_404(GrowLog, pk=pk)

    # Добавляем лайк, если его еще нет.
    if not growlog.likes.filter(pk=request.user.pk).exists():
        growlog.likes.add(request.user)

    return JsonResponse({'success': True, 'liked': True, 'count': growlog.likes.count()})

@login_required
@require_POST
def add_growlog_comment(request, pk):
    """AJAX-обработчик для добавления комментариев к гроурепорту."""
    growlog = get_object_or_404(GrowLog, pk=pk)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = GrowLogCommentForm(request.POST)
        parent_id = request.POST.get('parent_id')
        if form.is_valid():
            comment = form.save(commit=False)
            comment.growlog = growlog
            comment.author = request.user

            # Обрабатываем вложенные комментарии
            if parent_id:
                try:
                    parent_comment = GrowLogComment.objects.get(pk=parent_id, growlog=growlog)

                    # Ограничиваем глубину вложенности до 3 уровней (два предка максимум у родительского комментария)
                    if parent_comment.parent is not None and parent_comment.parent.parent is not None:
                        pass  # Превышен лимит – игнорируем parent, оставляем топ-уровнем
                    else:
                        comment.parent = parent_comment
                except GrowLogComment.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Родительский комментарий не найден.'}, status=404)

            comment.save()

            # После сохранения рендерим обновлённый список комментариев с тем же контекстом,
            # чтобы вернуть свежий HTML без вызова QuerySet в шаблоне.
            comments_html = render_to_string(
                'includes/partials/unified_comments_list.html',
                {
                    'growlog': growlog,
                    'top_level_comments': growlog.comments.filter(parent__isnull=True)
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
                'comments_count': get_total_comments_count(growlog),
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    # Fallback на обычный POST без AJAX – редиректим
    form = GrowLogCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.growlog = growlog
        comment.author = request.user

        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_comment = GrowLogComment.objects.get(pk=parent_id, growlog=growlog)
                # Ограничиваем глубину вложенности до 3 уровней (два предка максимум у родительского комментария)
                if parent_comment.parent is not None and parent_comment.parent.parent is not None:
                    pass  # Превышен лимит – игнорируем parent, оставляем топ-уровнем
                else:
                    comment.parent = parent_comment
            except GrowLogComment.DoesNotExist:
                pass

        comment.save()
        messages.success(request, "Комментарий успешно добавлен.")
    else:
        messages.error(request, "Ошибка при добавлении комментария.")
    return redirect(growlog.get_absolute_url())
