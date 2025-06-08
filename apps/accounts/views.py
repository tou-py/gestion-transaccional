from http.client import responses

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework import viewsets, permissions, filters, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, PasswordResetConfirmSerializer, PasswordResetConfirmSerializer, \
    PasswordResetRequestSerializer

User = get_user_model()


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permite acceso al propietario del objeto o a administradores."""

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para operaciones CRUD de usuarios."""

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "date_joined", "first_name", "last_name"]

    def get_permissions(self):
        """Asigna permisos según la acción."""
        if self.action in ["list", "destroy"]:
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ["retrieve", "update", "partial_update"]:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == "create":
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Endpoint para obtener datos del usuario autenticado."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class PasswordRequestView(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def post(request):
        serializer = PasswordResetRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Si el correo existe, recibirás instrucciones para resetear la contraseña.'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Contraseña restablecida correctamente.'},
            status=status.HTTP_200_OK
        )