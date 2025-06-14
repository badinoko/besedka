from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.mail import send_mail
import hashlib
import hmac
import time
from .models import User, BanRecord, Notification
from .forms import CustomUserCreationForm, UserProfileForm, UnbanRequestForm
from django.views.generic import DetailView, ListView, RedirectView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django import forms
from core.models import ActionLog
from core.monitoring import PlatformMonitor
from core.base_views import UnifiedListView

# Получаем модель пользователя
UserModel = get_user_model()

# Ваш пользовательский класс формы регистрации
class RegistrationForm(UserCreationForm):
    class Meta:
        model = UserModel
        fields = ['username', 'email', 'password1', 'password2']

@login_required
def profile(request):
    """User profile view."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Профиль успешно обновлен!"))
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "users/profile.html", {"user": request.user, "form": form})

def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('news:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Проверка на бан
                if user.is_banned:
                    # Найти последний активный бан
                    active_ban = BanRecord.objects.filter(
                        user=user,
                        ban_type=BanRecord.BAN_TYPE_GLOBAL,
                        is_active=True
                    ).order_by('-created_at').first()

                    if active_ban:
                        ban_reason = active_ban.reason
                        ban_expires = active_ban.expires_at
                    else:
                        ban_reason = None
                        ban_expires = None

                    return render(request, "users/unban_request.html", {
                        "form": UnbanRequestForm(initial={"email": user.email}),
                        "ban_reason": ban_reason,
                        "ban_expires": ban_expires,
                        "ban_email": user.email
                    })

                login(request, user)
                messages.success(request, _("Вы успешно вошли в систему!"))
                return redirect('news:home')
            else:
                messages.error(request, _("Неверные имя пользователя или пароль."))
        else:
            messages.error(request, _("Неверные имя пользователя или пароль."))
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})

def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('news:home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _("Вы успешно зарегистрировались!"))
            return redirect('news:home')
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})

def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, _("Вы вышли из системы."))
    return redirect('news:home')

def unban_request_view(request):
    """View for banned users to request unbanning."""
    if request.method == 'POST':
        form = UnbanRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            reason = form.cleaned_data['reason']

            # Отправка уведомления администраторам
            try:
                admins = UserModel.objects.filter(role__in=['owner', 'admin'], is_active=True)
                admin_emails = [admin.email for admin in admins if admin.email]

                subject = _('Новый запрос на разбан')
                message = _(f"""
                Пользователь запросил снятие бана:

                Email: {email}
                Причина запроса: {reason}
                """)

                if admin_emails:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=admin_emails,
                        fail_silently=True,
                    )

                success_message = _("Ваш запрос на снятие бана успешно отправлен администрации. Мы свяжемся с вами по указанному email.")
                return render(request, "users/unban_request.html", {
                    "form": form,
                    "success_message": success_message
                })
            except Exception as e:
                messages.error(request, _("Произошла ошибка при отправке запроса. Пожалуйста, попробуйте позже."))
    else:
        form = UnbanRequestForm()

    return render(request, "users/unban_request.html", {"form": form})

@csrf_exempt
def telegram_login(request):
    """
    Handle Telegram login callback.
    Validates data from Telegram Login Widget.
    """
    if request.method == 'GET':
        # Получаем данные от Telegram Login Widget
        telegram_data = request.GET.dict()
        is_registration = telegram_data.pop('register', '0') == '1'

        # Проверяем, что все необходимые данные получены
        required_fields = ['id', 'first_name', 'username', 'auth_date', 'hash']
        if not all(field in telegram_data for field in required_fields):
            return HttpResponseBadRequest("Incomplete Telegram data")

        # Проверяем подлинность данных
        telegram_hash = telegram_data.pop('hash')
        check_hash = generate_telegram_hash(telegram_data, settings.TELEGRAM_BOT_TOKEN)

        if telegram_hash != check_hash:
            return HttpResponseBadRequest("Invalid hash")

        # Проверяем актуальность данных (не старше 24 часов)
        auth_date = int(telegram_data.get('auth_date', 0))
        if time.time() - auth_date > 86400:
            return HttpResponseBadRequest("Authentication data expired")

        # Находим или создаем пользователя
        try:
            telegram_id = telegram_data.get('id')
            username = telegram_data.get('username')

            # Если имя пользователя не предоставлено, используем имя + id
            if not username:
                username = f"{telegram_data.get('first_name')}_{telegram_id}"

            # Проверяем, существует ли пользователь
            try:
                user = UserModel.objects.get(telegram_id=telegram_id)
                # Проверка на бан
                if user.is_banned:
                    # Найти последний активный бан
                    active_ban = BanRecord.objects.filter(
                        user=user,
                        ban_type=BanRecord.BAN_TYPE_GLOBAL,
                        is_active=True
                    ).order_by('-created_at').first()

                    if active_ban:
                        ban_reason = active_ban.reason
                        ban_expires = active_ban.expires_at
                    else:
                        ban_reason = None
                        ban_expires = None

                    return render(request, "users/unban_request.html", {
                        "form": UnbanRequestForm(initial={"email": user.email}),
                        "ban_reason": ban_reason,
                        "ban_expires": ban_expires,
                        "ban_email": user.email
                    })

                # Обновляем данные пользователя
                user.username = username
                # Формируем поле name из first_name и last_name от Telegram
                tg_first_name = telegram_data.get('first_name', '')
                tg_last_name = telegram_data.get('last_name', '')
                if tg_last_name:
                    user.name = f"{tg_first_name} {tg_last_name}".strip()
                else:
                    user.name = tg_first_name
                user.save()
                created = False
            except UserModel.DoesNotExist:
                # Проверяем, существует ли пользователь с таким же именем
                if UserModel.objects.filter(username=username).exists():
                    # Добавляем случайный суффикс к имени пользователя
                    username = f"{username}_{telegram_id[-4:]}"

                # Формируем поле name для нового пользователя
                tg_first_name = telegram_data.get('first_name', '')
                tg_last_name = telegram_data.get('last_name', '')
                if tg_last_name:
                    user_name_field = f"{tg_first_name} {tg_last_name}".strip()
                else:
                    user_name_field = tg_first_name

                # Создаем нового пользователя
                user = UserModel.objects.create(
                    telegram_id=telegram_id,
                    username=username,
                    name=user_name_field, # Используем сформированное поле name
                    role='user'  # Роль по умолчанию
                )
                created = True

            # Логиним пользователя
            login(request, user)

            if created:
                messages.success(request, _("Аккаунт успешно создан через Telegram!"))
            else:
                messages.success(request, _("Вы вошли через Telegram!"))

            return redirect('news:home')

        except Exception as e:
            messages.error(request, _(f"Ошибка аутентификации: {str(e)}"))
            return redirect('users:login')

    return HttpResponseBadRequest("Invalid request method")

def generate_telegram_hash(data, bot_token):
    """
    Generate hash for validating Telegram Login Widget data.
    """
    # Создаем data_check_string
    data_check_list = []
    for key, value in sorted(data.items()):
        data_check_list.append(f"{key}={value}")
    data_check_string = '\n'.join(data_check_list)

    # Получаем секретный ключ
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # Создаем и возвращаем хеш
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

class UserDetailView(LoginRequiredMixin, DetailView):
    model = UserModel
    slug_field = "username"
    slug_url_arg = "username"

user_detail_view = UserDetailView.as_view()

class UserListView(LoginRequiredMixin, UnifiedListView):
    """Унифицированный список пользователей"""
    model = UserModel
    template_name = 'base_list_page.html'
    context_object_name = 'users'
    paginate_by = 12

    card_type = 'user'
    section_hero_class = 'users-hero'

    # Переопределяем карты для пользователей
    def get_unified_cards(self, page_obj):
        cards = []
        for user in page_obj:
            avatar_url = user.avatar.url if getattr(user, 'avatar', None) else '/static/images/default_avatar.svg'
            cards.append({
                'id': user.id,
                'type': 'user',
                'title': user.username,
                'description': user.bio[:120] if getattr(user, 'bio', '') else '',
                'image_url': avatar_url,
                'detail_url': reverse_lazy('users:detail', kwargs={'username': user.username}),
                'author': {'name': user.username, 'avatar': avatar_url},
                'stats': [
                    {'icon': 'fa-image', 'count': getattr(user, 'photos_count', 0) if hasattr(user, 'photos_count') else 0, 'css': 'photos'},
                    {'icon': 'fa-book', 'count': getattr(user, 'growlogs_count', 0) if hasattr(user, 'growlogs_count') else 0, 'css': 'growlogs'},
                ],
                'created_at': user.date_joined,
            })
        return cards

    def get_filter_list(self):
        return []

    def get_hero_stats(self):
        return [
            {'value': self.model.objects.count(), 'label': 'Пользователей'},
        ]

user_list_view = UserListView.as_view()

class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse_lazy("users:detail", kwargs={"username": self.request.user.username})

user_redirect_view = UserRedirectView.as_view()

# ===== ФОРМЫ ДЛЯ ЛИЧНОГО КАБИНЕТА =====

class ProfileForm(forms.ModelForm):
    """Форма для редактирования профиля пользователя"""

    class Meta:
        model = UserModel
        fields = ['name', 'username', 'email', 'bio', 'avatar', 'telegram_username']
        labels = {
            'name': '👤 Отображаемое имя',
            'username': '🏷️ Никнейм (логин)',
            'email': '📧 Email адрес',
            'bio': '📝 О себе',
            'avatar': '🖼️ Аватар',
            'telegram_username': '�� Telegram Username'
        }
        help_texts = {
            'name': 'Как вас будут видеть другие пользователи',
            'username': 'Уникальное имя для входа',
            'email': 'Для восстановления пароля и уведомлений',
            'bio': 'Расскажите о себе (необязательно)',
            'avatar': 'Картинка профиля (необязательно)',
            'telegram_username': 'Ваш username в Telegram (без @, необязательно)'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше имя'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'nickname'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@example.com'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Немного о себе...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'telegram_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ' ваш_telegram_username'})
        }

class RoleManagementForm(forms.ModelForm):
    """Форма для управления ролями админов (только для владельцев)"""

    class Meta:
        model = UserModel
        fields = ['role']

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user

        # Определяем доступные роли в зависимости от того, кто делает изменения
        if current_user and current_user.role == 'owner':
            # Владелец платформы может назначать и увольнять админов платформы
            choices = [
                ('user', '👤 Обычный пользователь'),
                ('admin', '🎭 Администратор платформы'),
            ]
        elif current_user and current_user.role == 'store_owner':
            # Владелец магазина может назначать и увольнять админов магазина
            choices = [
                ('user', '👤 Обычный пользователь'),
                ('store_admin', '📦 Администратор магазина'),
            ]
        else:
            choices = []

        self.fields['role'].widget.choices = choices
        self.fields['role'].widget.attrs.update({'class': 'form-control'})

# ===== VIEWS ДЛЯ ЛИЧНОГО КАБИНЕТА =====

class NotificationListView(LoginRequiredMixin, UnifiedListView):
    """Унифицированный список уведомлений"""
    model = Notification
    template_name = 'base_list_page.html'
    context_object_name = 'notifications'
    paginate_by = 20

    card_type = 'notification'
    section_hero_class = 'notifications-hero'

    def get_queryset(self):
        return self.request.user.notifications.all().order_by('-created_at')

    def get_filter_list(self):
        return []

    def get_unified_cards(self, page_obj):
        cards = []
        for notif in page_obj:
            sender_name = notif.sender.username if notif.sender else 'Система'
            cards.append({
                'id': notif.id,
                'type': 'notification',
                'title': notif.title or 'Уведомление',
                'description': notif.message[:140] if notif.message else '',
                'image_url': '/static/images/default_notification.svg',
                'detail_url': reverse_lazy('users:notification_list'),
                'author': {'name': sender_name, 'avatar': None},
                'stats': [],
                'created_at': notif.created_at,
                'is_read': notif.is_read,
            })
        return cards

    def get_hero_stats(self):
        qs = self.get_queryset()
        return [
            {'value': qs.count(), 'label': 'Всего'},
            {'value': qs.filter(is_read=False).count(), 'label': 'Непрочитано'},
        ]

    def get_hero_actions(self):
        """Кнопки bulk-действий для уведомлений"""
        return [
            {
                'url': '#',
                'label': 'Прочитать все',
                'icon': 'fas fa-envelope-open-text',
                'is_primary': True,
                'css_class': '',
                'html_id': 'markAllRead',
            },
            {
                'url': '#',
                'label': 'Прочитать выбранные',
                'icon': 'fas fa-envelope-open',
                'is_primary': False,
                'css_class': '',
                'html_id': 'markSelectedRead',
            },
            {
                'url': '#',
                'label': 'Удалить выбранные',
                'icon': 'fas fa-trash',
                'is_primary': False,
                'css_class': 'btn-danger',
                'html_id': 'deleteSelected',
            },
        ]

notification_list_view = NotificationListView.as_view()

@login_required
def mark_notification_read(request, notification_id):
    """Помечает уведомление как прочитанное"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    # Если это AJAX запрос, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Уведомление помечено как прочитанное',
            'unread_notifications_count': request.user.notifications.filter(is_read=False).count(),
            'total_notifications_count': request.user.notifications.count()  # Добавлено
        })

    # Перенаправляем на связанный объект, если есть
    if notification.content_object and hasattr(notification.content_object, 'get_absolute_url'):
        return redirect(notification.content_object.get_absolute_url())

    # Иначе возвращаем к списку уведомлений
    return redirect('users:notification_list')

