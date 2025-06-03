from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

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
