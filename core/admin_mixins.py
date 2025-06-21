"""
Базовые миксины для всех админок проекта Besedka
"""
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.db import models


class BaseAdminMixin:
    """
    Универсальный миксин для всех админок проекта:
    - Добавляет кнопку ОТМЕНА во все формы
    - Улучшает UX с единым поведением
    - Автовозврат к списку после сохранения (опционально)
    """

    # Настройки поведения (можно переопределить в дочерних классах)
    auto_return_to_list = False  # Автовозврат к списку после сохранения
    show_cancel_button = True    # Показывать кнопку ОТМЕНА

    def response_add(self, request, obj, post_url_continue=None):
        """
        После создания объекта - возврат к списку или стандартное поведение
        """
        if self.auto_return_to_list:
            return self._redirect_to_changelist(request)
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        """
        После изменения объекта - возврат к списку или стандартное поведение
        """
        if self.auto_return_to_list:
            return self._redirect_to_changelist(request)
        return super().response_change(request, obj)

    def _redirect_to_changelist(self, request):
        """
        Универсальная функция возврата к списку БЕЗ сохранения фильтров
        """
        opts = self.model._meta
        redirect_url = reverse(
            f'{self.admin_site.name}:{opts.app_label}_{opts.model_name}_changelist',
            current_app=self.admin_site.name,
        )
        return HttpResponseRedirect(redirect_url)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        Добавляем кнопку ОТМЕНА в контекст формы + правильный URL возврата
        """
        if self.show_cancel_button:
            # Создаем правильный URL для возврата к списку модели
            opts = self.model._meta
            cancel_url = reverse(
                f'{self.admin_site.name}:{opts.app_label}_{opts.model_name}_changelist',
                current_app=self.admin_site.name,
            )

            context.update({
                'show_cancel': True,        # Наш флаг для шаблона
                'cancel_url': cancel_url,   # Правильный URL для кнопки ОТМЕНА
            })
        return super().render_change_form(request, context, add, change, form_url, obj)


class StoreAdminMixin(BaseAdminMixin):
    """
    Специализированный миксин для админок магазина:
    - Включает адаптивные стили
    - Автовозврат к списку после сохранения
    - Убирает лишние кнопки сохранения
    - ПРАВИЛЬНАЯ логика кнопки ОТМЕНА
    - ПОЛНЫЕ ПРАВА для ролей store_owner и store_admin
    """

    auto_return_to_list = True  # Для магазина всегда возвращаемся к списку

    class Media:
        css = {
            'all': ('admin/css/responsive_admin.css',)
        }
        js = ('admin/js/responsive_admin.js',)

    def has_view_permission(self, request, obj=None):
        """Разрешаем просмотр для ролей магазина"""
        if hasattr(request.user, 'role') and request.user.role in ['store_owner', 'store_admin']:
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        """Разрешаем добавление для ролей магазина"""
        if hasattr(request.user, 'role') and request.user.role in ['store_owner', 'store_admin']:
            return True
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        """Разрешаем изменение для ролей магазина"""
        if hasattr(request.user, 'role') and request.user.role in ['store_owner', 'store_admin']:
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Разрешаем удаление для ролей магазина (кроме store_admin для критических данных)"""
        if hasattr(request.user, 'role'):
            if request.user.role == 'store_owner':
                return True  # Владелец может удалять всё
            elif request.user.role == 'store_admin':
                # Администратор магазина не может удалять критические данные
                critical_models = ['Order', 'OrderItem', 'SalesReport', 'InventoryReport']
                if hasattr(self, 'model') and self.model.__name__ in critical_models:
                    return False
                return True
        return super().has_delete_permission(request, obj)

    def has_module_permission(self, request):
        """Разрешаем доступ к модулю для ролей магазина"""
        if hasattr(request.user, 'role') and request.user.role in ['store_owner', 'store_admin']:
            return True
        return super().has_module_permission(request)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        Настройки специально для магазина + счетчики остатков
        """
        # Добавляем информацию о остатках для StockItem
        if hasattr(self, 'model') and self.model.__name__ == 'StockItem':
            # Подсчитываем общие остатки
            from magicbeans_store.models import StockItem
            total_items = StockItem.objects.filter(is_active=True).count()
            total_seeds = StockItem.objects.filter(is_active=True).aggregate(
                total=models.Sum('seeds_count')
            )['total'] or 0

            context.update({
                'stock_stats': {
                    'total_items': total_items,
                    'total_seeds': total_seeds,
                }
            })

        # Основные настройки
        context.update({
            'show_save_and_add_another': False,  # Убираем "Сохранить и добавить другой"
            'show_save_and_continue': False,     # Убираем "Сохранить и продолжить"
            'show_save': True,                   # Оставляем только основную кнопку
            'show_cancel': True,                 # Добавляем кнопку ОТМЕНА
        })
        return super().render_change_form(request, context, add, change, form_url, obj)


class ModeratorAdminMixin(BaseAdminMixin):
    """
    Миксин для админок модератора (grow logs, галерея, пользователи)
    """
    auto_return_to_list = False  # Модератор может хотеть продолжить редактирование


class UserAdminMixin(BaseAdminMixin):
    """
    Миксин для управления пользователями
    """
    auto_return_to_list = False  # При работе с пользователями может понадобиться остаться
