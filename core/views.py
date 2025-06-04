from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status
from django.db import connection
from django.core.cache import caches
from django.utils import timezone


class APIRootView(APIView):
    """
    Presentación de la API en el endpoint raíz
    """
    authentication_classes = []
    permission_classes = []

    @staticmethod
    def get(request):
        return Response({
            'name': 'Mi API REST',
            'version': '1.0.0',
            'description': 'API profesional construida con Django REST Framework',
            'documentation': request.build_absolute_uri(reverse('redoc')),
            'endpoints': {
                'health_check': request.build_absolute_uri(reverse('health-check')),
                'api_docs': request.build_absolute_uri(reverse('swagger-ui')),
                # Añade aquí otros endpoints importantes
            },
            'timestamp': timezone.now().isoformat(),
            'status': 'operational'
        })

class HealthCheckView(APIView):
    """
    Endpoint de verificación del estado del sistema
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # Verificar estado de la base de datos
        db_status = self.check_database()

        # Verificar estado de la caché (si está configurada)
        cache_status = self.check_cache()

        # Determinar estado general
        overall_status = all([db_status['healthy'], cache_status['healthy']])

        # Preparar respuesta
        response_data = {
            'status': 'OK' if overall_status else 'Degraded',
            'services': {
                'database': db_status,
                'cache': cache_status,
            },
            'timestamp': timezone.now().isoformat()
        }

        # Código HTTP apropiado
        http_status = status.HTTP_200_OK if overall_status else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(response_data, status=http_status)

    @staticmethod
    def check_database():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {'healthy': True, 'detail': 'Connection successful'}
        except Exception as e:
            return {'healthy': False, 'detail': str(e)}

    @staticmethod
    def check_cache():
        try:
            # Intenta con la caché default, si falla prueba con otras
            for cache_name in caches:
                cache = caches[cache_name]
                cache.set('healthcheck', 'test', 1)
                if cache.get('healthcheck') != 'test':
                    raise ValueError(f'Cache test failed for {cache_name}')
            return {'healthy': True, 'detail': 'All caches working'}
        except Exception as e:
            return {'healthy': False, 'detail': str(e)}