@login_required
def mark_all_notifications_read(request):
    """Помечает все уведомления пользователя как прочитанные"""
    if request.method == 'POST':
        updated_count = request.user.notifications.filter(is_read=False).update(is_read=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX запрос
            unread_notifications_count = request.user.notifications.filter(is_read=False).count()
            total_notifications_count = request.user.notifications.count()
            return JsonResponse({
                'success': True,
                'updated_count': updated_count,
                'message': f'Помечено как прочитанные: {updated_count} уведомлений' if updated_count > 0 else 'Все уведомления уже прочитаны',
                # Унифицированные ключи для всех функций
                'unread_count': unread_notifications_count,
                'total_count': total_notifications_count,
                'unread_notifications_count': unread_notifications_count,
                'total_notifications_count': total_notifications_count
            })
        else:
            # Обычный запрос
            if updated_count > 0:
                messages.success(request, f'✅ Помечено как прочитанные: {updated_count} уведомлений')
            else:
                messages.info(request, 'ℹ️ Все уведомления уже прочитаны')

    return redirect('users:notification_list')

@login_required
def mark_multiple_notifications_read(request):
    """Помечает выбранные уведомления как прочитанные (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])

        if not notification_ids:
            return JsonResponse({'error': 'Не выбраны уведомления'}, status=400)

        # Обновляем только уведомления текущего пользователя
        updated_count = request.user.notifications.filter(
            id__in=notification_ids,
            is_read=False
        ).update(is_read=True)

        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        total_notifications_count = request.user.notifications.count()  # Добавлено
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'message': f'Помечено как прочитанные: {updated_count} уведомлений',
            'unread_notifications_count': unread_notifications_count,
            'total_notifications_count': total_notifications_count  # Добавлено
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_multiple_notifications(request):
    """Удаляет выбранные уведомления (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])

        if not notification_ids:
            return JsonResponse({'error': 'Не выбраны уведомления'}, status=400)

        # Удаляем только уведомления текущего пользователя
        deleted_count, _ = request.user.notifications.filter(
            id__in=notification_ids
        ).delete()

        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        total_notifications_count = request.user.notifications.count() # Новый общий счетчик
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Удалено уведомлений: {deleted_count}',
            'unread_notifications_count': unread_notifications_count,
            'total_notifications_count': total_notifications_count # Добавлено в ответ
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_notification(request, notification_id):
    """Удаляет отдельное уведомление (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user
        )

        notification.delete()

        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        total_notifications_count = request.user.notifications.count() # Новый общий счетчик
        return JsonResponse({
            'success': True,
            'message': 'Уведомление удалено',
            'unread_notifications_count': unread_notifications_count,
            'total_notifications_count': total_notifications_count # Добавлено в ответ
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class ProfileView(LoginRequiredMixin, TemplateView):
    # template_name = 'users/profile.html' # Будет определен в get_template_names

    def get_user_stats(self):
        user = self.request.user
        # Реальная логика сбора статистики, если она есть, иначе заглушка
        # Например, из ActionLog или отдельных моделей
        return {
            'orders_count': user.orders.count() if hasattr(user, 'orders') else 0,
            'growlogs_count': user.growlogs.count() if hasattr(user, 'growlogs') else 0,
            'photos_count': user.photos.count() if hasattr(user, 'photos') else 0,
        }

    def get_recent_activity(self):
        # Получение последних 5 действий пользователя из ActionLog
        return ActionLog.objects.filter(user=self.request.user).order_by('-timestamp')[:5]

    def get_template_names(self):
        user = self.request.user
        if user.role == 'owner':
            return ['users/cabinet_owner.html']
        elif user.role == 'admin': # Модератор платформы
            return ['users/cabinet_moderator.html']
        elif user.role == 'store_owner':
            return ['users/cabinet_store_owner.html']
        elif user.role == 'store_admin':
            return ['users/cabinet_store_admin.html']
        else: # Обычный пользователь
            return ['users/cabinet_user.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['page_title'] = _("Личный кабинет")

        # Общая информация для всех ролей
        context['user_stats'] = self.get_user_stats()
        context['recent_activity'] = self.get_recent_activity()

        # Статистика для специфических ролей
        if user.role == 'owner' or user.role == 'admin':
            context['platform_stats'] = PlatformMonitor.get_platform_stats()

        if user.role == 'store_owner' or user.role == 'store_admin':
            context['store_stats'] = PlatformMonitor.get_store_stats()

        # Бейдж роли уже должен быть в контексте из context_processor (user_role_badge)
        # Навигационные элементы также из context_processor (navigation_items, admin_navigation_items)
        return context

profile_view = ProfileView.as_view() # Для использования в urls.py

@login_required
def edit_profile_view(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Профиль успешно обновлен!')
            return redirect('users:profile')
        else:
            messages.error(request, '❌ Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def change_password_view(request):
    """Смена пароля"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Важно! Чтобы пользователь остался залогинен
            messages.success(request, '✅ Пароль успешно изменен!')
            return redirect('users:profile')
        else:
            messages.error(request, '❌ Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/change_password.html', {'form': form})

