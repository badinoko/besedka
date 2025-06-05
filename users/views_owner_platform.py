from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.core.exceptions import PermissionDenied
import logging

from .forms_owner_platform import AssignStoreOwnerForm, DeactivateStoreOwnerForm
from users.models import UserProfile
from .utils import TemporaryPasswordManager
from core.models import ActionLog

User = get_user_model()
logger = logging.getLogger(__name__)

class OwnerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав доступа владельца платформы"""

    def test_func(self):
        return (
            self.request.user.is_authenticated and
            self.request.user.role == User.Role.OWNER
        )

    def handle_no_permission(self):
        messages.error(self.request, "❌ Доступ запрещен. Только владелец платформы может управлять владельцами магазина.")
        return redirect('owner_admin:index')

class ManageStoreOwnerView(OwnerRequiredMixin, LoginRequiredMixin, View):
    template_name = "owner_admin/manage_store_owner.html"
    assign_form_class = AssignStoreOwnerForm
    deactivate_form_class = DeactivateStoreOwnerForm

    def _get_common_context(self, request, assign_form=None, deactivate_form=None, temp_password_details=None):
        current_store_owner = User.objects.filter(role=User.Role.STORE_OWNER, is_active=True).first()
        context = {
            "form": assign_form if assign_form else self.assign_form_class(),
            "deactivate_form": deactivate_form if deactivate_form else self.deactivate_form_class(),
            "current_store_owner": current_store_owner,
            "title": "Управление Владельцем Магазина",
            **(request.admin_site.each_context(request) if hasattr(request, 'admin_site') else {})
        }
        if temp_password_details:
            context["temp_password_details"] = temp_password_details
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self._get_common_context(request))

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Определяем, какая форма отправлена (по наличию специфического поля/кнопки)
        if "assign_owner_submit" in request.POST:
            return self._handle_assign_owner(request)
        elif "deactivate_owner_submit" in request.POST:
            return self._handle_deactivate_owner(request)

        messages.error(request, "❌ Неизвестное действие.")
        return render(request, self.template_name, self._get_common_context(request))

    @transaction.atomic
    def _handle_assign_owner(self, request):
        assign_form = self.assign_form_class(request.POST)
        if assign_form.is_valid():
            username = assign_form.cleaned_data['username']
            email = assign_form.cleaned_data['email']
            first_name = assign_form.cleaned_data.get('first_name', '')
            last_name = assign_form.cleaned_data.get('last_name', '')

            # КРИТИЧЕСКАЯ ЗАЩИТА: Проверяем, что не пытаемся изменить владельца платформы
            if username == 'owner_user':
                messages.error(
                    request,
                    "🚫 КРИТИЧЕСКАЯ ОШИБКА: Нельзя изменить роль владельца платформы! "
                    "Это защищенный аккаунт системы."
                )
                return render(request, self.template_name, self._get_common_context(request, assign_form=assign_form))

            try:
                # Проверяем, существует ли уже активный владелец магазина
                existing_store_owner = User.objects.filter(role=User.Role.STORE_OWNER, is_active=True).first()
                if existing_store_owner:
                    messages.warning(
                        request,
                        f"⚠️ Уже есть активный владелец магазина: {existing_store_owner.username}. "
                        f"Сначала деактивируйте его, если хотите назначить нового."
                    )
                    return render(request, self.template_name, self._get_common_context(request, assign_form=assign_form))

                # Проверяем, существует ли пользователь с таким именем
                existing_user = User.objects.filter(username=username).first()
                if existing_user:
                    # ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА: Проверяем, что это не владелец платформы
                    if existing_user.username == 'owner_user' or existing_user.role == 'owner':
                        messages.error(
                            request,
                            "🚫 КРИТИЧЕСКАЯ ОШИБКА: Нельзя изменить роль владельца платформы!"
                        )
                        return render(request, self.template_name, self._get_common_context(request, assign_form=assign_form))

                    # Повышаем существующего пользователя до владельца магазина
                    existing_user.role = User.Role.STORE_OWNER
                    existing_user.is_staff = True
                    existing_user.is_active = True
                    if first_name:
                        existing_user.first_name = first_name
                    if last_name:
                        existing_user.last_name = last_name
                    if first_name or last_name:
                        existing_user.name = f"{first_name} {last_name}".strip()
                    existing_user.save()

                    # Создаем временный пароль
                    temp_password_details = TemporaryPasswordManager.create_temporary_password_for_user(
                        existing_user, valid_hours=24
                    )

                    messages.success(
                        request,
                        f"✅ Пользователь '{username}' назначен владельцем магазина. "
                        f"Временный пароль создан и действителен 24 часа."
                    )

                    # Логирование
                    ActionLog.objects.create(
                        user=request.user,
                        action_type=ActionLog.ACTION_EDIT,
                        model_name=User.__name__,
                        object_id=existing_user.pk,
                        object_repr=str(existing_user),
                        details=f'Назначен владельцем магазина. Создан временный пароль.'
                    )

                    return render(request, self.template_name,
                                self._get_common_context(request, temp_password_details=temp_password_details))

                else:
                    # Создаем нового пользователя
                    new_user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role=User.Role.STORE_OWNER,
                        is_staff=True,
                        is_active=True
                    )

                    # Устанавливаем поле name
                    new_user.name = f"{first_name} {last_name}".strip()
                    new_user.save()

                    # Создаем временный пароль
                    temp_password_details = TemporaryPasswordManager.create_temporary_password_for_user(
                        new_user, valid_hours=24
                    )

                    messages.success(
                        request,
                        f"✅ Новый владелец магазина '{username}' создан успешно. "
                        f"Временный пароль действителен 24 часа."
                    )

                    # Логирование
                    ActionLog.objects.create(
                        user=request.user,
                        action_type=ActionLog.ACTION_ADD,
                        model_name=User.__name__,
                        object_id=new_user.pk,
                        object_repr=str(new_user),
                        details=f'Создан новый владелец магазина. Временный пароль установлен.'
                    )

                    return render(request, self.template_name,
                                self._get_common_context(request, temp_password_details=temp_password_details))

            except Exception as e:
                messages.error(request, f"❌ Ошибка при создании пользователя: {e}")
                return render(request, self.template_name, self._get_common_context(request, assign_form=assign_form))
        else:
            # Форма невалидна
            return render(request, self.template_name, self._get_common_context(request, assign_form=assign_form))

    def _handle_deactivate_owner(self, request):
        deactivate_form = self.deactivate_form_class(request.POST)
        current_store_owner = User.objects.filter(role=User.Role.STORE_OWNER, is_active=True).first()

        if not current_store_owner:
            messages.warning(request, "⚠️ Нет активного Владельца Магазина для деактивации.")
            return redirect(reverse_lazy("owner_admin:manage_store_owner"))

        # КРИТИЧЕСКАЯ ЗАЩИТА: Проверяем, что не пытаемся деактивировать владельца платформы
        if current_store_owner.username == 'owner_user' or current_store_owner.role == 'owner':
            messages.error(
                request,
                "🚫 КРИТИЧЕСКАЯ ОШИБКА: Нельзя деактивировать владельца платформы! "
                "Это защищенный аккаунт системы."
            )
            return render(request, self.template_name, self._get_common_context(request, deactivate_form=deactivate_form))

        if deactivate_form.is_valid():
            confirm_deactivation = deactivate_form.cleaned_data.get('confirm_deactivation')
            if confirm_deactivation:
                # Сохраняем имя для сообщения
                original_username = current_store_owner.username

                # Деактивируем владельца магазина
                current_store_owner.role = User.Role.USER
                current_store_owner.is_staff = False
                current_store_owner.is_active = False
                current_store_owner.save()

                # Деактивируем всех администраторов магазина
                store_admins = User.objects.filter(role=User.Role.STORE_ADMIN, is_active=True)
                deactivated_admins_usernames = []
                for admin in store_admins:
                    # ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА: Проверяем каждого администратора
                    if admin.username == 'owner_user' or admin.role == 'owner':
                        continue  # Пропускаем владельца платформы

                    admin.role = User.Role.USER
                    admin.is_staff = False
                    admin.is_active = False
                    admin.save()
                    deactivated_admins_usernames.append(admin.username)

                logger.info(f"Владелец магазина {original_username} деактивирован, роль понижена до USER, is_staff сброшен.")

                # Очищаем временный пароль у деактивированного владельца
                UserProfile.objects.filter(user=current_store_owner).update(temp_password=False, password_expires_at=None)

                # Логирование действия
                ActionLog.objects.create(
                    user=request.user,
                    action_type=ActionLog.ACTION_EDIT,
                    model_name=User.__name__,
                    object_id=current_store_owner.pk,
                    object_repr=original_username,
                    details=f'Деактивирован и понижен в роли владелец магазина: {original_username}. '
                            f'Также деактивированы и понижены администраторы: {", ".join(deactivated_admins_usernames) if deactivated_admins_usernames else "нет"}.'
                )

                success_message = f"✅ Владелец магазина '{original_username}' был успешно деактивирован и понижен в роли."
                if deactivated_admins_usernames:
                    success_message += f" Также деактивированы и понижены администраторы магазина: {', '.join(deactivated_admins_usernames)}."
                messages.success(request, success_message)
            else:
                messages.error(request, "❌ Пожалуйста, подтвердите деактивацию.")
        else:
            messages.error(request, "❌ Ошибка в форме деактивации.")

        return render(request, self.template_name, self._get_common_context(request, deactivate_form=deactivate_form))

# TODO:
# - Добавить name атрибуты "assign_owner_submit" и "deactivate_owner_submit" к кнопкам в шаблоне.
# - Тщательно протестировать всю логику, включая краевые случаи.
# - Рассмотреть вопрос о судьбе Администраторов Магазина при деактивации Владельца Магазина.
# - Убедиться, что проверка прав доступа (has_permission в OwnerAdminSite) работает корректно.
