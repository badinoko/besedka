from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import hashlib
import hmac
import time
from .models import User

# Ваш пользовательский класс формы регистрации
class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

@login_required
def profile(request):
    """User profile view."""
    return render(request, "users/profile.html", {"user": request.user})

def login_view(request):
    """User login view."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
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
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _("Вы успешно зарегистрировались!"))
            return redirect('news:home')
    else:
        form = RegistrationForm()
    return render(request, "users/register.html", {"form": form})

def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, _("Вы вышли из системы."))
    return redirect('news:home')

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
                user = User.objects.get(telegram_id=telegram_id)
                # Обновляем данные пользователя
                user.username = username
                tg_first_name = telegram_data.get('first_name', '')
                tg_last_name = telegram_data.get('last_name', '')
                if tg_last_name:
                    user.name = f"{tg_first_name} {tg_last_name}".strip()
                else:
                    user.name = tg_first_name
                user.save()
                created = False
            except User.DoesNotExist:
                # Проверяем, существует ли пользователь с таким же именем
                if User.objects.filter(username=username).exists():
                    # Добавляем случайный суффикс к имени пользователя
                    username = f"{username}_{telegram_id[-4:]}"

                # Создаем нового пользователя
                tg_first_name = telegram_data.get('first_name', '')
                tg_last_name = telegram_data.get('last_name', '')
                if tg_last_name:
                    user_name_field = f"{tg_first_name} {tg_last_name}".strip()
                else:
                    user_name_field = tg_first_name
                user = User.objects.create(
                    telegram_id=telegram_id,
                    username=username,
                    name=user_name_field,
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
