from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("telegram-login/", views.telegram_login, name="telegram_login"),
] 