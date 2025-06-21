from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, TextChoices
from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from PIL import Image
import os

class User(AbstractUser):
    """
    Custom user model with Telegram integration and roles.
    Enhanced for 2025 with modern social features.
    """

    class Role(TextChoices):
        OWNER = "owner", _("Владелец платформы")
        MODERATOR = "moderator", _("Модератор платформы")
        STORE_OWNER = "store_owner", _("Владелец магазина")
        STORE_ADMIN = "store_admin", _("Администратор магазина")
        USER = "user", _("Пользователь")
        GUEST = "guest", _("Гость")

    class ExperienceLevel(TextChoices):
        BEGINNER = "beginner", _("🌱 Новичок")
        INTERMEDIATE = "intermediate", _("🌿 Опытный")
        ADVANCED = "advanced", _("🌳 Эксперт")
        MASTER = "master", _("🏆 Мастер")

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Имя пользователя"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    # Роль пользователя
    role = CharField(
        _("Роль"),
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )

    # Персональный значок (для обычных пользователей)
    role_icon = models.CharField(
        _("Персональный значок"),
        max_length=10,
        blank=True,
        null=True,
        help_text=_("Персональный эмодзи-значок для обычных пользователей")
    )

    # Telegram ID - числовой идентификатор от Telegram
    telegram_id = models.BigIntegerField(
        _("Telegram ID"),
        unique=True,
        null=True, # Может быть null, если пользователь регистрировался не через Telegram
        blank=True,
        help_text=_("Уникальный числовой ID пользователя в Telegram")
    )

    # Telegram Username
    telegram_username = CharField(
        _("Telegram Username"),
        max_length=100,
        blank=True,
        null=True,
        unique=True, # Может быть null, но если указан, то уникален
        help_text=_("Ваш username в Telegram (без @)")
    )

    # === ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ===
    avatar = models.ImageField(
        _("Аватар"),
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text=_("Рекомендуемый размер: 300x300px")
    )

    bio = models.TextField(
        _("О себе"),
        blank=True,
        max_length=500,
        help_text=_("Расскажите о себе (максимум 500 символов)")
    )

    location = models.CharField(
        _("Местоположение"),
        blank=True,
        max_length=100,
        help_text=_("Город, регион или страна")
    )

    experience_level = models.CharField(
        _("Уровень опыта"),
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.BEGINNER,
        help_text=_("Ваш уровень опыта в выращивании")
    )

    website = models.URLField(
        _("Веб-сайт"),
        blank=True,
        help_text=_("Ваш личный сайт или блог")
    )

    # === СОЦИАЛЬНЫЕ ФУНКЦИИ ===
    karma_points = models.IntegerField(
        _("Очки кармы"),
        default=0,
        help_text=_("Очки за активность на платформе")
    )

    followers_count = models.IntegerField(
        _("Количество подписчиков"),
        default=0
    )

    following_count = models.IntegerField(
        _("Количество подписок"),
        default=0
    )

    # === СТАТИСТИКА АКТИВНОСТИ ===
    posts_count = models.IntegerField(
        _("Количество постов"),
        default=0
    )

    photos_count = models.IntegerField(
        _("Количество фотографий"),
        default=0
    )

    likes_given = models.IntegerField(
        _("Поставлено лайков"),
        default=0
    )

    likes_received = models.IntegerField(
        _("Получено лайков"),
        default=0
    )

    comments_count = models.IntegerField(
        _("Количество комментариев"),
        default=0
    )

    # === НАСТРОЙКИ ПРИВАТНОСТИ ===
    is_profile_public = models.BooleanField(
        _("Публичный профиль"),
        default=True,
        help_text=_("Разрешить другим пользователям видеть ваш профиль")
    )

    show_experience_level = models.BooleanField(
        _("Показывать уровень опыта"),
        default=True
    )

    show_karma = models.BooleanField(
        _("Показывать карму"),
        default=True
    )

    show_statistics = models.BooleanField(
        _("Показывать статистику"),
        default=True
    )

    allow_direct_messages = models.BooleanField(
        _("Разрешить личные сообщения"),
        default=True
    )

    # === УВЕДОМЛЕНИЯ ===
    email_notifications = models.BooleanField(
        _("Email уведомления"),
        default=True
    )

    notify_new_followers = models.BooleanField(
        _("Уведомления о новых подписчиках"),
        default=True
    )

    notify_likes = models.BooleanField(
        _("Уведомления о лайках"),
        default=True
    )

    notify_comments = models.BooleanField(
        _("Уведомления о комментариях"),
        default=True
    )

    # === СИСТЕМНЫЕ ПОЛЯ ===
    is_banned = models.BooleanField(
        _("Забанен"), default=False,
        help_text=_("Забаненные пользователи не могут войти в систему")
    )

    last_activity = models.DateTimeField(
        _("Последняя активность"),
        auto_now=True
    )

    account_created = models.DateTimeField(
        _("Дата создания аккаунта"),
        auto_now_add=True
    )

    # EMAIL_FIELD = "email"
    # USERNAME_FIELD = "username"
    # REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")
        app_label = 'users'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Автоматическое изменение размера аватара
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view."""
        return reverse("users:detail", kwargs={"username": self.username})

    def __str__(self):
        display_name = self.name or self.username
        if self.experience_level and self.experience_level != 'beginner':
            level_emoji = {
                'intermediate': '🌿',
                'advanced': '🌳',
                'master': '🏆'
            }.get(self.experience_level, '')
            return f"{level_emoji} {display_name}"
        return display_name

    # === МЕТОДЫ ПРОВЕРКИ РОЛИ ===
    def is_owner(self) -> bool:
        """Проверяет, является ли пользователь владельцем платформы."""
        return self.role == self.Role.OWNER

    def is_platform_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором платформы."""
        return self.role == self.Role.MODERATOR

    def is_store_owner(self) -> bool:
        """Проверяет, является ли пользователь владельцем магазина."""
        return self.role == self.Role.STORE_OWNER

    def is_store_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором магазина."""
        return self.role == self.Role.STORE_ADMIN

    def is_regular_user(self) -> bool:
        """Проверяет, является ли пользователь обычным пользователем."""
        return self.role == self.Role.USER

    def is_guest(self) -> bool:
        """Проверяет, является ли пользователь гостем."""
        return self.role == self.Role.GUEST

    def can_access_vip_chat(self) -> bool:
        """
        Проверяет, имеет ли пользователь доступ к VIP-чату.
        Доступ разрешен для Владельца платформы и Администратора платформы.
        """
        return self.role in [self.Role.OWNER, self.Role.MODERATOR]

    @property
    def has_admin_access(self) -> bool:
        """Проверяет, имеет ли пользователь доступ к какой-либо админке."""
        return self.role in [
            self.Role.OWNER,
            self.Role.MODERATOR,
            self.Role.STORE_OWNER,
            self.Role.STORE_ADMIN,
        ]

    # === МЕТОДЫ ДЛЯ СОЦИАЛЬНЫХ ФУНКЦИЙ ===
    @property
    def avatar_url(self):
        """Возвращает URL аватара или дефолтный."""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default-avatar.png'

    @property
    def experience_badge(self):
        """Возвращает эмодзи для уровня опыта."""
        return {
            'beginner': '🌱',
            'intermediate': '🌿',
            'advanced': '🌳',
            'master': '🏆'
        }.get(self.experience_level, '🌱')

    @property
    def karma_level(self):
        """Возвращает уровень кармы."""
        if self.karma_points >= 1000:
            return "🏆 Легенда"
        elif self.karma_points >= 500:
            return "⭐ Звезда"
        elif self.karma_points >= 100:
            return "🌟 Популярный"
        elif self.karma_points >= 50:
            return "👍 Активный"
        else:
            return "🌱 Новичок"

    def add_karma(self, points, reason=""):
        """Добавляет очки кармы."""
        self.karma_points += points
        self.save(update_fields=['karma_points'])

    def can_view_profile(self, viewer_user):
        """Проверяет, может ли пользователь просматривать профиль."""
        if not self.is_profile_public:
            return viewer_user == self or viewer_user.has_admin_access
        return True

    @property
    def display_name(self):
        """Возвращает отображаемое имя."""
        if self.name:
            return self.name
        elif self.username and self.username != f"user_{self.id}":
            return self.username
        else:
            return f"User{self.id}"

    @property
    def get_role_icon(self):
        """Возвращает значок роли или персональный значок."""
        # Системные значки ролей (приоритет)
        role_icons = {
            'owner': '👑',
            'moderator': '🛡️',
            'store_owner': '🏪',
            'store_admin': '📦',
            'user': '👤'
        }

        # Если есть персональный значок и роль = user
        if self.role == 'user' and self.role_icon:
            return self.role_icon

        return role_icons.get(self.role, '👤')

    @property
    def display_name_with_icon(self):
        """Возвращает отображаемое имя со значком роли."""
        return f"{self.get_role_icon} {self.display_name}"

    @property
    def short_bio(self):
        """Возвращает сокращенную биографию."""
        if len(self.bio) > 100:
            return self.bio[:100] + "..."
        return self.bio

    @property
    def unread_notifications_count(self):
        """Возвращает количество непрочитанных уведомлений."""
        return self.notifications.filter(is_read=False).count()

    @property
    def recent_notifications(self):
        """Возвращает последние 5 уведомлений."""
        return self.notifications.all()[:5]

    def get_short_name(self):
        """Возвращает короткое имя пользователя."""
        return self.name or self.username

    def get_full_name(self):
        """Возвращает полное имя пользователя."""
        return self.name or self.username

    def get_role_display(self):
        """Возвращает читаемое название роли."""
        role_dict = {
            'owner': 'Владелец платформы',
            'moderator': 'Модератор платформы',
            'store_owner': 'Владелец магазина',
            'store_admin': 'Администратор магазина',
            'user': 'Пользователь',
            'guest': 'Гость'
        }
        return role_dict.get(self.role, self.role)

class BanRecord(models.Model):
    """
    Records of user bans.
    """
    # Типы банов
    BAN_TYPE_GLOBAL = 'global'
    BAN_TYPE_CHAT = 'chat'
    BAN_TYPE_GALLERY = 'gallery'
    BAN_TYPE_GROWLOGS = 'growlogs'

    BAN_TYPE_CHOICES = [
        (BAN_TYPE_GLOBAL, _('Global Ban')),
        (BAN_TYPE_CHAT, _('Chat Ban')),
        (BAN_TYPE_GALLERY, _('Gallery Ban')),
        (BAN_TYPE_GROWLOGS, _('Grow Logs Ban')),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bans'
    )
    banned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bans_given'
    )
    ban_type = models.CharField(
        _("Ban Type"), max_length=20, choices=BAN_TYPE_CHOICES, default=BAN_TYPE_GLOBAL
    )
    reason = models.TextField(_("Reason"), blank=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    expires_at = models.DateTimeField(
        _("Expires at"), null=True, blank=True,
        help_text=_("Leave empty for permanent ban")
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Ban Record")
        verbose_name_plural = _("Ban Records")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.get_ban_type_display()} ban"

    def is_expired(self):
        """Check if the ban has expired."""
        if not self.expires_at:
            return False  # Permanent ban never expires
        return timezone.now() > self.expires_at

    def revoke(self, admin_user=None):
        """Revoke the ban."""
        self.is_active = False
        self.save()

        # If this is a global ban, update the user's banned status
        if self.ban_type == self.BAN_TYPE_GLOBAL:
            # Check if there are other active global bans
            other_global_bans = BanRecord.objects.filter(
                user=self.user,
                ban_type=self.BAN_TYPE_GLOBAL,
                is_active=True
            ).exclude(id=self.id).exists()

            # If no other global bans, set user.is_banned to False
            if not other_global_bans:
                self.user.is_banned = False
                self.user.save()

        return True

class UserFollow(models.Model):
    """
    Модель подписок между пользователями.
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_("Подписчик")
    )

    followed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name=_("На кого подписан")
    )

    created_at = models.DateTimeField(
        _("Дата подписки"),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _("Подписка")
        verbose_name_plural = _("Подписки")
        unique_together = ['follower', 'followed']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower} → {self.followed}"

    def save(self, *args, **kwargs):
        # Нельзя подписаться на самого себя
        if self.follower == self.followed:
            raise ValueError("Нельзя подписаться на самого себя")

        super().save(*args, **kwargs)

        # Обновляем счетчики
        self.follower.following_count = self.follower.following.count()
        self.follower.save(update_fields=['following_count'])

        self.followed.followers_count = self.followed.followers.count()
        self.followed.save(update_fields=['followers_count'])

