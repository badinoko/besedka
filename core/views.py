from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .models import MaintenanceModeSetting

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
    if user.role in ['owner', 'admin']:
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
    if request.user.is_superuser or getattr(request.user, 'role', None) in ['owner', 'admin']:
        admin_panels.append({
            'name': _('Управление платформой Беседка'),
            'url': '/owner_admin/',
            'icon': 'fa-crown',
            'color': '#9c27b0',
            'description': _('Панель управления для владельца и администраторов платформы.')
        })

    # Админка магазина
    if request.user.is_superuser or getattr(request.user, 'role', None) in ['owner', 'admin', 'store_owner', 'store_admin']:
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
