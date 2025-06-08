from typing import Any
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.http import HttpRequest
from django.contrib.auth.forms import PasswordResetForm
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer para operaciones CRUD de usuarios."""

    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "password",
            "password_confirm", "is_active", "is_staff", "date_joined"
        ]
        read_only_fields = ["id", "date_joined"]
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True}
        }

    def validate_email(self, value):
        """Validar email único."""
        email = value.lower()
        if self.instance:
            if self.instance.email.lower() == email:
                return email
            if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("Ya existe un usuario con ese correo.")
        else:
            if User.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError("Ya existe un usuario con ese correo.")
        return email

    def validate(self, attrs):
        """Validar contraseñas si se proporcionan."""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if self.instance is None and not password:
            raise serializers.ValidationError({'password': 'Este campo es obligatorio.'})

        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
            validate_password(password)

        attrs.pop('password_confirm', None)
        return attrs

    def create(self, validated_data):
        """Crear usuario con contraseña encriptada."""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        """Actualizar usuario, incluyendo contraseña si se proporciona."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    @staticmethod
    def validate_email(value: str) -> str:
        return value.lower()

    def save(self)->dict:
        request: HttpRequest = self.context['request']
        form = PasswordResetForm(data=self.validated_data)
        if form.is_valid():
            form.save(
                subject_template_name='registration/password_reset_subject.txt',
                email_template_name='registration/password_reset_email.html',
                use_https=request.is_secure(),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                request=request,
                token_generator=default_token_generator,
                html_email_template_name='registration/password_reset_email.html'
            )
        return {}


class PasswordResetConfirmSerializer(serializers.Serializer):
    def __init__(self, instance=None, data=None):
        super().__init__(instance, data)
        self.user = None

    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, required=False)


    @staticmethod
    def validate_new_password(value: str):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value

    def validate(self, attrs: dict[Any, Any]) -> dict:
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uidb64": "UID Invalido"})

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError({"uidb64": "UID Invalido"})

        return attrs

    def save(self)->dict:
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()
        return self.user