from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import HealthCheckView, APIRootView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Ruta de presentación de la API
    path('', APIRootView.as_view(), name='api-root'),
    # Ruta para verificar el estado de la API
    path('health/', HealthCheckView.as_view(), name='health-check'),
    # Rutas de cuentas de usuario
    path('', include('apps.accounts.urls'), name='accounts'),
    # Rutas de autenticación y tokens JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Rutas para documentación
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # UI opcional
    path('api/schema/swagger-ui', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
