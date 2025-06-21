from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# Переопределим админку пользователей для поддержки прав
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                # Ограничение доступа к разделу прав только для владельцев
                "classes": ("collapse",),
                "description": _("Расширенные права доступны только владельцам магазина."),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    def get_fieldsets(self, request, obj=None):
        """
        Показывать расширенные права только владельцам
        """
        fieldsets = super().get_fieldsets(request, obj)

        # Проверяем, является ли пользователь владельцем
        is_owner = request.user.groups.filter(name="Владельцы").exists() or request.user.is_superuser

        if not is_owner:
            # Удаляем раздел "Permissions" для не-владельцев
            return fieldsets[:2] + fieldsets[3:]  # Пропускаем permissions fieldset
        return fieldsets

    def get_queryset(self, request):
        """
        Ограничение видимости пользователей в зависимости от группы
        """
        qs = super().get_queryset(request)

        # Владельцы видят всех пользователей
        if request.user.groups.filter(name="Владельцы").exists() or request.user.is_superuser:
            return qs

        # Администраторы видят только себя
        return qs.filter(pk=request.user.pk)

# Перерегистрируем модель пользователя с нашей админкой
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
