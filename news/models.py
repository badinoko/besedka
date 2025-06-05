from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinLengthValidator
from django.db.models import Count, Q
import uuid
from PIL import Image
import os

User = get_user_model()


class Category(models.Model):
    """Категории новостей"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL-слаг")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('news:category_posts', kwargs={'slug': self.slug})


class Tag(models.Model):
    """Теги для новостей"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="URL-слаг")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('news:tag_posts', kwargs={'slug': self.slug})


class PublishedPostManager(models.Manager):
    """Менеджер для опубликованных постов"""
    def get_queryset(self):
        return super().get_queryset().filter(
            status='published',
            published_at__lte=timezone.now()
        )

    def pinned(self):
        """Закрепленные посты"""
        return self.get_queryset().filter(is_pinned=True)

    def regular(self):
        """Обычные посты (не закрепленные)"""
        return self.get_queryset().filter(is_pinned=False)


class Post(models.Model):
    """Новостные посты"""
    POST_TYPES = [
        ('article', 'Статья'),
        ('video_link', 'Видео-ссылка'),
        ('poll', 'Опрос'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-слаг")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")

    content = models.TextField(verbose_name="Содержание")
    excerpt = models.TextField(max_length=300, blank=True, verbose_name="Краткое описание")
    image = models.ImageField(upload_to='news/images/', blank=True, null=True, verbose_name="Изображение")

    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='article', verbose_name="Тип поста")
    video_url = models.URLField(blank=True, verbose_name="Ссылка на видео")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    is_pinned = models.BooleanField(default=False, verbose_name="Закреплен")

    published_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата публикации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    views_count = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")

    # Менеджеры
    objects = models.Manager()
    published = PublishedPostManager()

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ['-is_pinned', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['is_pinned', 'published_at']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Автоматически устанавливаем дату публикации при смене статуса на published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Генерируем excerpt если не указан
        if not self.excerpt and self.content:
            self.excerpt = self.content[:297] + '...' if len(self.content) > 300 else self.content

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('news:post_detail', kwargs={'slug': self.slug})

    @property
    def is_published(self):
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()

    def get_comments_count(self):
        return self.comments.count()

    def get_reactions_count(self):
        return self.reactions.count()

    def get_likes_count(self):
        return self.reactions.filter(reaction_type='like').count()

    def get_dislikes_count(self):
        return self.reactions.filter(reaction_type='dislike').count()


class Poll(models.Model):
    """Опросы для постов типа 'poll'"""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='poll', verbose_name="Пост")
    question_text = models.CharField(max_length=300, verbose_name="Вопрос")
    multiple_choice = models.BooleanField(default=False, verbose_name="Множественный выбор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Опрос"
        verbose_name_plural = "Опросы"

    def __str__(self):
        return f"Опрос: {self.question_text}"

    def get_total_votes(self):
        return sum(choice.votes for choice in self.choices.all())

    @property
    def total_votes(self):
        """Свойство для удобного доступа к общему количеству голосов"""
        return self.get_total_votes()

    def get_results(self):
        """Возвращает результаты опроса с процентами"""
        total_votes = self.get_total_votes()
        results = []
        for choice in self.choices.all():
            percentage = (choice.votes / total_votes * 100) if total_votes > 0 else 0
            results.append({
                'choice_id': choice.id,
                'choice': choice,
                'votes': choice.votes,
                'percentage': round(percentage, 1)
            })
        return results


class PollChoice(models.Model):
    """Варианты ответов в опросе"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choices', verbose_name="Опрос")
    choice_text = models.CharField(max_length=200, verbose_name="Текст варианта")
    votes = models.PositiveIntegerField(default=0, verbose_name="Количество голосов")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"
        ordering = ['id']

    def __str__(self):
        return f"{self.choice_text} ({self.votes} голосов)"


class PollVote(models.Model):
    """Голоса пользователей в опросах"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes', verbose_name="Опрос")
    choice = models.ForeignKey(PollChoice, on_delete=models.CASCADE, verbose_name="Выбранный вариант")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    voted_at = models.DateTimeField(auto_now_add=True, verbose_name="Время голосования")

    class Meta:
        verbose_name = "Голос в опросе"
        verbose_name_plural = "Голоса в опросах"
        unique_together = ['poll', 'user', 'choice']  # Пользователь может голосовать за каждый вариант только один раз

    def __str__(self):
        return f"{self.user.username} -> {self.choice.choice_text}"


class PostView(models.Model):
    """Просмотры постов для уникализации"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_views', verbose_name="Пост")
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Пользователь")
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    session_key = models.CharField(max_length=40, blank=True, verbose_name="Ключ сессии")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="Время просмотра")

    class Meta:
        verbose_name = "Просмотр поста"
        verbose_name_plural = "Просмотры постов"
        indexes = [
            models.Index(fields=['post', 'user']),
            models.Index(fields=['post', 'ip_address', 'session_key']),
        ]

    def __str__(self):
        user_info = self.user.username if self.user else f"Гость ({self.ip_address})"
        return f"{user_info} просмотрел {self.post.title}"


class Comment(models.Model):
    """Комментарии к постам"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="Пост")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    content = models.TextField(validators=[MinLengthValidator(3)], verbose_name="Содержание")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True,
                              related_name='replies', verbose_name="Родительский комментарий")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    is_edited = models.BooleanField(default=False, verbose_name="Отредактирован")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"Комментарий от {self.author.username} к {self.post.title}"

    def save(self, *args, **kwargs):
        # Отмечаем как отредактированный если изменяется содержание
        if self.pk:
            original = Comment.objects.get(pk=self.pk)
            if original.content != self.content:
                self.is_edited = True
        super().save(*args, **kwargs)

    def get_replies(self):
        return self.replies.all()

    def get_replies_count(self):
        return self.replies.count()


