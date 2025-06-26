from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Главная страница чата
    path('', views.ChatHomeView.as_view(), name='home'),

    # Общий чат
    path('general/', views.GeneralChatView.as_view(), name='general'),

    # VIP-чат
    path('vip/', views.VIPChatView.as_view(), name='vip'),

    # Приватные чаты
    path('private/', views.PrivateChatsView.as_view(), name='private_chats'),
    path('private/<uuid:thread_id>/', views.PrivateThreadView.as_view(), name='private_thread'),
    path('private/start/<int:user_id>/', views.StartPrivateChatView.as_view(), name='start_private_chat'),

    # Групповые обсуждения
    path('discussions/', views.DiscussionsView.as_view(), name='discussions'),
    path('discussions/create/', views.CreateDiscussionView.as_view(), name='create_discussion'),
    path('discussions/<slug:slug>/', views.DiscussionDetailView.as_view(), name='discussion_detail'),

    # Комнаты (общий доступ)
    path('room/<int:room_id>/', views.RoomView.as_view(), name='room'),

    # AJAX эндпоинты
    path('ajax/send-message/', views.SendMessageAjaxView.as_view(), name='send_message_ajax'),
    path('ajax/mark-read/', views.MarkMessagesReadAjaxView.as_view(), name='mark_read_ajax'),
    path('ajax/load-messages/', views.LoadMessagesAjaxView.as_view(), name='load_messages_ajax'),
]
