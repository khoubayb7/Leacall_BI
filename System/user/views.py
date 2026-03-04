from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ClientCreateSerializer,
    ClientSerializer,
    AdminSerializer,
)
from .permissions import IsAdmin, IsClient

User = get_user_model()


class CustomTokenSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Ajouter des données personnalisées dans le JWT
        token["role"] = user.role
        token["leacall_tenancy_url"] = user.leacall_tenancy_url

        return token


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body :
    {
        "username": "...",
        "password": "..."
    }

    Réponse :
    {
        "refresh": "...",
        "access": "...",
        "user": { ... }
    }
    """
    permission_classes = [AllowAny]
    serializer_class = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # Récupération de l'utilisateur
        user = User.objects.get(username=request.data.get("username"))

        user_data = (
            AdminSerializer(user).data
            if user.role == User.Role.ADMIN
            else ClientSerializer(user).data
        )

        response.data["user"] = user_data
        return response

class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Body :
    {
        "refresh": "..."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Déconnexion réussie."},
                status=status.HTTP_205_RESET_CONTENT,
            )

        except Exception:
            return Response(
                {"error": "Token invalide ou expiré."},
                status=status.HTTP_400_BAD_REQUEST,
            )

class MeView(APIView):
    """
    GET /api/auth/me/
    Authorization: Bearer <access_token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == User.Role.ADMIN:
            return Response(AdminSerializer(request.user).data)

        return Response(ClientSerializer(request.user).data)


class ClientListCreateView(APIView):
    """
    GET  /api/admin/clients/
    POST /api/admin/clients/
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        clients = User.objects.filter(
            role=User.Role.CLIENT
        ).order_by("-date_joined")

        return Response(
            ClientSerializer(clients, many=True).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = ClientCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = serializer.save()

        return Response(
            ClientSerializer(client).data,
            status=status.HTTP_201_CREATED,
        )


class ClientDetailView(APIView):
    """
    GET    /api/admin/clients/<pk>/
    PUT    /api/admin/clients/<pk>/
    DELETE /api/admin/clients/<pk>/
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def _get_client(self, pk):
        try:
            return User.objects.get(pk=pk, role=User.Role.CLIENT)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        client = self._get_client(pk)

        if not client:
            return Response(
                {"error": "Client introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ClientSerializer(client).data)

    def put(self, request, pk):
        client = self._get_client(pk)

        if not client:
            return Response(
                {"error": "Client introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        editable_fields = ["email", "leacall_tenancy_url", "is_active"]

        for field in editable_fields:
            if field in request.data:
                setattr(client, field, request.data[field])

        client.save()

        return Response(
            ClientSerializer(client).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        client = self._get_client(pk)

        if not client:
            return Response(
                {"error": "Client introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        client.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientPlatformView(APIView):
    """
    GET /api/client/platform/
    Authorization: Bearer <access_token>
    """
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        return Response(
            ClientSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )