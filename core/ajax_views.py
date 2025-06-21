from django.http import JsonResponse, Http404
from django.core.paginator import Paginator, EmptyPage
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from core.constants import COMMENTS_PAGE_SIZE
from news.models import Post
from gallery.models import Photo
from growlogs.models import GrowLog

COMMENTABLE_MODELS = {
    'post': Post,
    'photo': Photo,
    'growlog': GrowLog,
}

@require_GET
def load_comments(request):
    """Унифицированный AJAX-обработчик для постраничной подгрузки top-level комментариев."""
    object_type = request.GET.get('type')
    object_id = request.GET.get('id')
    page_number = request.GET.get('page', 1)

    if object_type not in COMMENTABLE_MODELS or not object_id:
        return JsonResponse({'success': False, 'message': 'Некорректные параметры.'}, status=400)

    model = COMMENTABLE_MODELS[object_type]
    try:
        obj = model.objects.get(pk=object_id)
    except model.DoesNotExist:
        raise Http404

    # получаем QuerySet только top-level
    comments_qs = (obj.comments.filter(parent__isnull=True)
                   .select_related('author')
                   .prefetch_related('replies__author')
                   .order_by('-created_at'))

    paginator = Paginator(comments_qs, COMMENTS_PAGE_SIZE)
    try:
        page = paginator.page(page_number)
    except EmptyPage:
        return JsonResponse({'success': False, 'message': 'Страница не найдена.'}, status=404)

    html = render_to_string(
        'includes/partials/unified_comments_list.html',
        {'top_level_comments': page.object_list},
        request=request,
    )

    return JsonResponse({
        'success': True,
        'comments_html': html,
        'has_next': page.has_next(),
        'next_page': page.next_page_number() if page.has_next() else None,
    })