class Reaction(models.Model):
    """Реакции к постам и комментариям"""
    REACTION_TYPES = [
        ('like', '👍'),
        ('dislike', '👎'),
        ('love', '❤️'),
        ('laugh', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('angry', '😠'),
    ]

    # Полиморфные связи - может быть привязана к посту или комментарию
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True,
                            related_name='reactions', verbose_name="Пост")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True,
                               related_name='reactions', verbose_name="Комментарий")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, verbose_name="Тип реакции")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Реакция"
        verbose_name_plural = "Реакции"
        constraints = [
            # Пользователь может поставить только одну реакцию на пост
            models.UniqueConstraint(
                fields=['post', 'user'],
                condition=Q(post__isnull=False),
                name='unique_post_reaction_per_user'
            ),
            # Пользователь может поставить только одну реакцию на комментарий
            models.UniqueConstraint(
                fields=['comment', 'user'],
                condition=Q(comment__isnull=False),
                name='unique_comment_reaction_per_user'
            ),
        ]
        indexes = [
            models.Index(fields=['post', 'reaction_type']),
            models.Index(fields=['comment', 'reaction_type']),
        ]

    def __str__(self):
        target = self.post.title if self.post else f"комментарий #{self.comment.id}"
        return f"{self.user.username} {self.get_reaction_type_display()} {target}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Проверяем, что реакция привязана либо к посту, либо к комментарию, но не к обоим
        if not self.post and not self.comment:
            raise ValidationError("Реакция должна быть привязана к посту или комментарию")
        if self.post and self.comment:
            raise ValidationError("Реакция не может быть привязана одновременно к посту и комментарию")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class NewsCategory(models.Model):
    """Категории новостей"""
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL слаг")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Категория новостей"
        verbose_name_plural = "Категории новостей"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class NewsSource(models.Model):
    """Источники новостей для парсинга"""
    name = models.CharField(max_length=200, verbose_name="Название источника")
    url = models.URLField(verbose_name="URL источника")
    parsing_enabled = models.BooleanField(default=True, verbose_name="Включен для парсинга")
    last_parsed = models.DateTimeField(null=True, blank=True, verbose_name="Последний парсинг")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Источник новостей"
        verbose_name_plural = "Источники новостей"
        ordering = ['name']

    def __str__(self):
        return self.name


