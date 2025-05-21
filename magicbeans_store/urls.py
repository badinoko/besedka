from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("strain/<int:pk>/", views.strain_detail, name="strain_detail"),
] 