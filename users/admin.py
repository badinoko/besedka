from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import User, BanRecord
from core.admin_site import owner_admin_site
from django import forms
from core.admin_mixins import UserAdminMixin, ModeratorAdminMixin
from django.contrib import messages

User._meta.verbose_name = 'Администратор'
User._meta.verbose_name_plural = 'Администраторы'

class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'telegram_id', 'role', 'name', 'is_active', 'is_banned')

# Inline для отображения банов пользователя
class BanRecordInline(admin.TabularInline):
    model = BanRecord
    extra = 0
    fk_name = 'user'  # Указываем, что используем поле 'user' как внешний ключ
    fields = ('ban_type', 'reason', 'created_at', 'expires_at', 'is_active')
    readonly_fields = ('created_at',)
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Только владелец платформы и модераторы могут добавлять баны
        return request.user.is_superuser or request.user.role in ('owner', 'moderator')

    def has_change_permission(self, request, obj=None):
        # Только владелец платформы и модераторы могут изменять баны
        return request.user.is_superuser or request.user.role in ('owner', 'moderator')

class SimpleRoleForm(forms.ModelForm):
    """Простая форма для назначения ролей пользователям"""

    # Создаем чекбоксы для ролей
    is_platform_admin = forms.BooleanField(
        label='🎭 Администратор платформы',
        required=False,
        help_text='Модерация контента, управление пользователями'
    )
    is_store_owner = forms.BooleanField(
        label='🏪 Владелец магазина',
        required=False,
        help_text='Полное управление магазином: склад, персонал, статистика'
    )
    is_store_admin = forms.BooleanField(
        label='📦 Администратор магазина',
        required=False,
        help_text='Только управление складом'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'is_active', 'is_banned']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Устанавливаем чекбоксы на основе текущей роли
            self.fields['is_platform_admin'].initial = (self.instance.role == 'moderator')
            self.fields['is_store_owner'].initial = (self.instance.role == 'store_owner')
            self.fields['is_store_admin'].initial = (self.instance.role == 'store_admin')

        # Убираем поля, которые не нужны
        self.fields['username'].help_text = 'Имя пользователя (логин)'
        self.fields['email'].help_text = 'Email адрес'
        self.fields['name'].help_text = 'Отображаемое имя'

    def clean(self):
        cleaned_data = super().clean()
        is_platform_admin = cleaned_data.get('is_platform_admin')
        is_store_owner = cleaned_data.get('is_store_owner')
        is_store_admin = cleaned_data.get('is_store_admin')

        # Проверяем что выбрана только одна роль
        roles_selected = sum([is_platform_admin, is_store_owner, is_store_admin])
        if roles_selected > 1:
            raise forms.ValidationError('Можно выбрать только одну роль!')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Определяем роль на основе чекбоксов
        if self.cleaned_data.get('is_platform_admin'):
            user.role = 'moderator'
            user.is_staff = True
        elif self.cleaned_data.get('is_store_owner'):
            user.role = 'store_owner'
            user.is_staff = True
        elif self.cleaned_data.get('is_store_admin'):
            user.role = 'store_admin'
            user.is_staff = True
        else:
            user.role = 'user'
            user.is_staff = False

        if commit:
            user.save()
        return user

