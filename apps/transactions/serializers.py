from datetime import date
from decimal import Decimal
from typing import Any, Optional, Dict

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
from .services import ExchangeRateService, TagService, AccountService, CategoryService, TransactionService, \
    BudgetService

User = get_user_model()


class CurrencySerializer(serializers.ModelSerializer):
    """
    Serializer para Currency.
    """

    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol']
        read_only_fields = ['id']

    @staticmethod
    def validate_code(value: str) -> str:
        return value.strip().upper()


class ExchangeRateSerializer(serializers.ModelSerializer):
    """
    Serializer para ExchangeRate.
    """

    class Meta:
        model = ExchangeRate
        fields = ['id', 'base_currency', 'target_currency', 'rate', 'date']
        read_only_fields = ['id']

    @staticmethod
    def validate_date(value: date) -> Optional[date]:
        if value > date.today():
            raise serializers.ValidationError('La fecha no puede ser futura')
        return value

    def create(self, validated_data: Dict[str, Any]) -> Optional[ExchangeRate]:
        return ExchangeRateService.create_exchange_rate(validated_data)

    def update(self, instance: ExchangeRate, validated_data: Dict[str, Any]) -> Optional[ExchangeRate]:
        return ExchangeRateService.update_exchange_rate(instance, validated_data)


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer para Tag.
    """

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

    def create(self, validated_data: Dict[str, Any]) -> Optional[Tag]:
        user = self.context['request'].user
        return TagService.create_tag(user, validated_data)

    def update(self, instance: Tag, validated_data: Dict[str, Any]) -> Optional[Tag]:
        return TagService.update_tag(instance, validated_data)


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer para Account.
    """

    class Meta:
        model = Account
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data: Dict[str, Any]) -> Optional[Account]:
        user = self.context['request'].user
        return AccountService.create_account(user, validated_data)

    def update(self, instance: Account, validated_data: Dict[str, Any]) -> Optional[Account]:
        return AccountService.update_account(instance, validated_data)


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer para Category.
    """

    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data: Dict[str, Any]) -> Optional[Category]:
        user = self.context['request'].user
        return CategoryService.create_category(user, validated_data)

    def update(self, instance: Category, validated_data: Dict[str, Any]) -> Optional[Category]:
        return CategoryService.update_category(instance, validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer para Transaction.
    """
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'category', 'amount', 'date',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            if user.is_authenticated:
                self.fields['tags'].queryset = Tag.objects.filter(user=user)
                self.fields['account'].queryset = Account.objects.filter(user=user)
                self.fields['category'].queryset = Category.objects.filter(user=user)

    @staticmethod
    def validate_date(value: date) -> Optional[date]:
        if value > timezone.now():
            raise serializers.ValidationError('La fecha no puede ser futura')
        return value

    def create(self, validated_data: Dict[str, Any]) -> Optional[Transaction]:
        user = self.context['request'].user
        return TransactionService.create_transaction(user, validated_data)

    def update(self, instance: Transaction, validated_data: Dict[str, Any]) -> Optional[Transaction]:
        return TransactionService.update_transaction(instance, validated_data)


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer para Budget.
    """

    class Meta:
        model = Budget
        fields = ['id', 'currency', 'tags', 'month', 'amount']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            if user.is_authenticated:
                self.fields['tags'].queryset = Tag.objects.filter(user=user)

    @staticmethod
    def validate_month(value):
        if value.day != 1:
            raise serializers.ValidationError('Debe ser el primer dia del mes')
        return value

    @staticmethod
    def validate_amount(value: Decimal) -> Optional[Decimal]:
        if value < Decimal('0'):
            raise serializers.ValidationError('La cantidad debe ser un numero positivo')
        return value

    def create(self, validated_data: Dict[str, Any]) -> Optional[Budget]:
        user = self.context['request'].user
        return BudgetService.create_budget(user, validated_data)

    def update(self, instance, validated_data: Dict[str, Any]) -> Optional[Budget]:
        return BudgetService.update_budget(instance, validated_data)
