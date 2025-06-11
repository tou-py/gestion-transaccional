from typing import Any, Optional, Dict, TypeVar

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Model
from rest_framework import serializers

from .models import Account, Category, Transaction, Tag, Budget, ExchangeRate

User = get_user_model()

T = TypeVar("T", bound=Model)


class BaseService:
    @staticmethod
    def _save_instance(instance: T, data: Dict[str, Any], uniqueness_error: Dict | str):
        """
        Asigna atributos, valida y guarda
        uniqueness_error puede ser un diccionario para field-errors o str para non_field
        """
        for field, value in data.items():
            setattr(instance, field, value)
        try:
            instance.full_clean()
            instance.save()
            return instance
        except IntegrityError:
            raise serializers.ValidationError(uniqueness_error)


class AccountService(BaseService):
    @staticmethod
    def create_account(user: User, validated_data: Dict[str, Any]) -> Optional[Account]:
        try:
            return Account.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'non_field_errors': 'Ya existe una cuenta con ese nombre.'})

    @staticmethod
    def update_account(instance: Account, validated_data: Dict[str, Any]) -> Optional[Account]:
        return BaseService._save_instance(instance, validated_data,
                                          {'non_field_errors': "Ya existe una cuenta con ese nombre"})


class CategoryService(BaseService):
    @staticmethod
    def create_category(user: User, validated_data: Dict[str, Any]) -> Optional[Category]:
        try:
            return Category.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'non_field_errors': 'Ya existe una categoría con ese nombre y tipo.'})

    @staticmethod
    def update_category(instance: Category, validated_data: Dict[str, Any]) -> Optional[Category]:
        return BaseService._save_instance(instance, validated_data,
                                          {'non_field_errors': "Ya existe una categoria con ese nombre y tipo"})


class TagService(BaseService):
    @staticmethod
    def create_tag(user: User, validated_data: Dict[str, Any]) -> Optional[Tag]:
        try:
            return Tag.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'non_field_errors': 'Ya existe una etiqueta con ese nombre.'})

    @staticmethod
    def update_tag(instance, validated_data):
        return BaseService._save_instance(instance, validated_data,
                                          {'non_field_errors': "Ya existe una etiqueta con ese nombre"})


class ExchangeRateService(BaseService):
    @staticmethod
    def create_exchange_rate(validated_data: Dict[str, Any]) -> Optional[ExchangeRate]:
        try:
            return ExchangeRate.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError('Ya existe una tasa para estas monedas en esa fecha.')

    @staticmethod
    def update_exchange_rate(instance, validated_data):
        return BaseService._save_instance(instance, validated_data,
                                          {'non_field_errors': "Ya existe una tasa para estas monedas en esa fecha"})


class TransactionService(BaseService):
    @staticmethod
    def create_transaction(user: User, validated_data: Dict[str, Any]) -> Optional[Transaction]:
        tags_data = validated_data.pop('tags', [])
        with transaction.atomic():
            tx = Transaction.objects.create(user=user, **validated_data)
            if tags_data:
                tx.tags.add(*tags_data)
        return tx

    @staticmethod
    def update_transaction(instance, validated_data: Dict[str, Any]) -> Optional[Transaction]:
        tags_data = validated_data.pop('tags', None)
        with transaction.atomic():
            # usa el helper genérico para campos simples
            tx = BaseService._save_instance(
                instance, validated_data,
                'Error al actualizar la transacción.'
            )
            if tags_data is not None:
                tx.tags.set(tags_data)
        return tx


class BudgetService(BaseService):
    @staticmethod
    def create_budget(user: User, validated_data: Dict[str, Any]) -> Optional[Budget]:
        try:
            return Budget.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError('Ya existe un presupuesto para esta combinación.')

    @staticmethod
    def update_budget(instance: Budget, validated_data: Dict[str, Any]) -> Optional[Budget]:
        return BaseService._save_instance(
            instance,
            validated_data,
            {"non_field_errors": "Ya existe un presupuesto con esa combinación"}
        )
