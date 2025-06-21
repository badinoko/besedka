from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, Http404
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .models import MaintenanceModeSetting
from django.apps import apps
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator
from django.views.generic import View
from django.contrib.contenttypes.models import ContentType
import json

# Create your views here.

@login_required
def admin_redirect(request):
    """
    Автоматически перенаправляет пользователей в соответствующую админку на основе их роли.
    """
    user = request.user

    # Проверяем, имеет ли пользователь право доступа к админке
    if not user.is_staff:
        return HttpResponseForbidden(_("У вас нет доступа к административной панели."))

    # Владелец платформы и админы платформы → админка владельца
    if user.role in ['owner', 'moderator']:
        return redirect('/owner_admin/')

    # Superuser без роли идет в стандартную админку
    elif user.is_superuser and not user.role:
        return redirect('/admin/')

    # Владелец магазина → админка владельца магазина
    elif user.role == 'store_owner':
        return redirect('/store_owner/')

    # Админы магазина → админка магазина
    elif user.role == 'store_admin':
        return redirect('/store_admin_site/')

    # Если роль не определена, но есть права staff → селектор
    elif user.is_staff:
        return redirect('/admin-selector/')

    # Если ничего не подходит
    return HttpResponseForbidden(_("Не удалось определить подходящую административную панель."))

@login_required
def admin_selector(request):
    """
    Представление для выбора административной панели в зависимости от прав доступа пользователя.
    """
    # Проверяем, имеет ли пользователь доступ к админке
    if not request.user.is_staff:
        return HttpResponseForbidden(_("У вас нет доступа к административной панели."))

    # Определяем, какие админки доступны пользователю
    admin_panels = []

    # Стандартная админка Django доступна только superuser
    if request.user.is_superuser:
        admin_panels.append({
            'name': _('Стандартная админка Django'),
            'url': '/admin/',
            'icon': 'fa-cog',
            'color': '#417690',
            'description': _('Стандартная административная панель Django.')
        })

    # Админка владельца платформы
    if request.user.is_superuser or getattr(request.user, 'role', None) in ['owner', 'moderator']:
        admin_panels.append({
            'name': _('Управление платформой Беседка'),
            'url': '/owner_admin/',
            'icon': 'fa-crown',
            'color': '#9c27b0',
            'description': _('Панель управления для владельца и администраторов платформы.')
        })

    # Админка магазина
    if request.user.is_superuser or getattr(request.user, 'role', None) in ['owner', 'moderator', 'store_owner', 'store_admin']:
        admin_panels.append({
                            'name': _('Управление магазином'),
            'url': '/store_admin_site/',
            'icon': 'fa-store',
            'color': '#2e7d32',
            'description': _('Панель управления магазином семян.')
        })

    # Если у пользователя доступна только одна админка, перенаправляем его туда
    if len(admin_panels) == 1:
        return redirect(admin_panels[0]['url'])

    return render(request, 'admin/admin_selector.html', {
        'admin_panels': admin_panels,
        'title': _('Выбор административной панели')
    })

def get_view_class_from_section(section_name):
    """
    Возвращает класс View на основе имени секции.
    Это центральный реестр, связывающий фронтенд и бэкенд.
    """
    if section_name == 'photo':
        from gallery.views import GalleryView
        return GalleryView
    elif section_name == 'growlog':
        from growlogs.views import GrowLogListView
        return GrowLogListView
    elif section_name == 'news':
        from news.views import HomePageView
        return HomePageView
    elif section_name == 'notifications':
        from users.views import NotificationListView
        return NotificationListView
    # Добавьте сюда другие секции по мере необходимости
    return None

