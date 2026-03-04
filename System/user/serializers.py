from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.permissions import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


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
            raise serializers.ValidationError("Compte désactivé.")

        refresh = RefreshToken.for_user(user)

        # Ajout d'informations personnalisées
        refresh["role"] = user.role
        refresh["leacall_tenancy_url"] = user.leacall_tenancy_url

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role,
            "leacall_tenancy_url": user.leacall_tenancy_url,
        }


class ClientCreateSerializer(serializers.ModelSerializer):
    """
    Utilisé par l'admin pour créer un client.
    Champs requis : username, email, password, leacall_tenancy_url
    """
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'password', 'leacall_tenancy_url']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(role='client', **validated_data)
        user.set_password(password)
        user.save()
        return user


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'role', 'leacall_tenancy_url', 'is_active', 'date_joined']
        read_only_fields = fields


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'role', 'is_active']
        read_only_fields = fields
