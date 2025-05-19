from django.db import models
from django.utils.translation import gettext_lazy as _


class ActionLog(models.Model):
    """Журнал действий пользователей."""
    ACTION_ADD = "add"
    ACTION_EDIT = "edit"
    ACTION_DELETE = "delete"
    ACTION_VIEW = "view"
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"

    ACTION_CHOICES = [
        (ACTION_ADD, _("Добавление")),
        (ACTION_EDIT, _("Редактирование")),
        (ACTION_DELETE, _("Удаление")),
        (ACTION_VIEW, _("Просмотр")),
        (ACTION_LOGIN, _("Вход")),
        (ACTION_LOGOUT, _("Выход")),
    ]

    user = models.ForeignKey(
        "auth.User",  # Используем строку чтобы избежать циклического импорта
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Пользователь"),
        related_name="action_logs",
    )
    action_type = models.CharField(
        _("Тип действия"),
        max_length=20,
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
