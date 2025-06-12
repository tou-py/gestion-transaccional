from rest_framework import viewsets, permissions

from .models import (
    Account, Category, Tag,
    Transaction, Budget,
    Currency, ExchangeRate
)
from .serializers import (
    AccountSerializer, CategorySerializer, TagSerializer,
    TransactionSerializer, BudgetSerializer,
    CurrencySerializer, ExchangeRateSerializer
)


class IsOwnerMixin:
    """
    Mixin para filtrar el queryset por el usuario autenticado.
    Solo para aquellos modelos que tengan FK user.
    """

    def get_queryset(self):
        # espera que el modelo tenga related_name 'accounts', 'categories', etc.
        return self.request.user.__getattribute__(self.basename + 's').all()


class AccountViewSet(IsOwnerMixin, viewsets.ModelViewSet):
    """
    CRUD de cuentas del usuario.
    """
    queryset = Account.objects.none()  # se ignora en favor de get_queryset()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]


class CategoryViewSet(IsOwnerMixin, viewsets.ModelViewSet):
    """
    CRUD de categorías del usuario.
    """
    queryset = Category.objects.none()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TagViewSet(IsOwnerMixin, viewsets.ModelViewSet):
    """
    CRUD de etiquetas del usuario.
    """
    queryset = Tag.objects.none()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]


class TransactionViewSet(IsOwnerMixin, viewsets.ModelViewSet):
    """
    CRUD de transacciones del usuario.
    """
    queryset = Transaction.objects.none()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]


class BudgetViewSet(IsOwnerMixin, viewsets.ModelViewSet):
    """
    CRUD de presupuestos del usuario.
    """
    queryset = Budget.objects.none()
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]


class CurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Listado y detalle de monedas.
    """
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]


class ExchangeRateViewSet(viewsets.ModelViewSet):
    """
    CRUD de tasas de cambio.
    """
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated]
