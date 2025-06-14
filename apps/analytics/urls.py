from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AnalyticsViewSet

router = DefaultRouter()
router.register(f'analytics'
                f'', AnalyticsViewSet, basename='analytics')
urlpatterns = [
    path('api/', include(router.urls)),
]
