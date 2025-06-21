from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Photo, PhotoComment
from core.admin_mixins import ModeratorAdminMixin


class PhotoCommentInline(admin.TabularInline):
    model = PhotoComment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['author', 'text', 'created_at']


class PhotoAdmin(ModeratorAdminMixin, admin.ModelAdmin):
    """Админка для фото с поддержкой кнопки ОТМЕНА"""
    list_display = ['title', 'author', 'image_preview', 'growlog', 'is_public', 'created_at']
    list_filter = ['is_public', 'growlog', 'created_at']
    search_fields = ['title', 'description', 'author__username']
    readonly_fields = ['created_at', 'image_preview']
    inlines = [PhotoCommentInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'author', 'image', 'image_preview')
        }),
        ('Связанное', {
            'fields': ('growlog', 'growlog_entry', 'description')
        }),
        ('Модерация', {
            'fields': ('is_public',)
        })
    )

    def image_preview(self, obj):
        """Превью изображения в админке"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = 'Превью'


class PhotoCommentAdmin(ModeratorAdminMixin, admin.ModelAdmin):
    """Админка для комментариев к фото с поддержкой кнопки ОТМЕНА"""
    list_display = ['photo', 'author', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['text', 'author__username', 'photo__title']
    readonly_fields = ['created_at']

    def content_preview(self, obj):
        """Короткая версия комментария"""
        if len(obj.text) > 50:
            return obj.text[:50] + '...'
        return obj.text
    content_preview.short_description = 'Комментарий'

# НЕ регистрируем в стандартной админке Django - только в кастомных!
# admin.site.register(Photo, PhotoAdmin)
# admin.site.register(PhotoComment, PhotoCommentAdmin)

# Регистрируем в админке модератора для модерации
from core.admin_site import moderator_admin_site
moderator_admin_site.register(Photo, PhotoAdmin)
moderator_admin_site.register(PhotoComment, PhotoCommentAdmin)
