from django.contrib.auth.views import PasswordResetDoneView
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .serializers import PasswordResetConfirmSerializer
from .views import UserViewSet, PasswordRequestView, PasswordResetConfirmView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')


urlpatterns = [
    path("api/", include(router.urls)),
    path("api/password/reset/", PasswordRequestView.as_view(), name="password_reset"),
    path("api/password/reset/done/", PasswordResetConfirmView.as_view(), name="password_reset_done"),
]