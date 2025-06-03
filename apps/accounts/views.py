from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import UserSerializer

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
