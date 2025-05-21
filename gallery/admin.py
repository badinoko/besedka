from django.contrib import admin
from .models import Photo, PhotoComment

class PhotoCommentInline(admin.TabularInline):
    model = PhotoComment
    extra = 1

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'growlog', 'is_public', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    list_filter = ('is_public', 'created_at')
    autocomplete_fields = ('author', 'growlog', 'growlog_entry')
    inlines = [PhotoCommentInline]
    readonly_fields = ('likes_count',)
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = "Количество лайков"

@admin.register(PhotoComment)
class PhotoCommentAdmin(admin.ModelAdmin):
    list_display = ('photo', 'author', 'created_at')
    search_fields = ('photo__title', 'author__username', 'text')
    list_filter = ('created_at',)
    autocomplete_fields = ('photo', 'author')
