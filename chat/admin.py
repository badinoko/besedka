from django.contrib import admin
from .models import Room, Message

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'author', 'content_preview', 'created_at')
    list_filter = ('room', 'author')
    search_fields = ('content', 'author__username')
    raw_id_fields = ('room', 'author', 'parent')

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = 'Content Preview'
