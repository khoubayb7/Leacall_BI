from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import IsAdmin, IsClient
from .serializers import AdminSerializer, ClientCreateSerializer, ClientSerializer

User = get_user_model()


class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["leacall_tenancy_url"] = user.leacall_tenancy_url
        return token


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        print("Login attempt for username:", request.data.get("username"))
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response

        username = request.data.get("username")
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return response

        user_data = AdminSerializer(user).data if user.role == User.Role.ADMIN else ClientSerializer(user).data
        response.data["user"] = user_data
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Deconnexion reussie."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Token invalide ou expire."}, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == User.Role.ADMIN:
            return Response(AdminSerializer(request.user).data)
        return Response(ClientSerializer(request.user).data)


class ClientListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        clients = User.objects.filter(role=User.Role.CLIENT).order_by("-date_joined")
        return Response(ClientSerializer(clients, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ClientCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        client = serializer.save()
        return Response(ClientSerializer(client).data, status=status.HTTP_201_CREATED)


class ClientDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def _get_client(self, pk):
        try:
            return User.objects.get(pk=pk, role=User.Role.CLIENT)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        client = self._get_client(pk)
        if not client:
            return Response({"error": "Client introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClientSerializer(client).data)

    def put(self, request, pk):
        client = self._get_client(pk)
        if not client:
            return Response({"error": "Client introuvable."}, status=status.HTTP_404_NOT_FOUND)

        editable_fields = ["email", "leacall_tenancy_url", "is_active"]
        for field in editable_fields:
            if field in request.data:
                setattr(client, field, request.data[field])
        client.save()

        return Response(ClientSerializer(client).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        client = self._get_client(pk)
        if not client:
            return Response({"error": "Client introuvable."}, status=status.HTTP_404_NOT_FOUND)

        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientPlatformView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        return Response(ClientSerializer(request.user).data, status=status.HTTP_200_OK)
