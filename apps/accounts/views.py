from typing import Any, List

from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer, PasswordResetConfirmSerializer, \
    PasswordResetRequestSerializer

User = get_user_model()


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado que permite acceso al propietario del objeto o a administradores.

    Aplicación del principio de responsabilidad única (SRP) - una clase, un propósito.
    """

    def has_object_permission(self, request: Request, view: Any, obj: User) -> bool:
        """
         Verificar si el usuario tiene permiso para acceder al objeto.
        Args:
            request: Solicitud HTTP
            view: Vista que maneja la solicitud
            obj: Objeto User a verificar
        Returns:
            True si tiene permiso, False caso contrario
        """
        return obj == request.user or request.user.is_staff


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operaciones CRUD completas de usuarios.

    Proporciona endpoints para:
    - Listar usuarios (solo admin)
    - Crear usuario (público)
    - Obtener usuario específico (propietario o admin)
    - Actualizar usuario (propietario o admin)
    - Eliminar usuario (solo admin)
    - Obtener datos del usuario autenticado (/me)
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "date_joined", "first_name", "last_name"]

    def get_permissions(self) -> List[permissions.BasePermission]:
        """
        Asignar permisos dinámicamente según la acción.

        Returns:
            Lista de instancias de permisos
        """
        permission_map = {
            'list': [permissions.IsAuthenticated],
            'destroy': [permissions.IsAdminUser],
            'retrieve': [permissions.IsAuthenticated, IsOwnerOrAdmin],
            'update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
            'partial_update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
            'create': [permissions.AllowAny],

        }

        permission_classes = permission_map.get(
            self.action, [permissions.IsAuthenticated]
        )

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Endpoint para obtener datos del usuario autenticado.

        Args:
            request: Solicitud HTTP

        Returns:
            Datos del usuario autenticado
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordRequestView(APIView):
    """
    Vista para solicitar restablecimiento de contraseña.

    Acepta un email y envía instrucciones de reset si el usuario existe.
    Por seguridad, siempre retorna el mismo mensaje sin revelar si el email existe.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @staticmethod
    def post(request: Request) -> Response:
        """
        Procesar solicitud de restablecimiento de contraseña.

        Args:
            request: Solicitud HTTP con email

        Returns:
            Mensaje de confirmación genérico
        """
        serializer = PasswordResetRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Si el correo existe, recibirás instrucciones para resetear la contraseña.'},
                        status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Vista para confirmar restablecimiento de contraseña.

    Acepta UID, token y nueva contraseña para completar el proceso de reset.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @staticmethod
    def post(request: Request) -> Response:
        """
        Procesar confirmación de restablecimiento de contraseña.

        Args:
            request: Solicitud HTTP con UID, token y nueva contraseña

        Returns:
            Mensaje de confirmación de éxito
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'detail': 'Contraseña restablecida correctamente.'},
            status=status.HTTP_200_OK
        )
