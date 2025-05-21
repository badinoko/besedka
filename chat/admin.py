from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'text_preview', 'is_system', 'created_at')
    search_fields = ('author__username', 'text')
    list_filter = ('is_system', 'created_at')
    autocomplete_fields = ('author',)
    readonly_fields = ('created_at',)
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = "Сообщение"
