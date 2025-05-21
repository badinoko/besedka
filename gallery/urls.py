from django.urls import path
from . import views

app_name = "gallery"

urlpatterns = [
    path("", views.photo_list, name="list"),
    path("upload/", views.photo_upload, name="upload"),
    path("<int:pk>/", views.photo_detail, name="detail"),
] 