class CustomUserAdmin(admin.ModelAdmin, UserAdminMixin):
    """Кастомная админка пользователей для владельца платформы"""
    list_display = ['username', 'name', 'role', 'telegram_username', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'name', 'telegram_username']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'name', 'telegram_username')
        }),
        ('Роль и права', {
            'fields': ('role', 'is_active', 'is_staff')
        }),
        ('Даты', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Защита владельца платформы от изменений"""
        readonly = list(self.readonly_fields)

        # КРИТИЧЕСКАЯ ЗАЩИТА: Владелец платформы не может изменить свою роль
        if obj and obj.username == 'owner_user':
            readonly.extend(['role', 'is_active', 'is_staff', 'username'])

        return readonly

    def has_delete_permission(self, request, obj=None):
        """КРИТИЧЕСКАЯ ЗАЩИТА: Запрещаем удаление владельца платформы"""
        if obj and obj.username == 'owner_user':
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        """КРИТИЧЕСКАЯ ЗАЩИТА: Предотвращаем случайные изменения владельца платформы"""
        if obj.username == 'owner_user':
            # Принудительно сохраняем критические поля для владельца платформы
            obj.role = 'owner'
            obj.is_active = True
            obj.is_staff = True
            obj.is_superuser = True

            if change:
                messages.warning(
                    request,
                    "⚠️ ВНИМАНИЕ: Аккаунт владельца платформы защищен от изменений. "
                    "Роль и статус автоматически восстановлены."
                )

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """КРИТИЧЕСКАЯ ЗАЩИТА: Блокируем удаление владельца платформы"""
        if obj.username == 'owner_user':
            messages.error(
                request,
                "🚫 КРИТИЧЕСКАЯ ОШИБКА: Нельзя удалить аккаунт владельца платформы! "
                "Это приведет к потере доступа к системе управления."
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """КРИТИЧЕСКАЯ ЗАЩИТА: Блокируем массовое удаление владельца платформы"""
        owner_in_queryset = queryset.filter(username='owner_user').exists()
        if owner_in_queryset:
            messages.error(
                request,
                "🚫 КРИТИЧЕСКАЯ ОШИБКА: В выборке есть аккаунт владельца платформы! "
                "Массовое удаление отменено для безопасности."
            )
            return
        super().delete_queryset(request, queryset)

    def get_form(self, request, obj=None, **kwargs):
        """Добавляем предупреждения в форму"""
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.username == 'owner_user':
            # Добавляем предупреждение в help_text
            if 'role' in form.base_fields:
                form.base_fields['role'].help_text = (
                    "🔒 ЗАЩИЩЕНО: Роль владельца платформы не может быть изменена"
                )
            if 'is_active' in form.base_fields:
                form.base_fields['is_active'].help_text = (
                    "🔒 ЗАЩИЩЕНО: Владелец платформы всегда должен быть активен"
                )

        return form

class BanRecordAdmin(admin.ModelAdmin, ModeratorAdminMixin):
    list_display = ('user', 'get_ban_type_display', 'reason_short', 'get_banned_by_display', 'created_at', 'expires_at', 'is_active')
    list_filter = ('ban_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__name', 'reason')
    readonly_fields = ('created_at', 'banned_by')
    actions = ['revoke_selected_bans']

    fieldsets = (
        (None, {
            'fields': ('user', 'ban_type', 'reason')
        }),
        (_('📅 Сроки'), {
            'fields': ('expires_at',),
            'description': 'Оставьте пустым для постоянного бана'
        }),
        (_('📋 Информация'), {
            'fields': ('created_at', 'banned_by', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    def get_ban_type_display(self, obj):
        """Красивое отображение типов банов с эмодзи"""
        ban_types = {
            'global': '🚫 Полный бан',
            'chat': '💬 Бан чата',
            'gallery': '🖼️ Бан галереи',
            'growlogs': '📝 Бан grow logs'
        }
        return ban_types.get(obj.ban_type, f'❓ {obj.ban_type}')
    get_ban_type_display.short_description = 'Тип бана'

    def reason_short(self, obj):
        """Короткая версия причины"""
        if len(obj.reason) > 50:
            return obj.reason[:50] + '...'
        return obj.reason
    reason_short.short_description = 'Причина'

    def get_banned_by_display(self, obj):
        """Кто выдал бан"""
        if obj.banned_by:
            return f'👤 {obj.banned_by.username}'
        return '❓ Неизвестно'
    get_banned_by_display.short_description = 'Забанил'

    def revoke_selected_bans(self, request, queryset):
        """Action to revoke selected bans."""
        for ban in queryset:
            ban.revoke(request.user)

        self.message_user(request, _("Selected bans have been revoked."))
    revoke_selected_bans.short_description = _("Revoke selected bans")

    def save_model(self, request, obj, form, change):
        if not change:  # Если создается новая запись
            obj.banned_by = request.user

        # Если это глобальный бан, обновляем статус пользователя
        if obj.ban_type == BanRecord.BAN_TYPE_GLOBAL and obj.is_active:
            obj.user.is_banned = True
            obj.user.save()

        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Владелец и админы платформы видят ВСЕ баны
        # Остальные не должны попадать в эту админку вообще
        return qs

    def has_add_permission(self, request):
        # Владелец платформы и модераторы могут добавлять баны
        return request.user.role in ('owner', 'moderator')

    def has_change_permission(self, request, obj=None):
        # Владелец платформы и модераторы могут изменять баны
        if request.user.role == 'owner':
            return True  # Владелец может изменять любые баны
        if request.user.role == 'moderator':
            # Админ может изменять любые баны, НО НЕ МОЖЕТ снять бан с себя
            if obj and obj.user == request.user and obj.banned_by != request.user:
                return False  # Админ не может снять с себя бан, который наложил owner
            return True  # Во всех остальных случаях админ может изменять баны
        return False

    def has_delete_permission(self, request, obj=None):
        # Владелец и модераторы платформы могут удалять баны
        # Но модератор не может удалить бан, который на него наложил owner
        if request.user.role == 'owner':
            return True
        if request.user.role == 'moderator':
            if obj and obj.user == request.user and obj.banned_by != request.user:
                return False  # Админ не может удалить свой бан от owner
            return True
        return False

# Регистрация в админке владельца платформы (ТОЛЬКО управление ролями)
owner_admin_site.register(User, CustomUserAdmin)
# Убираем баны из админки владельца - это функция модераторов!
# owner_admin_site.register(BanRecord, BanRecordAdmin)

# Регистрация в админке модератора (баны и модерация)
from core.admin_site import moderator_admin_site
moderator_admin_site.register(BanRecord, BanRecordAdmin)

# В админке магазина нет необходимости регистрировать этих моделей
# так как управление пользователями не входит в компетенцию магазина
