from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.views import AuthorizationView
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, HttpResponse
from oauth2_provider.models import Application
import urllib.parse
import logging

logger = logging.getLogger(__name__)


class RocketChatAuthorizationView(AuthorizationView):
    """
    Кастомный OAuth authorization view для Rocket.Chat
    Автоматически одобряет запросы для уже авторизованных пользователей
    """

    def get(self, request, *args, **kwargs):
        """
        Обрабатываем GET запрос авторизации
        """
        # Если пользователь не авторизован, редиректим на логин
        if not request.user.is_authenticated:
            login_url = reverse('account_login')
            current_url = request.get_full_path()
            return redirect(f"{login_url}?next={urllib.parse.quote(current_url)}")

        # Получаем параметры OAuth
        client_id = request.GET.get('client_id')

        # Проверяем, что это наше Rocket.Chat приложение
        try:
            app = Application.objects.get(client_id=client_id)
            if app.name == 'Rocket.Chat SSO' or client_id == 'BesedkaRocketChat2025':
                # Автоматически одобряем для Rocket.Chat
                # Создаем копию GET параметров как POST для автоматического одобрения
                request.POST = request.GET.copy()
                request.POST['allow'] = 'Authorize'
                request.method = 'POST'

                # Вызываем POST обработчик родительского класса
                return self.post(request, *args, **kwargs)
        except Application.DoesNotExist:
            logger.warning(f"OAuth application not found: {client_id}")

        # Для других приложений показываем стандартную форму
        return super().get(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        """
        Обрабатываем POST запрос с отключенной CSRF проверкой
        """
        return super().post(request, *args, **kwargs)
