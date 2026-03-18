from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.permissions import IsAdmin, IsClient

from .executor import ETLPipelineExecutor
from .models import CampaignRecord, ClientDataSource, ETLRun
from .serializers import (
    CampaignRecordSerializer,
    ClientDataSourceSerializer,
    ETLRunSerializer,
    ETLRunSyncTriggerSerializer,
)

User = get_user_model()


# ── Data Sources (admin manages, clients can view their own) ──────────────────


class DataSourceListCreateView(APIView):
    """Admin: list all / create.  Client: list own sources."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == "admin":
            qs = ClientDataSource.objects.select_related("client").all()
        else:
            qs = ClientDataSource.objects.filter(client=request.user, is_active=True)
        return Response(ClientDataSourceSerializer(qs, many=True).data)

    def post(self, request):
        # Only admin can create data sources
        if request.user.role != "admin":
            return Response(
                {"detail": "Seul un admin peut créer des sources de données."},
                status=status.HTTP_403_FORBIDDEN,
            )

        client_id = request.data.get("client_id", request.user.pk)
        if client_id in (None, ""):
            return Response(
                {"client_id": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client_id = int(client_id)
        except (TypeError, ValueError):
            return Response(
                {"client_id": ["A valid integer is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not User.objects.filter(pk=client_id, role=User.Role.CLIENT).exists():
            return Response(
                {"client_id": ["Client not found."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ClientDataSourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(client_id=client_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DataSourceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ds = get_object_or_404(ClientDataSource, pk=pk)
        if request.user.role != "admin" and ds.client != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(ClientDataSourceSerializer(ds).data)


# ── ETL Runs ──────────────────────────────────────────────────────────────────


class ETLRunListView(APIView):
    """List past ETL runs (admin=all, client=own)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == "admin":
            runs = ETLRun.objects.select_related("data_source", "client").all()[:50]
        else:
            runs = ETLRun.objects.filter(client=request.user).select_related("data_source")[:50]
        return Response(ETLRunSerializer(runs, many=True).data)


class ETLRunDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        run = get_object_or_404(ETLRun.objects.select_related("data_source", "client"), pk=pk)
        if request.user.role != "admin" and run.client != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(ETLRunSerializer(run).data)


class ETLSyncView(APIView):
    """Trigger an ETL sync for a specific data source."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ETLRunSyncTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ds = get_object_or_404(
            ClientDataSource,
            pk=serializer.validated_data["data_source_id"],
            is_active=True,
        )

        # Clients can only sync their own data sources
        if request.user.role != "admin" and ds.client != request.user:
            return Response(
                {"detail": "Vous ne pouvez synchroniser que vos propres sources."},
                status=status.HTTP_403_FORBIDDEN,
            )

        executor = ETLPipelineExecutor(data_source=ds)
        run = executor.execute()

        http_status = (
            status.HTTP_201_CREATED
            if run.status == ETLRun.Status.SUCCESS
            else status.HTTP_400_BAD_REQUEST
        )
        return Response(ETLRunSerializer(run).data, status=http_status)


class CampaignSyncView(APIView):
    """Discover and create datasources for all campaigns from BI API."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Clients can only sync their own campaigns
        if request.user.role == "admin":
            # Admins can optionally sync for a specific client
            client_id = request.data.get("client_id", request.user.id)
            try:
                client_id = int(client_id)
            except (TypeError, ValueError):
                return Response(
                    {"error": "Invalid client_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            client_id = request.user.id

        try:
            from user.tasks import discover_client_campaigns
            result = discover_client_campaigns.apply_async(args=[client_id], retry=False)
            return Response(
                {
                    "message": "Campaign discovery queued",
                    "task_id": result.id,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



# ── Campaign Records ──────────────────────────────────────────────────────────


class CampaignRecordListView(APIView):
    """Return records for a data source. Clients only see their own."""
    permission_classes = [IsAuthenticated]

    def get(self, request, data_source_id):
        ds = get_object_or_404(ClientDataSource, pk=data_source_id)
        if request.user.role != "admin" and ds.client != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        records = CampaignRecord.objects.filter(data_source=ds)[:500]
        return Response(CampaignRecordSerializer(records, many=True).data)