@login_required
def manage_admins_view(request):
    """Управление администраторами (только для владельцев)"""
    user = request.user

    # Проверяем права доступа
    if user.role not in ['owner', 'store_owner']:
        messages.error(request, '❌ У вас нет прав для управления администраторами!')
        return redirect('users:profile')

    # Определяем кого можем управлять
    if user.role == 'owner':
        # Владелец платформы управляет админами платформы
        managed_users = UserModel.objects.filter(role__in=['admin', 'user']).exclude(pk=user.pk)
        title = "Управление администраторами платформы"
        can_promote_to = 'admin'
    else:  # store_owner
        # Владелец магазина управляет админами магазина
        managed_users = UserModel.objects.filter(role__in=['store_admin', 'user']).exclude(pk=user.pk)
        title = "Управление администраторами магазина"
        can_promote_to = 'store_admin'

    context = {
        'managed_users': managed_users,
        'title': title,
        'can_promote_to': can_promote_to,
        'user': user,
    }

    return render(request, 'users/manage_admins.html', context)

@login_required
def change_user_role_view(request, user_id):
    """Изменение роли пользователя"""
    current_user = request.user
    target_user = get_object_or_404(UserModel, pk=user_id)

    # Проверяем права доступа
    if current_user.role == 'owner':
        # Владелец платформы может управлять админами платформы
        if target_user.role not in ['admin', 'user']:
            messages.error(request, '❌ Вы не можете изменить роль этого пользователя!')
            return redirect('users:manage_admins')
    elif current_user.role == 'store_owner':
        # Владелец магазина может управлять админами магазина
        if target_user.role not in ['store_admin', 'user']:
            messages.error(request, '❌ Вы не можете изменить роль этого пользователя!')
            return redirect('users:manage_admins')
    else:
        messages.error(request, '❌ У вас нет прав для изменения ролей!')
        return redirect('users:profile')

    if request.method == 'POST':
        form = RoleManagementForm(request.POST, instance=target_user, current_user=current_user)
        if form.is_valid():
            old_role = target_user.role
            new_role = form.cleaned_data['role']

            # Сохраняем изменения
            target_user.role = new_role
            target_user.is_staff = new_role in ['admin', 'store_owner', 'store_admin']
            target_user.save()

            # Определяем действие
            if old_role != 'user' and new_role == 'user':
                action = 'уволен с должности'
                icon = '👇'
            elif old_role == 'user' and new_role != 'user':
                action = 'назначен на должность'
                icon = '👆'
            else:
                action = 'изменена роль'
                icon = '🔄'

            messages.success(request, f'{icon} Пользователь {target_user.username} {action}!')
            return redirect('users:manage_admins')
        else:
            messages.error(request, '❌ Пожалуйста, исправьте ошибки в форме.')
    else:
        form = RoleManagementForm(instance=target_user, current_user=current_user)

    context = {
        'form': form,
        'target_user': target_user,
        'current_user': current_user,
    }

    return render(request, 'users/change_role.html', context)
