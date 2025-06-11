from typing import Any, Optional, Dict

from django.conf import settings
from django.db import IntegrityError
from rest_framework import serializers

from .models import Account, Category, Transaction, Tag, Budget, ExchangeRate


class AccountService:
    @staticmethod
    def create_account(user: settings.AUTH_USER_MODEL, validated_data: Dict[str, Any]) -> Optional[Account]:
        try:
            return Account.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'name': 'Ya existe una cuenta con ese nombre.'})

    @staticmethod
    def update_account(instance: Account, validated_data: Dict[str, Any]) -> Optional[Account]:
        try:
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.full_clean()
            instance.save()
            return instance
        except IntegrityError:
            raise serializers.ValidationError({'name': 'Ya existe una cuenta con ese nombre.'})


class CategoryService:
    @staticmethod
    def create_category(user: settings.AUTH_USER_MODEL, validated_data: Dict[str, Any]) -> Optional[Category]:
        try:
            return Category.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'name': 'Ya existe una categoría con ese nombre y tipo.'})

    @staticmethod
    def update_category(instance: Category, validated_data: Dict[str, Any]) -> Optional[Category]:
        try:
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.full_clean()
            instance.save()
            return instance
        except IntegrityError:
            raise serializers.ValidationError({'name': 'Ya existe una categoría con ese nombre y tipo.'})


class TagService:
    @staticmethod
    def create_tag(user: settings.AUTH_USER_MODEL, validated_data: Dict[str, Any]) -> Optional[Tag]:
        try:
            return Tag.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'name': 'Ya existe una etiqueta con ese nombre.'})

    @staticmethod
    def update_tag(instance, validated_data):
        try:
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.full_clean()
            instance.save()
            return instance
        except IntegrityError:
            raise serializers.ValidationError({'name': 'Ya existe una etiqueta con ese nombre.'})


class ExchangeRateService:
    @staticmethod
    def create_exchange_rate(validated_data: Dict[str, Any]) -> Optional[ExchangeRate]:
        try:
            return ExchangeRate.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError('Ya existe una tasa para estas monedas en esa fecha.')

    @staticmethod
    def update_exchange_rate(instance, validated_data):
        try:
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.full_clean()
            instance.save()
            return instance
        except IntegrityError:
            raise serializers.ValidationError('Ya existe una tasa para estas monedas en esa fecha.')


class TransactionService:
    @staticmethod
    def create_transaction(user: settings.AUTH_USER_MODEL, validated_data: Dict[str, Any]) -> Optional[Transaction]:
        # Extraer tags para manejarlos después de crear la transacción
        tags_data = validated_data.pop('tags', [])

        transaction = Transaction.objects.create(user=user, **validated_data)

        # Asignar tags si existen
        if tags_data:
            for tag in tags_data:
                transaction.tags.add(tag)

        return transaction

    @staticmethod
    def update_transaction(instance: Transaction, validated_data: Dict[str, Any]) -> Optional[Transaction]:
        tags_data = validated_data.pop('tags', None)

        # Actualizar campos básicos
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.full_clean()
        instance.save()

        # Actualizar tags si se proporcionaron
        if tags_data is not None:
            instance.tags.set(tags_data)

        return instance


class BudgetService:
    @staticmethod
    def create_budget(user: settings.AUTH_USER_MODEL, validated_data: Dict[str, Any]) -> Optional[Budget]:
        try:
            return Budget.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError('Ya existe un presupuesto para esta combinación.')

    @staticmethod
    def update_budget(instance: Budget, validated_data: Dict[str, Any]) -> Optional[Budget]:
        try:
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.full_clean()
            instance.save()
            return instance
        except IntegrityError:
            raise serializers.ValidationError('Ya existe un presupuesto para esta combinación.')
