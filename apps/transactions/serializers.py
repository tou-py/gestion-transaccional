from datetime import date
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Account,
    Category,
    Transaction,
    Currency,
    ExchangeRate,
    Tag,
    Budget,
)

User = get_user_model()


class CurrencySerializer(serializers.ModelSerializer):
    """
    Serializer para Currency.
    Validaciones:
    - code en mayúsculas.
    - code único.
    """

    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol']
        read_only_fields = ['id']

    @staticmethod
    def validate_code(value: str) -> str:
        code = value.strip().upper()
        if not code:
            raise serializers.ValidationError("El código de moneda no puede estar vacío.")
        return code

    def create(self, validated_data: dict[str, Any]) -> Currency:
        # Asegurar código uppercase antes de crear
        validated_data['code'] = validated_data['code'].upper()
        return super().create(validated_data)

    def update(self, instance: Currency, validated_data: dict[str, Any]) -> Currency:
        if 'code' in validated_data:
            validated_data['code'] = validated_data['code'].upper()
        return super().update(instance, validated_data)


class ExchangeRateSerializer(serializers.ModelSerializer):
    """
    Serializer para ExchangeRate.
    Validaciones:
    - base_currency != target_currency
    - rate > 0
    - date no en el futuro
    - unique_together (base, target, date) se maneja en model, aquí chequeamos antes.
    """
    base_currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all()
    )
    target_currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all()
    )

    class Meta:
        model = ExchangeRate
        fields = ['id', 'base_currency', 'target_currency', 'rate', 'date']
        read_only_fields = ['id']

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        base = attrs.get('base_currency')
        target = attrs.get('target_currency')
        rate = attrs.get('rate')
        d = attrs.get('date')

        if base and target and base == target:
            raise serializers.ValidationError("La moneda base y destino deben ser diferentes.")

        if rate is not None:
            # Aceptar Decimal, cast automático de DRF
            if rate <= Decimal('0'):
                raise serializers.ValidationError({"rate": "La tasa debe ser un número positivo."})

        if d:
            today = date.today()
            if d > today:
                raise serializers.ValidationError({"date": "La fecha de la tasa no puede ser futura."})

        # Verificar duplicados previos: si estamos creando nueva instancia (no existe self.instance),
        # o actualizando a valores que colisionan:
        if base and target and d:
            qs = ExchangeRate.objects.filter(
                base_currency=base,
                target_currency=target,
                date=d
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("Ya existe una tasa para estas monedas en esa fecha.")
        return attrs


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer para Tag.
    - name único por usuario.
    """

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

    @staticmethod
    def validate_name(value: str) -> str:
        name = value.strip()
        if not name:
            raise serializers.ValidationError("El nombre de la etiqueta no puede estar vacío.")
        return name

    def create(self, validated_data: dict[str, Any]) -> Tag:
        user = self.context['request'].user
        name = validated_data['name'].strip()
        # Verificar duplicado
        if Tag.objects.filter(user=user, name__iexact=name).exists():
            raise serializers.ValidationError({"name": "Ya existe una etiqueta con ese nombre."})
        return Tag.objects.create(user=user, name=name)

    def update(self, instance: Tag, validated_data: dict[str, Any]) -> Tag:
        user = self.context['request'].user
        if 'name' in validated_data:
            name = validated_data['name'].strip()
            # Verificar duplicado excluyendo la instancia actual
            if Tag.objects.filter(user=user, name__iexact=name).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({"name": "Ya existe una etiqueta con ese nombre."})
            instance.name = name
        instance.save()
        return instance


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer para Account.
    - name único por usuario (se valida en create/update).
    """

    class Meta:
        model = Account
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    @staticmethod
    def validate_name(value: str) -> str:
        name = value.strip()
        if not name:
            raise serializers.ValidationError("El nombre de la cuenta no puede estar vacío.")
        return name

    def create(self, validated_data: dict[str, Any]) -> Account:
        user = self.context['request'].user
        name = validated_data['name'].strip()
        # Verificar duplicado de cuenta para el usuario
        if Account.objects.filter(user=user, name__iexact=name).exists():
            raise serializers.ValidationError({"name": "Ya existe una cuenta con ese nombre."})
        return Account.objects.create(user=user, name=name, description=validated_data.get('description', '').strip())

    def update(self, instance: Account, validated_data: dict[str, Any]) -> Account:
        user = self.context['request'].user
        if 'name' in validated_data:
            name = validated_data['name'].strip()
            if Account.objects.filter(user=user, name__iexact=name).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({"name": "Ya existe una cuenta con ese nombre."})
            instance.name = name
        if 'description' in validated_data:
            instance.description = validated_data['description'].strip()
        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer para Category.
    - name+type únicos por usuario.
    """

    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    @staticmethod
    def validate_name(value: str) -> str:
        name = value.strip()
        if not name:
            raise serializers.ValidationError("El nombre de la categoría no puede estar vacío.")
        return name

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # Validar combinación única name+type por usuario
        user = self.context['request'].user
        name = attrs.get('name', '').strip()
        ctype = attrs.get('type')
        if self.instance:
            # Al actualizar: tomar valores nuevos o los existentes
            name = name if 'name' in attrs else self.instance.name
            ctype = ctype if 'type' in attrs else self.instance.type
            qs = Category.objects.filter(user=user, name__iexact=name, type=ctype).exclude(pk=self.instance.pk)
        else:
            qs = Category.objects.filter(user=user, name__iexact=name, type=ctype)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una categoría con ese nombre y tipo para este usuario.")
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Category:
        user = self.context['request'].user
        name = validated_data['name'].strip()
        return Category.objects.create(
            user=user,
            name=name,
            type=validated_data['type'],
            description=validated_data.get('description', '').strip()
        )

    def update(self, instance: Category, validated_data: dict[str, Any]) -> Category:
        if 'name' in validated_data:
            instance.name = validated_data['name'].strip()
        if 'type' in validated_data:
            instance.type = validated_data['type']
        if 'description' in validated_data:
            instance.description = validated_data['description'].strip()
        instance.save()
        return instance


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer para Transaction.
    - Asigna user desde request.
    - Valida que account y category pertenezcan al mismo usuario.
    - amount siempre positivo (model valida con MinValueValidator).
    - date: puede validarse para no permitir fechas futuras o demasiado antiguas según requisitos.
    - Opcional: manejar tags relacionados o presupuestos fuera de aquí.
    """
    # Podrías exponer también campos anidados opcionales, p.ej. nombre de cuenta o categoría:
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    # Para mostrar datos relacionados se podría usar Serializers anidados o SerializerMethodField, pero aquí
    # nos quedamos con PK y en vistas permiten incluir información adicional si es necesario.

    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'category', 'amount', 'date',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = self.context['request'].user

        # Validar cuenta
        account = attrs.get('account')
        if account.user_id != user.id:
            raise serializers.ValidationError({'account': 'Cuenta inválida o no pertenece al usuario.'})

        # Validar categoría
        category = attrs.get('category')
        if category.user_id != user.id:
            raise serializers.ValidationError({'category': 'Categoría inválida o no pertenece al usuario.'})

        # Validar que category.type coherente? No necesariamente aquí; se supone que la categoría ya define ingreso/gasto.
        # Validar fecha: no futura (opcional)
        tx_date = attrs.get('date')
        if tx_date:
            now = timezone.now()
            if tx_date > now:
                raise serializers.ValidationError({'date': 'La fecha no puede ser futura.'})
            # Opcional: no permitir transacciones muy antiguas, etc.
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Transaction:
        user = self.context['request'].user
        return Transaction.objects.create(user=user, **validated_data)

    def update(self, instance: Transaction, validated_data: dict[str, Any]) -> Transaction:
        # Al actualizar, validar igual: account/category no cambian de usuario
        if 'account' in validated_data:
            account = validated_data['account']
            if account.user_id != self.context['request'].user.id:
                raise serializers.ValidationError({'account': 'Cuenta inválida.'})
            instance.account = account
        if 'category' in validated_data:
            category = validated_data['category']
            if category.user_id != self.context['request'].user.id:
                raise serializers.ValidationError({'category': 'Categoría inválida.'})
            instance.category = category
        if 'amount' in validated_data:
            instance.amount = validated_data['amount']
        if 'date' in validated_data:
            tx_date = validated_data['date']
            now = timezone.now()
            if tx_date > now:
                raise serializers.ValidationError({'date': 'La fecha no puede ser futura.'})
            instance.date = tx_date
        if 'description' in validated_data:
            instance.description = validated_data['description'].strip()
        instance.save()
        return instance


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer para Budget.
    - month debe ser primer día de mes.
    - unique_together se valida aquí: user, currency, tag, month.
    """
    currency = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all())
    tag = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        required=False,
        allow_null=True
    )
    month = serializers.DateField(help_text='Fecha representando el mes, p.ej. 2025-06-01')

    class Meta:
        model = Budget
        fields = ['id', 'currency', 'tag', 'month', 'amount']
        read_only_fields = ['id']

    @staticmethod
    def validate_month(value):
        # Asegurar que el día sea 1 (primer día del mes)
        if value.day != 1:
            raise serializers.ValidationError("El campo 'month' debe contener el primer día del mes (día=1).")
        # Opcional: no permitir meses en el pasado (o permitir solo actual y futuros, según requisitos)
        # if value < date.today().replace(day=1):
        #     raise serializers.ValidationError("No se puede crear presupuesto en un mes pasado.")
        return value

    @staticmethod
    def validate_amount(value):
        if value <= Decimal('0'):
            raise serializers.ValidationError("El monto del presupuesto debe ser positivo.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        currency = attrs.get('currency')
        tag = attrs.get('tag', None)
        month = attrs.get('month')
        # Verificar que la combinación no exista ya
        qs = Budget.objects.filter(user=user, currency=currency, month=month)
        if tag:
            qs = qs.filter(tag=tag)
        else:
            qs = qs.filter(tag__isnull=True)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un presupuesto para este usuario, moneda, mes y etiqueta.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return Budget.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        # Solo se permiten cambiar currency, tag, month, amount con mismas validaciones previas
        if 'currency' in validated_data:
            instance.currency = validated_data['currency']
        if 'tag' in validated_data:
            instance.tag = validated_data['tag']
        if 'month' in validated_data:
            instance.month = validated_data['month']
        if 'amount' in validated_data:
            instance.amount = validated_data['amount']
        # Revalidar unique_together
        # Podemos reutilizar validate:
        # Pero aquí, después de asignar, chequeamos duplicados:
        user = self.context['request'].user
        qs = Budget.objects.filter(user=user, currency=instance.currency, month=instance.month)
        if instance.tag:
            qs = qs.filter(tag=instance.tag)
        else:
            qs = qs.filter(tag__isnull=True)
        qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un presupuesto para esta combinación.")
        instance.save()
        return instance
