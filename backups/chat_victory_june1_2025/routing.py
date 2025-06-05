from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Общий чат
    re_path(r'^general/$', consumers.GeneralChatConsumer.as_asgi()),

    # Приватные чаты
    re_path(r'^private/(?P<thread_id>[0-9a-f-]+)/$', consumers.PrivateChatConsumer.as_asgi()),

    # Групповые обсуждения
    re_path(r'^discussion/(?P<discussion_slug>[\w-]+)/$', consumers.DiscussionChatConsumer.as_asgi()),

    # VIP чат
    re_path(r'^vip/$', consumers.VIPChatConsumer.as_asgi()),
]
