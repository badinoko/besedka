from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from .models import Category, Tag, Post, Poll, PollChoice, PollVote, PostView, Comment, Reaction, NewsCategory, NewsSource, ParsedNews, News, ParsingLog
import json


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'posts_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def posts_count(self, obj):
        count = obj.post_set.count()
        if count > 0:
            url = reverse('admin:news_post_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} постов</a>', url, count)
        return '0 постов'
    posts_count.short_description = 'Количество постов'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'posts_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    def posts_count(self, obj):
        count = obj.post_set.count()
        if count > 0:
            url = reverse('admin:news_post_changelist') + f'?tags__id__exact={obj.id}'
            return format_html('<a href="{}">{} постов</a>', url, count)
        return '0 постов'
    posts_count.short_description = 'Количество постов'


class PollChoiceInline(admin.TabularInline):
    model = PollChoice
    extra = 2
    fields = ['choice_text', 'votes']
    readonly_fields = ['votes']


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'post', 'multiple_choice', 'total_votes', 'created_at']
    list_filter = ['multiple_choice', 'created_at']
    search_fields = ['question_text', 'post__title']
    readonly_fields = ['created_at', 'total_votes']
    inlines = [PollChoiceInline]

    def total_votes(self, obj):
        return obj.get_total_votes()
    total_votes.short_description = 'Всего голосов'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'post_type', 'status', 'is_pinned',
                   'views_count', 'comments_count', 'reactions_count', 'published_at']
    list_filter = ['status', 'post_type', 'is_pinned', 'category', 'created_at', 'published_at']
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['views_count', 'created_at', 'updated_at', 'comments_count', 'reactions_count']

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'author', 'category', 'tags')
        }),
        ('Содержание', {
            'fields': ('post_type', 'content', 'excerpt', 'image', 'video_url')
        }),
        ('Публикация', {
            'fields': ('status', 'is_pinned', 'published_at')
        }),
        ('Статистика', {
            'fields': ('views_count', 'comments_count', 'reactions_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def comments_count(self, obj):
        count = obj.get_comments_count()
        if count > 0:
            url = reverse('admin:news_comment_changelist') + f'?post__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    comments_count.short_description = 'Комментарии'

    def reactions_count(self, obj):
        count = obj.get_reactions_count()
        if count > 0:
            url = reverse('admin:news_reaction_changelist') + f'?post__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    reactions_count.short_description = 'Реакции'

    def save_model(self, request, obj, form, change):
        if not change:  # Если создается новый пост
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['short_content', 'author', 'post', 'parent', 'is_edited', 'created_at']
    list_filter = ['is_edited', 'created_at', 'post__category']
    search_fields = ['content', 'author__username', 'post__title']
    readonly_fields = ['created_at', 'updated_at', 'is_edited', 'replies_count']
    raw_id_fields = ['post', 'parent']

    fieldsets = (
        ('Основная информация', {
            'fields': ('post', 'author', 'parent', 'content')
        }),
        ('Метаданные', {
            'fields': ('is_edited', 'replies_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Содержание'

    def replies_count(self, obj):
        count = obj.get_replies_count()
        if count > 0:
            url = reverse('admin:news_comment_changelist') + f'?parent__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    replies_count.short_description = 'Ответы'


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'reaction_type', 'target_object', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username', 'post__title', 'comment__content']
    readonly_fields = ['created_at']
    raw_id_fields = ['post', 'comment']

    def target_object(self, obj):
        if obj.post:
            return format_html('Пост: <a href="{}">{}</a>',
                             reverse('admin:news_post_change', args=[obj.post.id]),
                             obj.post.title)
        elif obj.comment:
            return format_html('Комментарий: <a href="{}">{}</a>',
                             reverse('admin:news_comment_change', args=[obj.comment.id]),
                             obj.comment.short_content if hasattr(obj.comment, 'short_content') else str(obj.comment))
        return 'Не определено'
    target_object.short_description = 'Объект реакции'


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ['post', 'user_info', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at', 'post__category']
    search_fields = ['post__title', 'user__username', 'ip_address']
    readonly_fields = ['viewed_at']
    raw_id_fields = ['post', 'user']

    def user_info(self, obj):
        if obj.user:
            return format_html('<a href="{}">{}</a>',
                             reverse('admin:users_user_change', args=[obj.user.id]),
                             obj.user.username)
        return f'Гость (сессия: {obj.session_key[:8]}...)'
    user_info.short_description = 'Пользователь'


@admin.register(PollChoice)
class PollChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'poll', 'votes', 'created_at']
    list_filter = ['created_at', 'poll__post__category']
    search_fields = ['choice_text', 'poll__question_text', 'poll__post__title']
    readonly_fields = ['votes', 'created_at']
    raw_id_fields = ['poll']


@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'poll', 'choice', 'voted_at']
    list_filter = ['voted_at', 'poll__post__category']
    search_fields = ['user__username', 'poll__question_text', 'choice__choice_text']
    readonly_fields = ['voted_at']
    raw_id_fields = ['poll', 'choice', 'user']


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'parsing_enabled', 'last_parsed', 'created_at']
    list_filter = ['parsing_enabled', 'created_at']
    search_fields = ['name', 'url']
    list_editable = ['parsing_enabled']

    actions = ['enable_parsing', 'disable_parsing']

    def enable_parsing(self, request, queryset):
        updated = queryset.update(parsing_enabled=True)
        self.message_user(request, f'Парсинг включен для {updated} источников.')
    enable_parsing.short_description = "Включить парсинг для выбранных источников"

    def disable_parsing(self, request, queryset):
        updated = queryset.update(parsing_enabled=False)
        self.message_user(request, f'Парсинг отключен для {updated} источников.')
    disable_parsing.short_description = "Отключить парсинг для выбранных источников"


@admin.register(ParsedNews)
class ParsedNewsAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'source', 'status', 'category', 'parsed_at', 'moderated_by', 'action_buttons']
    list_filter = ['status', 'source', 'category', 'parsed_at']
    search_fields = ['title', 'original_title', 'content']
    list_per_page = 20

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'original_title', 'summary', 'category')
        }),
        ('Содержание', {
            'fields': ('content', 'original_content'),
            'classes': ('collapse',)
        }),
        ('Редактирование модератором', {
            'fields': ('edited_title', 'edited_content', 'edited_summary'),
            'classes': ('wide',)
        }),
        ('Источник', {
            'fields': ('source', 'original_url', 'image_url'),
            'classes': ('collapse',)
        }),
        ('Модерация', {
            'fields': ('status', 'moderated_by', 'moderated_at', 'moderation_notes'),
            'classes': ('wide',)
        }),
        ('Временные метки', {
            'fields': ('parsed_at', 'original_date'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['parsed_at', 'moderated_at', 'moderated_by']

    actions = ['approve_news', 'reject_news', 'publish_news', 'reset_to_pending']

    def title_short(self, obj):
        return obj.title[:80] + "..." if len(obj.title) > 80 else obj.title
    title_short.short_description = "Заголовок"

    def action_buttons(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}">Редактировать</a> '
                '<a class="button" href="{}">Одобрить</a> '
                '<a class="button" href="{}">Отклонить</a>',
                reverse('admin:news_parsednews_change', args=[obj.pk]),
                reverse('admin:approve_parsed_news', args=[obj.pk]),
                reverse('admin:reject_parsed_news', args=[obj.pk])
            )
        elif obj.status == 'approved':
            return format_html(
                '<a class="button" href="{}">Редактировать</a> '
                '<a class="button" style="background-color: green; color: white;" href="{}">Опубликовать</a>',
                reverse('admin:news_parsednews_change', args=[obj.pk]),
                reverse('admin:publish_parsed_news', args=[obj.pk])
            )
        else:
            return format_html(
                '<a class="button" href="{}">Редактировать</a>',
                reverse('admin:news_parsednews_change', args=[obj.pk])
            )
    action_buttons.short_description = "Действия"
    action_buttons.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:pk>/', self.admin_site.admin_view(self.approve_news_view), name='approve_parsed_news'),
            path('reject/<int:pk>/', self.admin_site.admin_view(self.reject_news_view), name='reject_parsed_news'),
            path('publish/<int:pk>/', self.admin_site.admin_view(self.publish_news_view), name='publish_parsed_news'),
            path('run-parser/', self.admin_site.admin_view(self.run_parser_view), name='run_news_parser'),
        ]
        return custom_urls + urls

    def approve_news_view(self, request, pk):
        parsed_news = get_object_or_404(ParsedNews, pk=pk)
        parsed_news.status = 'approved'
        parsed_news.moderated_by = request.user
        parsed_news.moderated_at = timezone.now()
        parsed_news.save()
        messages.success(request, f'Новость "{parsed_news.title}" одобрена.')
        return redirect('admin:news_parsednews_changelist')

    def reject_news_view(self, request, pk):
        parsed_news = get_object_or_404(ParsedNews, pk=pk)
        parsed_news.status = 'rejected'
        parsed_news.moderated_by = request.user
        parsed_news.moderated_at = timezone.now()
        parsed_news.save()
        messages.warning(request, f'Новость "{parsed_news.title}" отклонена.')
        return redirect('admin:news_parsednews_changelist')

    def publish_news_view(self, request, pk):
        parsed_news = get_object_or_404(ParsedNews, pk=pk)

        if parsed_news.status != 'approved':
            messages.error(request, 'Можно публиковать только одобренные новости.')
            return redirect('admin:news_parsednews_changelist')

        # Создаем опубликованную новость
        news = News.objects.create(
            title=parsed_news.get_display_title(),
            summary=parsed_news.get_display_summary(),
            content=parsed_news.get_display_content(),
            category=parsed_news.category,
            author=request.user,
            parsed_news=parsed_news,
            original_url=parsed_news.original_url,
            meta_description=parsed_news.get_display_summary()[:160]
        )

        # Обновляем статус спарсенной новости
        parsed_news.status = 'published'
        parsed_news.save()

        messages.success(request, f'Новость "{news.title}" опубликована.')
        return redirect('admin:news_news_change', news.pk)

    def run_parser_view(self, request):
        """Запуск парсера новостей вручную"""
        if request.method == 'POST':
            try:
                from .services import NewsParsingService
                service = NewsParsingService()
                result = service.run_parsing()

                if result['success']:
                    messages.success(request,
                        f'Парсинг завершен успешно. Обработано {result["total_articles"]} статей, '
                        f'добавлено {result["new_articles"]} новых.')
                else:
                    messages.error(request, f'Ошибка парсинга: {result["error"]}')
            except Exception as e:
                messages.error(request, f'Ошибка запуска парсера: {str(e)}')

            return redirect('admin:news_parsednews_changelist')

        return render(request, 'admin/news/run_parser.html')

    def approve_news(self, request, queryset):
        updated = 0
        for parsed_news in queryset.filter(status='pending'):
            parsed_news.status = 'approved'
            parsed_news.moderated_by = request.user
            parsed_news.moderated_at = timezone.now()
            parsed_news.save()
            updated += 1
        self.message_user(request, f'Одобрено {updated} новостей.')
    approve_news.short_description = "Одобрить выбранные новости"

    def reject_news(self, request, queryset):
        updated = 0
        for parsed_news in queryset.filter(status='pending'):
            parsed_news.status = 'rejected'
            parsed_news.moderated_by = request.user
            parsed_news.moderated_at = timezone.now()
            parsed_news.save()
            updated += 1
        self.message_user(request, f'Отклонено {updated} новостей.')
    reject_news.short_description = "Отклонить выбранные новости"

    def publish_news(self, request, queryset):
        published = 0
        for parsed_news in queryset.filter(status='approved'):
            try:
                news = News.objects.create(
                    title=parsed_news.get_display_title(),
                    summary=parsed_news.get_display_summary(),
                    content=parsed_news.get_display_content(),
                    category=parsed_news.category,
                    author=request.user,
                    parsed_news=parsed_news,
                    original_url=parsed_news.original_url,
                    meta_description=parsed_news.get_display_summary()[:160]
                )
                parsed_news.status = 'published'
                parsed_news.save()
                published += 1
            except Exception as e:
                continue
        self.message_user(request, f'Опубликовано {published} новостей.')
    publish_news.short_description = "Опубликовать выбранные одобренные новости"

    def reset_to_pending(self, request, queryset):
        updated = queryset.exclude(status='published').update(
            status='pending',
            moderated_by=None,
            moderated_at=None
        )
        self.message_user(request, f'Сброшено в ожидание {updated} новостей.')
    reset_to_pending.short_description = "Сбросить в ожидание модерации"


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'category', 'author', 'is_published', 'is_featured', 'views_count', 'published_at']
    list_filter = ['is_published', 'is_featured', 'category', 'published_at']
    search_fields = ['title', 'content', 'summary']
    list_editable = ['is_published', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'summary', 'category', 'author')
        }),
        ('Содержание', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('Изображение', {
            'fields': ('image', 'image_alt'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Связи', {
            'fields': ('parsed_news', 'original_url'),
            'classes': ('collapse',)
        }),
        ('Публикация', {
            'fields': ('is_published', 'is_featured', 'published_at'),
            'classes': ('wide',)
        }),
        ('Статистика', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['views_count', 'created_at', 'updated_at']

    def title_short(self, obj):
        return obj.title[:80] + "..." if len(obj.title) > 80 else obj.title
    title_short.short_description = "Заголовок"


@admin.register(ParsingLog)
class ParsingLogAdmin(admin.ModelAdmin):
    list_display = ['started_at', 'status', 'total_sources', 'successful_sources', 'total_articles', 'new_articles', 'duration']
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'finished_at', 'status', 'total_sources', 'successful_sources', 'total_articles', 'new_articles', 'errors', 'notes']

    def duration(self, obj):
        if obj.finished_at:
            delta = obj.finished_at - obj.started_at
            return f"{delta.total_seconds():.1f}с"
        return "Выполняется..."
    duration.short_description = "Длительность"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
