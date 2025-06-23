"""
API Router для проекта Беседка
"""

from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from chat.views import RocketChatOAuthTokenView, RocketChatOAuthUserView

urlpatterns = [
    # API документация
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # OAuth API для Rocket.Chat интеграции
    path('v1/auth/rocket/', RocketChatOAuthTokenView.as_view(), name='rocketchat_oauth_token'),
    path('v1/auth/rocket/user/', RocketChatOAuthUserView.as_view(), name='rocketchat_oauth_user'),

    # API endpoints
    path('', include('api.urls')),
]
