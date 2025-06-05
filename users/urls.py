from django.urls import path
from . import views
from . import admin_views
from .views_owner_platform import ManageStoreOwnerView

app_name = "users"

urlpatterns = [
    # Старые маршруты
    path("profile/", views.profile, name="profile_old"),  # Временно сохраняем
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("telegram-login/", views.telegram_login, name="telegram_login"),
    path("unban-request/", views.unban_request_view, name="unban_request"),

    # НОВАЯ СИСТЕМА ЛИЧНЫХ КАБИНЕТОВ
    path("cabinet/", views.profile_view, name="profile"),  # Главная ЛК
    path("cabinet/edit/", views.edit_profile_view, name="edit_profile"),  # Редактирование профиля
    path("cabinet/password/", views.change_password_view, name="change_password"),  # Смена пароля
    path("cabinet/notifications/", views.notification_list_view, name="notification_list"), # Список уведомлений
    path("cabinet/notifications/<int:notification_id>/mark-read/", views.mark_notification_read, name="mark_notification_read"), # Пометить как прочитанное
    path("cabinet/notifications/read-all/", views.mark_all_notifications_read, name="mark_all_notifications_read"), # Пометить все как прочитанные
    path("cabinet/notifications/read-multiple/", views.mark_multiple_notifications_read, name="mark_multiple_notifications_read"), # Пометить выбранные как прочитанные
    path("cabinet/notifications/delete-multiple/", views.delete_multiple_notifications, name="delete_multiple_notifications"), # Удалить выбранные
    path("cabinet/notifications/delete/<int:notification_id>/", views.delete_notification, name="delete_notification"), # Удалить отдельное
    path("cabinet/admins/", views.manage_admins_view, name="manage_admins"),  # Управление админами
    path("manage-admins/", views.manage_admins_view, name="manage_admins_alias"),  # Альтернативный URL
    path("cabinet/role/<int:user_id>/", views.change_user_role_view, name="change_role"),  # Изменение роли

    # Детали пользователей
    path("<str:username>/", views.user_detail_view, name="detail"),
    path("", views.user_redirect_view, name="redirect"),

    # Маршрут для управления владельцами магазина
    path("owner/manage-store-owners/", admin_views.StoreOwnerManagementView.as_view(), name="store_owner_management"),
    path(
        "owner-platform/manage-store-owner/",
        ManageStoreOwnerView.as_view(),
        name="manage_store_owner",
    ),
]