class Like(models.Model):
    """
    Универсальная модель лайков для всех типов контента.
    """
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes_given_new',
        verbose_name=_("Пользователь")
    )

    # Универсальная связь с любой моделью
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(_("Дата"), auto_now_add=True)

    class Meta:
        verbose_name = _("Лайк")
        verbose_name_plural = _("Лайки")
        unique_together = ['user', 'content_type', 'object_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} → {self.content_object}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Обновляем счетчик лайков у пользователя
        self.user.likes_given += 1
        self.user.save(update_fields=['likes_given'])

class Notification(models.Model):
    """
    Модель уведомлений для пользователей.
    """
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType

    class NotificationType(models.TextChoices):
        LIKE = 'like', _('👍 Лайк')
        COMMENT = 'comment', _('💬 Комментарий')
        FOLLOW = 'follow', _('👥 Подписка')
        MENTION = 'mention', _('📢 Упоминание')
        SYSTEM = 'system', _('⚙️ Системное')
        ORDER = 'order', _('🛍️ Новый заказ')
        CHAT_MESSAGE = 'chat_message', _('💬 Новое сообщение в чате')

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_("Получатель")
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        verbose_name=_("Отправитель"),
        null=True,
        blank=True
    )

    notification_type = models.CharField(
        _("Тип уведомления"),
        max_length=20,
        choices=NotificationType.choices
    )

    title = models.CharField(_("Заголовок"), max_length=255)
    message = models.TextField(_("Сообщение"))

    # Связанный объект (опционально)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    is_read = models.BooleanField(_("Прочитано"), default=False)
    created_at = models.DateTimeField(_("Дата"), auto_now_add=True)

    class Meta:
        verbose_name = _("Уведомление")
        verbose_name_plural = _("Уведомления")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title} для {self.recipient.username}"

    @property
    def type_icon(self):
        icons = {
            'like': '<i class="fas fa-thumbs-up text-primary"></i>',
            'comment': '<i class="fas fa-comment-dots text-info"></i>',
            'follow': '<i class="fas fa-user-plus text-success"></i>',
            'mention': '<i class="fas fa-at text-warning"></i>',
            'system': '<i class="fas fa-cog text-secondary"></i>',
            'order': '<i class="fas fa-receipt text-purple"></i>', # Пример цвета
            'chat_message': '<i class="fas fa-comments text-success"></i>', # Иконка для чата
        }
        return icons.get(self.notification_type, '<i class="fas fa-bell"></i>')

    def get_action_url(self):
        """
        Возвращает URL для действия, связанного с уведомлением.
        Например, переход к заказу, посту, комментарию, профилю пользователя, чату.
        Возвращает None, если действие не предусмотрено.
        """
        # 1. Стандартный способ: пытаемся вызвать get_absolute_url() у content_object
        if self.content_object and hasattr(self.content_object, 'get_absolute_url'):
            try:
                url = self.content_object.get_absolute_url()
                if url: # Убедимся, что URL не пустой
                    return url
            except (NoReverseMatch, Exception):
                pass # Ошибка реверсирования, попробуем другие способы

        # 2. Специальная логика для определенных типов уведомлений

        if self.notification_type == self.NotificationType.ORDER:
            # Для заказов
            if hasattr(self.content_object, 'pk'):
                try:
                    if self.recipient.is_store_owner() or self.recipient.is_store_admin():
                        # URL для админки магазина
                        return reverse('admin:magicbeans_store_order_change', kwargs={'object_id': self.content_object.pk})
                    else:
                        # URL для личного кабинета пользователя
                        return reverse('store:order_detail', kwargs={'order_id': self.content_object.pk})
                except NoReverseMatch:
                    # Если специфичный URL не найден, ведем в магазин
                    try:
                        return reverse('store:catalog')
                    except NoReverseMatch:
                        pass

        elif self.notification_type == self.NotificationType.FOLLOW:
            # Для подписок ведем в личный кабинет
            try:
                return reverse('users:profile')
            except NoReverseMatch:
                return reverse('news:home')  # Fallback

        elif self.notification_type == self.NotificationType.LIKE:
            # Для лайков ведем в галерею (основное место для лайков)
            try:
                return reverse('gallery:gallery')
            except NoReverseMatch:
                return reverse('news:home')  # Fallback

        elif self.notification_type == self.NotificationType.COMMENT:
            # Для комментариев ведем в гроу-репорты (основное место для комментариев)
            try:
                return reverse('growlogs:list')
            except NoReverseMatch:
                return reverse('news:home')  # Fallback

        elif self.notification_type == self.NotificationType.MENTION:
            # Для упоминаний ведем в личный кабинет
            try:
                return reverse('users:profile')
            except NoReverseMatch:
                return reverse('news:home')  # Fallback

        elif self.notification_type == self.NotificationType.CHAT_MESSAGE:
            # Для сообщений в чате ведем на главную (чат доступен через модальное окно)
            try:
                return reverse('news:home')
            except NoReverseMatch:
                pass

        elif self.notification_type == self.NotificationType.SYSTEM:
            # Системные уведомления - в личный кабинет
            try:
                return reverse('users:profile')
            except NoReverseMatch:
                return reverse('news:home')  # Fallback

        # Если ни один из способов не дал URL, возвращаем главную страницу как fallback
        try:
            return reverse('news:home')
        except:
            return '/'  # Последний fallback

    @property
    def is_actionable(self):
        """
        Проверяет, является ли уведомление "кликабельным" (имеет ли оно URL для действия).
        Все уведомления должны иметь возможность навигации к соответствующим разделам.
        """
        action_url = self.get_action_url()
        return action_url is not None and action_url != '#' and action_url != 'None'

    def mark_as_read(self):
        """Помечает уведомление как прочитанное."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    @classmethod
    def create_notification(cls, recipient, notification_type, title, message, sender=None, content_object=None):
        """
        Создает новое уведомление с проверкой прав доступа.

        Валидирует, что пользователь может получать уведомления данного типа
        в зависимости от его роли и доступных функций.
        """
        # Проверяем, может ли пользователь получать уведомления данного типа
        if not cls.can_receive_notification(recipient, notification_type):
            # Логируем попытку создания недопустимого уведомления
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Попытка создать недопустимое уведомление типа '{notification_type}' "
                f"для пользователя '{recipient.username}' (роль: {recipient.role})"
            )
            return None

        return cls.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            content_object=content_object
        )

    @classmethod
    def can_receive_notification(cls, user, notification_type):
        """
        Проверяет, может ли пользователь получать уведомления данного типа
        в зависимости от его роли и доступных функций.
        """
        # Гости могут получать только уведомления о заказах
        if user.role == 'guest':
            return notification_type == cls.NotificationType.ORDER

        # Неаутентифицированные пользователи не получают уведомления
        if not user.is_authenticated:
            return False

        # Проверяем доступность функций по типам уведомлений
        if notification_type == cls.NotificationType.LIKE:
            # Лайки доступны только аутентифицированным пользователям
            # Гости не могут лайкать, значит и уведомления о лайках не нужны
            return user.role in ['user', 'moderator', 'owner', 'store_owner', 'store_admin']

        elif notification_type == cls.NotificationType.COMMENT:
            # Комментарии доступны только аутентифицированным пользователям
            return user.role in ['user', 'moderator', 'owner', 'store_owner', 'store_admin']

        elif notification_type == cls.NotificationType.FOLLOW:
            # Подписки доступны только аутентифицированным пользователям
            return user.role in ['user', 'moderator', 'owner', 'store_owner', 'store_admin']

        elif notification_type == cls.NotificationType.MENTION:
            # Упоминания в чате - только для тех, кто имеет доступ к чату
            return user.role in ['user', 'moderator', 'owner', 'store_owner', 'store_admin']

        elif notification_type == cls.NotificationType.CHAT_MESSAGE:
            # Сообщения в чате - только для тех, кто имеет доступ к чату
            return user.role in ['user', 'moderator', 'owner', 'store_owner', 'store_admin']

        elif notification_type == cls.NotificationType.ORDER:
            # Уведомления о заказах могут получать все (включая гостей)
            return True

        elif notification_type == cls.NotificationType.SYSTEM:
            # Системные уведомления - только для аутентифицированных пользователей
            return user.role in ['user', 'moderator', 'owner', 'store_owner', 'store_admin']

        # По умолчанию запрещаем
        return False

    def get_notification_type_display_verbose(self):
        """Возвращает подробное описание типа уведомления"""
        type_descriptions = {
            'like': 'Лайк',
            'comment': 'Комментарий',
            'follow': 'Подписка',
            'mention': 'Упоминание',
            'system': 'Системное',
            'order': 'Заказ',
            'chat_message': 'Сообщение в чате',
        }
        return type_descriptions.get(self.notification_type, self.get_notification_type_display())

class UserProfile(models.Model):
    """
    Расширенная информация профиля пользователя.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile_extra',
        verbose_name=_("Пользователь")
    )

    # === ПОЛЯ ДЛЯ ВРЕМЕННЫХ ПАРОЛЕЙ ===
    temp_password = models.BooleanField(
        _("Временный пароль"),
        default=False,
        help_text=_("Отмечено, если пользователь использует временный пароль")
    )

    password_expires_at = models.DateTimeField(
        _("Пароль истекает"),
        null=True,
        blank=True,
        help_text=_("Дата и время истечения временного пароля")
    )

    # Дополнительные поля профиля
    birth_date = models.DateField(
        _("Дата рождения"),
        null=True,
        blank=True
    )

    phone = models.CharField(
        _("Телефон"),
        max_length=20,
        blank=True
    )

    preferred_language = models.CharField(
        _("Предпочитаемый язык"),
        max_length=10,
        choices=[
            ('ru', 'Русский'),
            ('en', 'English'),
            ('ua', 'Українська'),
        ],
        default='ru'
    )

    timezone = models.CharField(
        _("Часовой пояс"),
        max_length=50,
        default='Europe/Moscow'
    )

    # Настройки профиля
    theme_preference = models.CharField(
        _("Тема оформления"),
        max_length=10,
        choices=[
            ('light', _('Светлая')),
            ('dark', _('Темная')),
            ('auto', _('Автоматически')),
        ],
        default='light'
    )

    # Дополнительные интересы
    favorite_strains = models.TextField(
        _("Любимые сорта"),
        blank=True,
        help_text=_("Перечислите ваши любимые сорта через запятую")
    )

    growing_style = models.CharField(
        _("Стиль выращивания"),
        max_length=50,
        choices=[
            ('indoor', _('🏠 Индор')),
            ('outdoor', _('🌞 Аутдор')),
            ('greenhouse', _('🏡 Теплица')),
            ('mixed', _('🔄 Смешанный')),
        ],
        blank=True
    )

    equipment = models.TextField(
        _("Оборудование"),
        blank=True,
        help_text=_("Опишите ваше оборудование для выращивания")
    )

    class Meta:
        verbose_name = _("Расширенный профиль")
        verbose_name_plural = _("Расширенные профили")

    def __str__(self):
        return f"Профиль {self.user}"

    # === МЕТОДЫ ДЛЯ ВРЕМЕННЫХ ПАРОЛЕЙ ===
    def set_temp_password(self, valid_hours=24):
        """Устанавливает режим временного пароля"""
        from django.utils import timezone
        from datetime import timedelta
        self.temp_password = True
        self.password_expires_at = timezone.now() + timedelta(hours=valid_hours)
        self.save()

    def clear_temp_password(self):
        """Очищает режим временного пароля"""
        self.temp_password = False
        self.password_expires_at = None
        self.save()

    def is_temp_password_expired(self):
        """Проверяет, истек ли срок временного пароля"""
        if not self.temp_password or not self.password_expires_at:
            return False
        from django.utils import timezone
        return self.password_expires_at < timezone.now()