@require_GET
def unified_list_ajax_filter(request, section_name):
    """
    ЕДИНЫЙ ГЛОБАЛЬНЫЙ AJAX-обработчик для всех списковых страниц.
    Использует `section_name` для динамического выбора нужного View и его логики.
    """
    ViewClass = get_view_class_from_section(section_name)
    if not ViewClass:
        return JsonResponse({'error': f'Section "{section_name}" not found'}, status=404)

    # Создаем экземпляр View, чтобы получить доступ к его методам
    view_instance = ViewClass()
    view_instance.request = request

    # Получаем отфильтрованный и отсортированный queryset
    queryset = view_instance.get_queryset()
    queryset = view_instance.apply_filters(queryset) # Применяем фильтры из View

    # Пагинация
    paginator = Paginator(queryset, view_instance.paginate_by)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Рендерим карточки и пагинацию в HTML
    cards_html = render_to_string('includes/partials/_unified_cards_wrapper.html', {
        'unified_card_list': view_instance.get_unified_cards(page_obj),
        'request': request
    })

    pagination_html = ""
    if page_obj.has_other_pages():
        pagination_html = render_to_string('includes/partials/_unified_pagination.html', {
            'page_obj': page_obj,
            'current_filter': request.GET.get('filter', 'all')
        })

    return JsonResponse({
        'success': True,
        'cards_html': cards_html,
        'pagination_html': pagination_html,
        'posts_count': paginator.count
    })

def maintenance_page_view(request, section_slug=None):
    """
    Отображает страницу технического обслуживания.
    Если section_slug передан, пытается найти конкретную настройку.
    Иначе, ищет настройку по текущему пути запроса (если это возможно определить).
    """
    maintenance_setting = None

    # Пытаемся найти настройку по section_slug, если он передан явно
    if section_slug:
        try:
            maintenance_setting = MaintenanceModeSetting.objects.get(section_name=section_slug, is_enabled=True)
        except MaintenanceModeSetting.DoesNotExist:
            pass # Если для конкретного section_slug нет активной настройки, это нормально

    # Если настройка не найдена по slug или slug не передан,
    # можно добавить логику определения раздела по request.path_info (если потребуется)
    # Например, если request.path_info.startswith('/chat/'), то section_slug = 'chat'
    # Но это усложнит и потребует четкого маппинга URL на section_name

    # Если ни одна конкретная настройка не активна, но мы попали на эту view,
    # возможно, это общий вызов или ошибка. Можно показать дефолтное сообщение.
    if not maintenance_setting:
        # Это состояние не должно возникать, если middleware работает правильно
        # и перенаправляет только для активных настроек.
        # В качестве fallback, можно создать "общую" заглушку или редиректить на главную.
        # Пока что, если мы сюда попали без maintenance_setting, покажем базовую заглушку.
        # В идеале, middleware должен передавать section_slug.
        maintenance_setting = MaintenanceModeSetting(
            title="Техническое обслуживание",
            message="Один из разделов сайта находится на техническом обслуживании.",
            color_scheme='blue'
        )

    available_sections = []
    all_settings = MaintenanceModeSetting.objects.all()
    section_to_url_map = {
        'gallery': 'gallery:gallery', # Пример, нужно будет заменить на актуальные URL names
        'growlogs': 'growlogs:list',  # Пример
        'store': 'store:product_list',  # Пример
        # Чат пока не имеет основного списка, можно ссылку на главную или пропустить
    }

    for setting_choice_val, setting_choice_disp in MaintenanceModeSetting.SECTION_CHOICES:
        # Проверяем, что раздел не является текущим обслуживаемым
        if maintenance_setting and setting_choice_val == maintenance_setting.section_name:
            continue

        # Проверяем, что раздел НЕ находится на обслуживании (is_enabled=False)
        try:
            other_section_setting = all_settings.get(section_name=setting_choice_val)
            if not other_section_setting.is_enabled:
                if setting_choice_val in section_to_url_map:
                    try:
                        url = reverse(section_to_url_map[setting_choice_val])
                        available_sections.append((setting_choice_val, url, setting_choice_disp))
                    except Exception: # NoReverseMatch
                        pass # Если URL не найден, не добавляем
        except MaintenanceModeSetting.DoesNotExist:
            # Если настройки для раздела нет, считаем его доступным (если есть URL)
            if setting_choice_val in section_to_url_map:
                try:
                    url = reverse(section_to_url_map[setting_choice_val])
                    available_sections.append((setting_choice_val, url, setting_choice_disp))
                except Exception:
                    pass

    context = {
        'maintenance_setting': maintenance_setting,
        'available_sections': available_sections,
        'title': maintenance_setting.title
    }
    return render(request, 'core/maintenance_page.html', context)