class ParsedNews(models.Model):
    """Новости, полученные парсингом (ожидают модерации)"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает модерации'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
        ('published', 'Опубликовано'),
    ]

    title = models.CharField(max_length=500, verbose_name="Заголовок")
    original_title = models.CharField(max_length=500, verbose_name="Оригинальный заголовок")
    content = models.TextField(verbose_name="Содержание")
    original_content = models.TextField(verbose_name="Оригинальное содержание")
    summary = models.TextField(max_length=1000, blank=True, verbose_name="Краткое описание")

    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, verbose_name="Источник")
    original_url = models.URLField(verbose_name="Оригинальная ссылка")
    image_url = models.URLField(blank=True, null=True, verbose_name="URL изображения")

    parsed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата парсинга")
    original_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата оригинальной публикации")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    moderated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Модератор")
    moderated_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата модерации")
    moderation_notes = models.TextField(blank=True, verbose_name="Заметки модератора")

    # Поля для редактирования модератором
    edited_title = models.CharField(max_length=500, blank=True, verbose_name="Отредактированный заголовок")
    edited_content = models.TextField(blank=True, verbose_name="Отредактированное содержание")
    edited_summary = models.TextField(max_length=1000, blank=True, verbose_name="Отредактированное описание")

    category = models.ForeignKey(NewsCategory, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Категория")

    class Meta:
        verbose_name = "Спарсенная новость"
        verbose_name_plural = "Спарсенные новости"
        ordering = ['-parsed_at']

    def __str__(self):
        return f"{self.title[:50]}... ({self.get_status_display()})"

    def get_display_title(self):
        """Возвращает отредактированный заголовок или оригинальный"""
        return self.edited_title or self.title

    def get_display_content(self):
        """Возвращает отредактированное содержание или оригинальное"""
        return self.edited_content or self.content

    def get_display_summary(self):
        """Возвращает отредактированное описание или автоматически созданное"""
        if self.edited_summary:
            return self.edited_summary
        elif self.summary:
            return self.summary
        else:
            # Автоматически создаем краткое описание из первых 200 символов контента
            content = self.get_display_content()
            return content[:200] + "..." if len(content) > 200 else content


def news_image_upload_path(instance, filename):
    """Путь для загрузки изображений новостей"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"news/{instance.id}/{filename}"


class News(models.Model):
    """Опубликованные новости"""
    title = models.CharField(max_length=500, verbose_name="Заголовок")
    slug = models.SlugField(max_length=500, unique=True, verbose_name="URL слаг")
    summary = models.TextField(max_length=1000, verbose_name="Краткое описание")
    content = models.TextField(verbose_name="Содержание")

    category = models.ForeignKey(NewsCategory, on_delete=models.CASCADE, verbose_name="Категория")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")

    image = models.ImageField(upload_to=news_image_upload_path, blank=True, null=True, verbose_name="Изображение")
    image_alt = models.CharField(max_length=200, blank=True, verbose_name="Alt текст изображения")

    # SEO поля
    meta_description = models.CharField(max_length=160, blank=True, verbose_name="META описание")
    meta_keywords = models.CharField(max_length=200, blank=True, verbose_name="META ключевые слова")

    # Связь с оригинальной спарсенной новостью
    parsed_news = models.OneToOneField(ParsedNews, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Спарсенная новость")
    original_url = models.URLField(blank=True, null=True, verbose_name="Оригинальная ссылка")

    # Статистика
    views_count = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    published_at = models.DateTimeField(default=timezone.now, verbose_name="Дата публикации")

    # Управление публикацией
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемая")

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Автоматически создаем META описание из summary
        if not self.meta_description and self.summary:
            self.meta_description = self.summary[:160]

        super().save(*args, **kwargs)

        # Оптимизируем изображение
        if self.image:
            self.optimize_image()

    def optimize_image(self):
        """Оптимизирует размер изображения"""
        try:
            with Image.open(self.image.path) as img:
                # Конвертируем в RGB если необходимо
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Изменяем размер если изображение слишком большое
                max_size = (800, 600)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(self.image.path, optimize=True, quality=85)
        except Exception as e:
            print(f"Ошибка при оптимизации изображения: {e}")

    def get_absolute_url(self):
        return reverse('news:detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class ParsingLog(models.Model):
    """Логи парсинга новостей"""
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Начало парсинга")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Окончание парсинга")
    status = models.CharField(max_length=20, choices=[
        ('running', 'Выполняется'),
        ('completed', 'Завершен'),
        ('failed', 'Ошибка'),
    ], default='running', verbose_name="Статус")

    total_sources = models.PositiveIntegerField(default=0, verbose_name="Всего источников")
    successful_sources = models.PositiveIntegerField(default=0, verbose_name="Успешных источников")
    total_articles = models.PositiveIntegerField(default=0, verbose_name="Всего статей")
    new_articles = models.PositiveIntegerField(default=0, verbose_name="Новых статей")

    errors = models.TextField(blank=True, verbose_name="Ошибки")
    notes = models.TextField(blank=True, verbose_name="Заметки")

    class Meta:
        verbose_name = "Лог парсинга"
        verbose_name_plural = "Логи парсинга"
        ordering = ['-started_at']

    def __str__(self):
        duration = ""
        if self.finished_at:
            delta = self.finished_at - self.started_at
            duration = f" ({delta.total_seconds():.1f}с)"
        return f"Парсинг {self.started_at.strftime('%d.%m.%Y %H:%M')}{duration} - {self.get_status_display()}"
