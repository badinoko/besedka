from django.shortcuts import redirect
from django.urls import reverse_lazy # Используем reverse_lazy для class-based views
from django.views.generic.edit import FormView
from django.contrib import messages
from django.contrib.auth import get_user_model

from .forms import StoreOwnerForm
from .utils import TemporaryPasswordManager
from core.models import ActionLog
# Предположим, что OwnerRequiredMixin существует. Если нет, его нужно создать.
# Примерно так он мог бы выглядеть:
# from django.contrib.auth.mixins import UserPassesTestMixin
# class OwnerRequiredMixin(UserPassesTestMixin):
#     def test_func(self):
#         return self.request.user.is_authenticated and getattr(self.request.user, 'role', None) == 'owner'
#     def handle_no_permission(self):
#         messages.error(self.request, "Доступ запрещен.")
#         return redirect('some_other_view') # или на главную, или на страницу логина

# ЗАГЛУШКА: Если OwnerRequiredMixin не определен глобально, используем UserPassesTestMixin
from django.contrib.auth.mixins import UserPassesTestMixin

User = get_user_model()

class OwnerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав доступа владельца платформы"""

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            getattr(self.request.user, 'role', None) == 'owner'
        )

    def handle_no_permission(self):
        messages.error(self.request, "Доступ запрещен. Только владелец платформы может управлять владельцами магазина.")
        return redirect('owner_admin:index')

class StoreOwnerManagementView(OwnerRequiredMixin, FormView):
    """Управление владельцами магазина (только для Owner платформы)."""
    template_name = 'owner_admin/store_owner_management.html'
    form_class = StoreOwnerForm
    success_url = reverse_lazy('users:store_owner_management')

    def get_context_data(self, **kwargs):
        """Добавляем текущих владельцев магазина в контекст"""
        context = super().get_context_data(**kwargs)

        # Получаем всех владельцев магазина
        current_store_owners = User.objects.filter(
            role='store_owner'
        ).select_related('profile_extra').order_by('-date_joined')

        context['current_store_owners'] = current_store_owners
        return context

    def form_valid(self, form):
        action = form.cleaned_data['action']
        current_user = self.request.user

        if action == 'create_new':
            # Создаем нового владельца магазина
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']

            # Проверяем, что пользователь не существует
            if User.objects.filter(username=username).exists():
                messages.error(self.request, f'Пользователь с именем "{username}" уже существует.')
                return self.form_invalid(form)

            if User.objects.filter(email=email).exists():
                messages.error(self.request, f'Пользователь с email "{email}" уже существует.')
                return self.form_invalid(form)

            # Создаем пользователя
            new_owner = User.objects.create_user(
                username=username,
                email=email,
                role='store_owner',
                is_staff=True  # Владельцы магазина должны иметь доступ к админке
            )

            # Создаем профиль для временного пароля
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=new_owner)

            # Генерируем временные учетные данные
            temp_creds = TemporaryPasswordManager.create_temp_credentials(new_owner, role='store_owner')

            messages.success(
                self.request,
                f'✅ Владелец магазина "{temp_creds["username"]}" создан успешно! '
                f'Временный пароль: <strong>{temp_creds["password"]}</strong> '
                f'(действителен до {temp_creds["expires_at"].strftime("%d.m.Y %H:%M") if temp_creds["expires_at"] else "неопределенного времени"}). '
                f'📧 Отправьте эти данные новому владельцу.'
            )

            # Логируем действие от имени Owner платформы
            if isinstance(current_user, User) and current_user.is_authenticated:
                ActionLog.objects.create(
                    user=current_user,
                    action_type=ActionLog.ACTION_ADD,
                    model_name=User.__name__,
                    object_id=new_owner.pk,
                    object_repr=str(new_owner),
                    details=f'Создан новый владелец магазина: {new_owner.username}. Временные учетные данные сгенерированы.'
                )

        elif action == 'revoke_access':
            # Отзываем доступ у существующего владельца
            user_to_revoke = form.cleaned_data['user_to_revoke']

            if user_to_revoke:
                # Деактивируем пользователя вместо удаления
                user_to_revoke.is_active = False
                user_to_revoke.save()

                messages.success(
                    self.request,
                    f'🚫 Доступ владельца магазина "{user_to_revoke.username}" отозван. '
                    f'Пользователь больше не может входить в систему.'
                )

                # Логируем действие
                if isinstance(current_user, User) and current_user.is_authenticated:
                    ActionLog.objects.create(
                        user=current_user,
                        action_type=ActionLog.ACTION_EDIT,
                        model_name=User.__name__,
                        object_id=user_to_revoke.pk,
                        object_repr=str(user_to_revoke),
                        details=f'Доступ владельца магазина {user_to_revoke.username} отозван'
                    )
            else:
                messages.error(self.request, 'Не выбран пользователь для отзыва доступа.')
                return self.form_invalid(form)

        return super().form_valid(form)
