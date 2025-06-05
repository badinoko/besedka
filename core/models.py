from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class TimeStampedModel(models.Model):
    """
    Abstract base class model that provides self-updating
    created and modified fields.
    """
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        abstract = True

class PublicModel(TimeStampedModel):
    """
    Abstract base class model that provides public/private visibility.
    """
    is_public = models.BooleanField(_("Public"), default=True)

    class Meta:
        abstract = True

class ActionLog(models.Model):
    """
    Log of user actions in the system.
    """
    ACTION_ADD = "add"
    ACTION_EDIT = "edit"
    ACTION_DELETE = "delete"
    ACTION_VIEW = "view"
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_TEMP_PASSWORD_CREATED = "temp_password_created"

    ACTION_CHOICES = [
        (ACTION_ADD, _("Добавление")),
        (ACTION_EDIT, _("Редактирование")),
        (ACTION_DELETE, _("Удаление")),
        (ACTION_VIEW, _("Просмотр")),
        (ACTION_LOGIN, _("Вход")),
        (ACTION_LOGOUT, _("Выход")),
        (ACTION_TEMP_PASSWORD_CREATED, _("Создан временный пароль")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Пользователь"),
        related_name="action_logs",
    )
    action_type = models.CharField(
        _("Тип действия"),
        max_length=30,
        choices=ACTION_CHOICES,
    )
    timestamp = models.DateTimeField(
        _("Время действия"),
        auto_now_add=True,
    )
    model_name = models.CharField(
        _("Название модели"),
        max_length=100,
    )
    object_id = models.PositiveIntegerField(
        _("ID объекта"),
        null=True,
        blank=True,
    )
    object_repr = models.CharField(
        _("Представление объекта"),
        max_length=255,
    )
    details = models.TextField(
        _("Детали"),
        blank=True,
    )

    class Meta:
        verbose_name = _("Запись журнала")
        verbose_name_plural = _("Журнал действий")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.object_repr} ({self.timestamp})"

class MaintenanceModeSetting(models.Model):
    """
    Настройки режима технического обслуживания для различных разделов сайта.
    """
    SECTION_CHOICES = [
        ('chat', _('Чат')),
        ('gallery', _('Галерея')),
        ('growlogs', _('Гроу-репорты')),
        ('store', _('Магазин')),
        # Добавьте другие разделы по необходимости
    ]

    COLOR_SCHEME_CHOICES = [
        ('blue', _('Синяя (информационная)')),
        ('orange', _('Оранжевая (предупреждение)')),
        ('red', _('Красная (критично/недоступно)')),
    ]

    section_name = models.CharField(
        _("Название раздела"),
        max_length=50,
        choices=SECTION_CHOICES,
        unique=True, # Уникальное имя раздела
        help_text=_("Выберите раздел сайта.")
    )
    is_enabled = models.BooleanField(
        _("Режим обслуживания включен"),
        default=False,
        help_text=_("Включить/выключить режим технического обслуживания для этого раздела.")
    )
    title = models.CharField(
        _("Заголовок страницы обслуживания"),
        max_length=200,
        default=_("Техническое обслуживание"),
        help_text=_("Заголовок, который увидят пользователи (например, 'Чат временно недоступен').")
    )
    message = models.TextField(
        _("Сообщение для пользователей"),
        default=_("Мы работаем над улучшением этого раздела. Пожалуйста, зайдите позже."),
        help_text=_("Подробное сообщение для пользователей.")
    )
    expected_recovery_time = models.CharField(
        _("Ожидаемое время восстановления"),
        max_length=100,
        blank=True,
        null=True,
        default=_("В ближайшее время"),
        help_text=_("Например, 'В течение часа', 'До 15:00 МСК', 'В ближайшее время'.")
    )
    color_scheme = models.CharField(
        _("Цветовая схема страницы"),
        max_length=20,
        choices=COLOR_SCHEME_CHOICES,
        default='blue',
        help_text=_("Выберите цветовую схему для страницы обслуживания.")
    )
    # Это поле можно использовать для формирования ссылок на активные разделы.
    # Например, если section_name = 'chat', то url_name = 'chat:chat_room_list' (пример)
    # Оставляю пока пустым, так как точные URL-имена еще не определены для всех разделов.
    # Мы сможем заполнить его позже, когда определимся с URL-структурой для всех разделов.
    # Пока что будем просто проверять по section_name
    # url_name_for_check = models.CharField(
    # _("URL-имя для проверки активности (например, 'gallery:list')"),
    # max_length=100,
    # blank=True,
    # null=True,
    # help_text=_("URL-имя, используемое для проверки, активен ли раздел (для отображения в альтернативных ссылках).")
    # )


    class Meta:
        verbose_name = _("Настройка режима обслуживания")
        verbose_name_plural = _("Настройки режимов обслуживания")
        ordering = ['section_name']

    def __str__(self):
        return f"{self.get_section_name_display()} - {'Включен' if self.is_enabled else 'Выключен'}"
