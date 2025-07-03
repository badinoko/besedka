from django.contrib import admin
from .models import Room, Message, MessageReaction, UserChatPosition

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'room', 'content_snippet', 'is_deleted', 'is_edited', 'is_forwarded', 'is_pinned', 'likes_count', 'dislikes_count', 'created_at')
    list_filter = ('room', 'is_deleted', 'is_edited', 'is_forwarded', 'is_pinned', 'created_at')
    search_fields = ('content', 'author__username', 'author__name')
    readonly_fields = ('id', 'created_at', 'likes_count', 'dislikes_count')
    raw_id_fields = ('author', 'parent', 'edited_by', 'pinned_by')

    def content_snippet(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_snippet.short_description = 'Содержимое'

    def has_change_permission(self, request, obj=None):
        """Запрещаем изменение сообщений через админку для защиты истории"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление сообщений через админку - только мягкое удаление"""
        return False

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_snippet', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'user__name', 'message__content')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('message', 'user')

    def message_snippet(self, obj):
        return obj.message.content[:50] + '...' if len(obj.message.content) > 50 else obj.message.content
    message_snippet.short_description = 'Сообщение'

    def has_change_permission(self, request, obj=None):
        """Запрещаем изменение реакций через админку для защиты системы кармы"""
        return False

@admin.register(UserChatPosition)
class UserChatPositionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'room', 'unread_count', 'last_read_at',
        'last_message_snippet', 'updated_at'
    )
    list_filter = ('room', 'last_read_at', 'updated_at')
    search_fields = ('user__username', 'user__name', 'room__name')
    readonly_fields = ('id', 'updated_at', 'calculated_unread_count')
    raw_id_fields = ('user',)

    # Группировка полей для удобства
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'room')
        }),
        ('Позиция чтения', {
            'fields': ('last_read_at', 'last_message_id')
        }),
        ('Статистика', {
            'fields': ('unread_count', 'calculated_unread_count', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_display(self, obj):
        """Отображение пользователя с значком роли"""
        return f"{obj.user.get_role_icon} {obj.user.display_name}"
    user_display.short_description = 'Пользователь'
    user_display.admin_order_field = 'user__username'

    def last_message_snippet(self, obj):
        """Показывает фрагмент последнего прочитанного сообщения"""
        if not obj.last_message_id:
            return "—"
        try:
            message = Message.objects.get(id=obj.last_message_id)
            snippet = message.content[:30] + '...' if len(message.content) > 30 else message.content
            return f'"{snippet}"'
        except Message.DoesNotExist:
            return "Сообщение удалено"
    last_message_snippet.short_description = 'Последнее прочитанное'

    def calculated_unread_count(self, obj):
        """Показывает актуальное количество непрочитанных (для сравнения с кешем)"""
        return obj.get_unread_messages_count()
    calculated_unread_count.short_description = 'Актуальное количество непрочитанных'

    # Действия для массового обновления
    actions = ['refresh_unread_counters', 'mark_all_as_read']

    def refresh_unread_counters(self, request, queryset):
        """Обновляет кешированные счетчики непрочитанных сообщений"""
        updated_count = 0
        for position in queryset:
            old_count = position.unread_count
            position.unread_count = position.get_unread_messages_count()
            position.save()
            updated_count += 1

        self.message_user(
            request,
            f"Обновлено {updated_count} счетчиков непрочитанных сообщений."
        )
    refresh_unread_counters.short_description = "Обновить счетчики непрочитанных"

    def mark_all_as_read(self, request, queryset):
        """Отмечает все сообщения как прочитанные для выбранных позиций"""
        updated_count = 0
        for position in queryset:
            position.mark_as_read()
            updated_count += 1

        self.message_user(
            request,
            f"Отмечено как прочитанное для {updated_count} позиций."
        )
    mark_all_as_read.short_description = "Отметить как прочитанное"
