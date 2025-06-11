import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, ValidationError
from django.db import models


class Account(models.Model):
    """
    Representa una cuenta o billetera del usuario: ej. efectivo, banco, tarjeta, ahorro, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_account_name'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.user.get_username() or self.user.first_name})"

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        else:
            raise ValidationError({"name": "El nombre no puede estar vacío"})


class Category(models.Model):
    """
    Categorías para clasificar transacciones
    """
    TYPE_CHOICES = [
        ('INGRESO', 'ingreso'),
        ('EGRESO', 'egreso'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_CHOICES[0][0])
    description = models.TextField(blank=True)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        unique_together = [('user', 'name', 'category_type')]
        ordering = ['name', 'category_type']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name', 'category_type'],
                name='unique_category_per_user'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        else:
            raise ValidationError({"name": "El nombre no puede estar vacio"})


class Tag(models.Model):
    """
    Representa etiquetas para categorizar transacciones
    """
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        verbose_name = 'Etiqueta'
        verbose_name_plural = 'Etiquetas'
        unique_together = [('user', 'name')]
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_tag_per_user'
            )
        ]

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        else:
            raise ValidationError({"name": "El nombre no puede estar vacio"})


class Transaction(models.Model):
    """
    Registro de una transacción individual
        - amount: siempre positivo; el efecto, ingreso o gasto, se deriva de la categoría.
        - date: fecha y hora de la transacción, independiente de la hora del registro de la misma.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # relaciones con otras tablas
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='transactions')
    tags = models.ManyToManyField(Tag, related_name='transactions')

    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))],
                                 help_text='El monto debe siempre ser positivo')
    date = models.DateTimeField(help_text='Fecha y hora del registro de la transacción')
    description = models.TextField(blank=True)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-date', '-created_at']

    def __str__(self):
        # Mostramos un resumen de la transacción
        tipo = self.category.get_category_type_display()
        sign = '+' if self.category.category_type == Category.TYPE_CHOICES[0][0] else '-'
        return f"{tipo} {sign} {self.amount} en {self.account.name} el {self.date.date()}"

    def clean(self):
        # Validar que account y category pertenezcan al usuario
        if self.account_id and self.account.user != self.user:
            raise ValidationError({'account': 'La cuenta debe pertenecer al usuario.'})

        if self.category_id and self.category.user != self.user:
            raise ValidationError({'category': 'La categoría debe pertenecer al usuario.'})

        super().clean()

    def save(self, *args, **kwargs):
        # Asegurar las validaciones antes de llamar a save
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_income(self):
        return self.category.category_type == Category.TYPE_CHOICES[0][0]

    @property
    def is_expense(self):
        return self.category.category_type == Category.TYPE_CHOICES[1][0]


class Currency(models.Model):
    """
    Representa una moneda, ej. USD, EUR
    """
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)

    class Meta:
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        if self.code:
            self.code = self.code.strip()
        else:
            raise ValidationError({"code": "El codigo no puede estar vacio"})


class ExchangeRate(models.Model):
    """
    Representa el histórico de la tasa de cambio entre dos monedas
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    base_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='base_rates')
    target_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='target_rates')
    rate = models.DecimalField(max_digits=12, decimal_places=6)
    date = models.DateField()

    class Meta:
        verbose_name = 'Tasa de cambio'
        verbose_name_plural = 'Tasas de cambio'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['base_currency', 'target_currency', 'date'],
                name='unique_exchange_rate_per_date'
            )
        ]

    def __str__(self):
        return f"{self.base_currency.code} - {self.target_currency.code} @ {self.rate} ({self.date})"

    def clean(self):
        if self.base_currency and self.target_currency and self.base_currency.id == self.target_currency.id:
            raise ValidationError("La moneda base y destino deben ser diferentes")


class Budget(models.Model):
    """
    Presupuesto mensual por usuario
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='budgets')
    tag = models.ForeignKey(Tag, null=True, blank=True, on_delete=models.SET_NULL, related_name='budgets')
    month = models.DateField(help_text='Primer dia del mes')
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        unique_together = [('user', 'currency', 'tag', 'month')]
        ordering = ['-month']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'currency', 'tag', 'month'],
                name='unique_budget_month_per_user_currency_tag_month'
            )
        ]

    def __str__(self):
        tag_part = f" Para {self.tag.name}" if self.tag else ""
        return f"{self.user.first_name} - {self.amount} {self.currency.code} en {self.month.strftime('%B %Y')}{tag_part}"

    def clean(self):
        if self.month and self.month.day != 1:
            raise ValidationError({"month": "Debe ser el primer dia del mes"})

        if self.tag and self.tag.user != self.user:
            raise ValidationError({"tag": "La etiqueta debe pertenecer al usuario."})
