from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter
from django.urls import path, include

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

# Register viewsets here
# router.register("users", UserViewSet)

app_name = "api"
urlpatterns = router.urls 