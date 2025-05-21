from django.urls import path
from . import views

app_name = "growlogs"
 
urlpatterns = [
    path("", views.growlog_list, name="list"),
    path("create/", views.growlog_create, name="create"),
    path("<int:pk>/", views.growlog_detail, name="detail"),
] 