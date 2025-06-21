from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Room, Message, Thread, Tag, DiscussionRoom, VIPChatRoom, VIPChatMembership, GlobalChatRoom
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django import forms


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created')
    list_filter = ('created',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created', 'modified')
    fields = ('author', 'content', 'reply_to', 'unread', 'is_edited', 'created')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_private', 'is_discussion', 'muted', 'history_cleared', 'created', 'modified')
    list_filter = ('is_private', 'is_discussion', 'muted', 'history_cleared', 'created')
    search_fields = ('id',)
    filter_horizontal = ('connected_clients',)
    readonly_fields = ('created', 'modified')
    ordering = ('-modified',)
    inlines = [MessageInline]

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('is_private', 'is_discussion', 'muted', 'history_cleared')
        }),
        (_('Подключенные пользователи'), {
            'fields': ('connected_clients',),
            'classes': ('collapse',)
        }),
        (_('Временные метки'), {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'room', 'content_preview', 'unread', 'is_edited', 'created')
    list_filter = ('unread', 'is_edited', 'created', 'room__is_private', 'room__is_discussion')
    search_fields = ('content', 'author__username', 'author__first_name', 'author__last_name')
    readonly_fields = ('created', 'modified')
    raw_id_fields = ('author', 'room', 'reply_to')
    ordering = ('-created',)

    @admin.display(description=_('Превью содержимого'))
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('author', 'room', 'content')
        }),
        (_('Связи'), {
            'fields': ('reply_to',),
            'classes': ('collapse',)
        }),
        (_('Статус'), {
            'fields': ('unread', 'is_edited')
        }),
        (_('Временные метки'), {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'room', 'created_date')
    list_filter = ('room__created',)
    search_fields = ('user1__username', 'user1__first_name', 'user1__last_name',
                    'user2__username', 'user2__first_name', 'user2__last_name')
    raw_id_fields = ('room', 'user1', 'user2')
    readonly_fields = ('id',)
    ordering = ('-room__modified',)

    @admin.display(description=_('Дата создания'), ordering='room__created')
    def created_date(self, obj):
        return obj.room.created

    fieldsets = (
        (_('Участники'), {
            'fields': ('user1', 'user2')
        }),
        (_('Комната'), {
            'fields': ('room',)
        }),
        (_('Идентификатор'), {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DiscussionRoom)
class DiscussionRoomAdmin(admin.ModelAdmin):
    list_display = ('headline', 'owner', 'members_count', 'tags_list', 'created', 'modified')
    list_filter = ('created', 'modified', 'tags')
    search_fields = ('headline', 'description', 'owner__username', 'tags__name')
    filter_horizontal = ('members', 'tags')
    prepopulated_fields = {'slug': ('headline',)}
    raw_id_fields = ('owner', 'room')
    readonly_fields = ('created', 'modified', 'messages_dump')
    ordering = ('-modified',)

    @admin.display(description=_('Участников'))
    def members_count(self, obj):
        return obj.members.count()

    @admin.display(description=_('Теги'))
    def tags_list(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()[:3]])

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('headline', 'slug', 'description', 'owner', 'room')
        }),
        (_('Участники и теги'), {
            'fields': ('members', 'tags')
        }),
        (_('Поиск'), {
            'fields': ('messages_dump',),
            'classes': ('collapse',)
        }),
        (_('Временные метки'), {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


class VIPChatMembershipInline(admin.TabularInline):
    """Инлайн для управления участниками VIP-чата"""
    model = VIPChatMembership
    extra = 0
    readonly_fields = ('invited_at', 'accepted_at')
    fields = ('user', 'invited_by', 'is_active', 'invited_at', 'accepted_at')
    raw_id_fields = ('user', 'invited_by')


@admin.register(VIPChatRoom)
class VIPChatRoomAdmin(admin.ModelAdmin):
    """Админка для управления VIP-чатом"""
    list_display = ('name', 'created_by', 'members_count', 'is_active', 'created')
    list_filter = ('is_active', 'created')
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('created', 'modified')
    raw_id_fields = ('created_by', 'room')
    inlines = [VIPChatMembershipInline]
    ordering = ('-created',)

    @admin.display(description=_('Участников'))
    def members_count(self, obj):
        return obj.members.count()

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'description', 'created_by', 'is_active')
        }),
        (_('Комната'), {
            'fields': ('room',)
        }),
        (_('Временные метки'), {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Показываем только VIP-чаты, доступные текущему пользователю"""
        qs = super().get_queryset(request)
        if request.user.role in ['owner', 'admin']:
            return qs
        return qs.none()


@admin.register(VIPChatMembership)
class VIPChatMembershipAdmin(admin.ModelAdmin):
    """Админка для управления участниками VIP-чата"""
    list_display = ('vip_chat', 'user', 'invited_by', 'is_active', 'invited_at', 'accepted_at')
    list_filter = ('is_active', 'invited_at', 'accepted_at', 'vip_chat')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
                    'invited_by__username', 'vip_chat__name')
    readonly_fields = ('invited_at', 'accepted_at')
    raw_id_fields = ('vip_chat', 'user', 'invited_by')
    ordering = ('-invited_at',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('vip_chat', 'user', 'invited_by', 'is_active')
        }),
        (_('Временные метки'), {
            'fields': ('invited_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Показываем только участников VIP-чатов, доступных текущему пользователю"""
        qs = super().get_queryset(request)
        if request.user.role in ['owner', 'admin']:
            return qs
        return qs.none()


@admin.register(GlobalChatRoom)
class GlobalChatRoomAdmin(admin.ModelAdmin):
    """Админка для управления общим чатом"""
    list_display = ('name', 'is_active', 'auto_add_users', 'created')
    list_filter = ('is_active', 'auto_add_users', 'created')
    search_fields = ('name', 'description')
    readonly_fields = ('created', 'modified')
    raw_id_fields = ('room',)
    ordering = ('-created',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'description', 'is_active', 'auto_add_users')
        }),
        (_('Комната'), {
            'fields': ('room',)
        }),
        (_('Временные метки'), {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Показываем только владельцам платформы"""
        qs = super().get_queryset(request)
        if request.user.role == 'owner':
            return qs
        return qs.none()


# Настройка заголовков админки
admin.site.site_header = _('Администрирование чата "Беседка"')
admin.site.site_title = _('Чат "Беседка"')
admin.site.index_title = _('Управление чатом сообщества')

# Регистрация в админке модератора для модерации
from core.admin_site import moderator_admin_site
from core.admin_mixins import ModeratorAdminMixin

class ModeratorMessageAdmin(MessageAdmin, ModeratorAdminMixin):
    """Админка сообщений для модераторов"""
    pass

class ModeratorRoomAdmin(RoomAdmin, ModeratorAdminMixin):
    """Админка комнат для модераторов"""
    pass

moderator_admin_site.register(Message, ModeratorMessageAdmin)
moderator_admin_site.register(Room, ModeratorRoomAdmin)

# Регистрация VIP-чата в админке владельца платформы
from core.admin_site import owner_admin_site

class VIPInvitationForm(forms.Form):
    """Форма для отправки приглашений в VIP-чат"""
    users = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label="Выберите пользователей для приглашения",
        help_text="Выберите пользователей, которых хотите пригласить в VIP-чат"
    )

    def __init__(self, *args, **kwargs):
        vip_chat = kwargs.pop('vip_chat', None)
        super().__init__(*args, **kwargs)

        if vip_chat:
            # Показываем только пользователей, которые еще не в VIP-чате
            from users.models import User
            existing_members = vip_chat.members.all()
            self.fields['users'].queryset = User.objects.exclude(
                id__in=existing_members.values_list('id', flat=True)
            ).filter(is_active=True).order_by('username')

class OwnerVIPChatRoomAdmin(VIPChatRoomAdmin):
    """Админка VIP-чата для владельца платформы с системой приглашений"""

    change_list_template = 'admin/chat/vipchatroom/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:vip_chat_id>/invite-users/',
                self.admin_site.admin_view(self.invite_users_view),
                name='chat_vipchatroom_invite_users',
            ),
            path(
                '<int:vip_chat_id>/manage-members/',
                self.admin_site.admin_view(self.manage_members_view),
                name='chat_vipchatroom_manage_members',
            ),
        ]
        return custom_urls + urls

    def invite_users_view(self, request, vip_chat_id):
        """Представление для приглашения пользователей в VIP-чат"""
        try:
            vip_chat = VIPChatRoom.objects.get(id=vip_chat_id)
        except VIPChatRoom.DoesNotExist:
            messages.error(request, "VIP-чат не найден")
            return redirect('admin:chat_vipchatroom_changelist')

        if request.method == 'POST':
            form = VIPInvitationForm(request.POST, vip_chat=vip_chat)
            if form.is_valid():
                invited_count = 0
                for user in form.cleaned_data['users']:
                    try:
                        vip_chat.add_member(user, invited_by=request.user)
                        invited_count += 1
                    except Exception as e:
                        messages.warning(request, f"Не удалось пригласить {user.username}: {str(e)}")

                if invited_count > 0:
                    messages.success(
                        request,
                        f"Успешно приглашено {invited_count} пользователей в VIP-чат"
                    )

                return redirect('admin:chat_vipchatroom_changelist')
        else:
            form = VIPInvitationForm(vip_chat=vip_chat)

        context = {
            'title': f'Пригласить пользователей в "{vip_chat.name}"',
            'form': form,
            'vip_chat': vip_chat,
            'opts': self.model._meta,
            'has_view_permission': True,
        }

        return TemplateResponse(
            request,
            'admin/chat/vipchatroom/invite_users.html',
            context
        )

    def manage_members_view(self, request, vip_chat_id):
        """Представление для управления участниками VIP-чата"""
        try:
            vip_chat = VIPChatRoom.objects.get(id=vip_chat_id)
        except VIPChatRoom.DoesNotExist:
            messages.error(request, "VIP-чат не найден")
            return redirect('admin:chat_vipchatroom_changelist')

        if request.method == 'POST':
            action = request.POST.get('action')
            user_id = request.POST.get('user_id')

            if action == 'remove' and user_id:
                try:
                    from users.models import User
                    user = User.objects.get(id=user_id)
                    vip_chat.remove_member(user)
                    messages.success(request, f"Пользователь {user.username} исключен из VIP-чата")
                except Exception as e:
                    messages.error(request, f"Ошибка при исключении пользователя: {str(e)}")

            return redirect('admin:chat_vipchatroom_manage_members', vip_chat_id=vip_chat_id)

        members = vip_chat.vipchatmembership_set.select_related('user', 'invited_by').order_by('-invited_at')

        context = {
            'title': f'Управление участниками "{vip_chat.name}"',
            'vip_chat': vip_chat,
            'members': members,
            'opts': self.model._meta,
            'has_view_permission': True,
        }

        return TemplateResponse(
            request,
            'admin/chat/vipchatroom/manage_members.html',
            context
        )

    def changelist_view(self, request, extra_context=None):
        """Добавляем дополнительный контекст для списка VIP-чатов"""
        extra_context = extra_context or {}

        # Статистика по VIP-чатам
        vip_chats = VIPChatRoom.objects.all()
        stats = {
            'total_vip_chats': vip_chats.count(),
            'active_vip_chats': vip_chats.filter(is_active=True).count(),
            'total_members': VIPChatMembership.objects.filter(is_active=True).count(),
        }
        extra_context['vip_stats'] = stats

        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        """Владелец платформы видит все VIP-чаты"""
        return super(admin.ModelAdmin, self).get_queryset(request)

class OwnerVIPChatMembershipAdmin(VIPChatMembershipAdmin):
    """Админка участников VIP-чата для владельца платформы"""

    list_display = ('vip_chat', 'user', 'invited_by', 'is_active', 'invited_at', 'accepted_at', 'user_role')
    list_filter = ('is_active', 'invited_at', 'accepted_at', 'vip_chat', 'user__role')

    @admin.display(description='Роль пользователя')
    def user_role(self, obj):
        return obj.user.get_role_display() if obj.user else '-'

    def get_queryset(self, request):
        """Владелец платформы видит всех участников VIP-чатов"""
        return super(admin.ModelAdmin, self).get_queryset(request)

# Регистрируем VIP-чат в админке владельца платформы
owner_admin_site.register(VIPChatRoom, OwnerVIPChatRoomAdmin)
owner_admin_site.register(VIPChatMembership, OwnerVIPChatMembershipAdmin)
