from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# @admin.register(User) # Декоратор будет удален или закомментирован
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'name', 'is_staff')
    search_fields = ('username', 'name', 'email')
    ordering = ('username',)
