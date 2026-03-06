from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _client_module_choices():
    return [
        ("dashboard", "Client Dashboard"),
        ("my_calls", "My Calls"),
        ("reports", "Reports"),
        ("tasks", "Tasks"),
        ("support", "Support"),
    ]


class ClientModulesValidationMixin:
    enabled_modules = serializers.ListField(
        child=serializers.ChoiceField(choices=_client_module_choices()),
        required=False,
        allow_empty=False,
    )

    def validate_enabled_modules(self, value):
        unique_modules = []
        for module in value:
            if module not in unique_modules:
                unique_modules.append(module)

        if not unique_modules:
            raise serializers.ValidationError("At least one module is required.")

        return unique_modules


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Identifiants invalides.")
        if not user.is_active:
            raise serializers.ValidationError("Compte desactive.")

        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["leacall_tenancy_url"] = user.leacall_tenancy_url
        refresh["enabled_modules"] = user.enabled_modules

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role,
            "leacall_tenancy_url": user.leacall_tenancy_url,
            "enabled_modules": user.enabled_modules,
        }


class ClientCreateSerializer(ClientModulesValidationMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "leacall_tenancy_url", "enabled_modules"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.CLIENT, **validated_data)
        user.set_password(password)
        user.save()
        return user


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "leacall_tenancy_url", "enabled_modules", "is_active", "date_joined"]
        read_only_fields = fields


class ClientUpdateSerializer(ClientModulesValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "leacall_tenancy_url", "enabled_modules", "is_active"]


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active"]
        read_only_fields = fields
