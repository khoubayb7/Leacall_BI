from django.contrib.auth import authenticate, get_user_model

from rest_framework.views        import APIView
from rest_framework.response     import Response
from rest_framework.permissions  import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status

from .serializers import (
    LoginSerializer,
    ClientCreateSerializer,
    ClientSerializer,
    AdminSerializer,
)
from .permissions import IsAdminTenancy, IsClientTenancy

User = get_user_model()


# ═══════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════

class LoginView(APIView):
    """
    POST /api/auth/login/
    Body : { "username": "...", "password": "..." }

    Réponse admin  : { token, user: { role: "admin", ... } }
    Réponse client : { token, user: { role: "client", leacall_tenancy_url: "...", ... } }

    Le frontend lit `role` et `leacall_tenancy_url` pour savoir où envoyer l'utilisateur.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )

        if user is None:
            return Response(
                {'error': "Nom d'utilisateur ou mot de passe incorrect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'error': "Ce compte est désactivé."},
                status=status.HTTP_403_FORBIDDEN,
            )

        token, _ = Token.objects.get_or_create(user=user)

        user_data = AdminSerializer(user).data if user.role == 'admin' else ClientSerializer(user).data

        return Response({
            'token': token.key,
            'user':  user_data,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Authorization: Token <token>
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'message': "Token révoqué."}, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    GET /api/auth/me/
    Authorization: Token <token>
    Retourne les infos de l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin':
            return Response(AdminSerializer(request.user).data)
        return Response(ClientSerializer(request.user).data)


# ═══════════════════════════════════════════
#  ADMIN — gestion des clients
# ═══════════════════════════════════════════

class ClientListCreateView(APIView):
    """
    GET  /api/admin/clients/
         → liste de tous les clients

    POST /api/admin/clients/
         → crée un nouveau client
         Body :
         {
             "username":            "dupont",
             "email":               "dupont@example.com",
             "password":            "secret123",
             "leacall_tenancy_url": "https://dupont.leacall.com"
         }
    """
    permission_classes = [IsAuthenticated, IsAdminTenancy]

    def get(self, request):
        clients = User.objects.filter(role='client').order_by('-date_joined')
        return Response(ClientSerializer(clients, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ClientCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        client = serializer.save()

        return Response(
            ClientSerializer(client).data,
            status=status.HTTP_201_CREATED,
        )


class ClientDetailView(APIView):
    """
    GET    /api/admin/clients/<pk>/   → détail d'un client
    PUT    /api/admin/clients/<pk>/   → mise à jour (email, leacall_tenancy_url, is_active)
    DELETE /api/admin/clients/<pk>/   → suppression
    """
    permission_classes = [IsAuthenticated, IsAdminTenancy]

    def _get_client(self, pk):
        try:
            return User.objects.get(pk=pk, role='client')
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        client = self._get_client(pk)
        if not client:
            return Response({'error': 'Client introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClientSerializer(client).data)

    def put(self, request, pk):
        client = self._get_client(pk)
        if not client:
            return Response({'error': 'Client introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        editable = ['email', 'leacall_tenancy_url', 'is_active']
        for field in editable:
            if field in request.data:
                setattr(client, field, request.data[field])
        client.save()

        return Response(ClientSerializer(client).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        client = self._get_client(pk)
        if not client:
            return Response({'error': 'Client introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════
#  CLIENT — son propre espace
# ═══════════════════════════════════════════

class ClientPlatformView(APIView):
    """
    GET /api/client/platform/
    Authorization: Token <token>

    Retourne les données du client connecté, incluant son leacall_tenancy_url.
    Le frontend utilise cette URL pour construire son interface.
    """
    permission_classes = [IsAuthenticated, IsClientTenancy]

    def get(self, request):
        return Response(ClientSerializer(request.user).data, status=status.HTTP_200_OK)