@login_required
@require_POST
def unified_like_api(request):
    """
    Унифицированный API для лайков всех типов объектов.
    Поддерживает:
    - Галерея: Photo с ManyToManyField likes
    - Гроурепорты: GrowLog с ManyToManyField likes (необратимо)
    - Новости: Post с системой Reaction
    ✅ ДОБАВЛЕНО: Проверка авторства - автор не может лайкнуть свой контент
    """
    try:
        data = json.loads(request.body)
        object_type = data.get('object_type')  # 'photo', 'growlog', 'post'
        object_id = data.get('object_id')
        action = data.get('action', 'toggle')  # 'toggle', 'like', 'unlike'

        if not object_type or not object_id:
            return JsonResponse({'error': 'Отсутствуют обязательные параметры'}, status=400)

        # Определяем модель и объект
        model_map = {
            'photo': 'gallery.Photo',
            'growlog': 'growlogs.GrowLog',
            'post': 'news.Post'
        }

        if object_type not in model_map:
            return JsonResponse({'error': 'Неподдерживаемый тип объекта'}, status=400)

        model_path = model_map[object_type]
        app_label, model_name = model_path.split('.')
        Model = apps.get_model(app_label, model_name)
        obj = get_object_or_404(Model, pk=object_id)

        # ✅ НОВОЕ: Проверка авторства - автор не может лайкнуть свой контент
        is_author = False
        if hasattr(obj, 'author') and obj.author == request.user:
            is_author = True
        elif hasattr(obj, 'user') and obj.user == request.user:
            is_author = True
        elif hasattr(obj, 'owner') and obj.owner == request.user:
            is_author = True

        if is_author:
            return JsonResponse({
                'success': True,
                'action': 'cannot_like_own',
                'likes_count': getattr(obj, 'likes', obj.__class__.objects.none()).count() if hasattr(obj, 'likes') else 0,
                'user_liked': False,
                'object_type': object_type,
                'object_id': object_id,
                'message': 'Нельзя лайкнуть собственный контент'
            })

        # Обработка по типу объекта
        if object_type in ['photo', 'growlog']:
            # Простая система ManyToManyField likes
            user_liked = obj.likes.filter(id=request.user.id).exists()

            # ВСЕ лайки теперь необратимые (photo, growlog)
            if not user_liked:
                obj.likes.add(request.user)
                action_performed = 'liked'
            else:
                action_performed = 'already_liked'

            likes_count = obj.likes.count()
            user_liked_after = obj.likes.filter(id=request.user.id).exists()

        elif object_type == 'post':
            # Система Reaction для новостей
            from news.models import Reaction

            reaction_type = data.get('reaction_type', 'like')
            if reaction_type not in dict(Reaction.REACTION_TYPES):
                return JsonResponse({'error': 'Неверный тип реакции'}, status=400)

            existing_reaction = Reaction.objects.filter(post=obj, user=request.user).first()

            if existing_reaction:
                # Реакция уже есть - лайки необратимы
                action_performed = 'already_liked'
            else:
                # Добавляем новую реакцию
                Reaction.objects.create(post=obj, user=request.user, reaction_type=reaction_type)
                action_performed = 'liked'

            # Подсчитываем лайки (только тип 'like')
            likes_count = Reaction.objects.filter(post=obj, reaction_type='like').count()
            user_liked_after = Reaction.objects.filter(post=obj, user=request.user, reaction_type='like').exists()

        return JsonResponse({
            'success': True,
            'action': action_performed,
            'likes_count': likes_count,
            'user_liked': user_liked_after,
            'object_type': object_type,
            'object_id': object_id
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
