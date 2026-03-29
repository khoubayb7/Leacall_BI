from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.permissions import IsAdmin, IsClient

from .models import CampaignRecord, ClientDataSource, ETLRun
from .tasks import run_etl_pipeline
from .serializers import (
    CampaignRecordSerializer,
    ClientDataSourceSerializer,
    ETLRunSerializer,
    ETLRunSyncTriggerSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


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

        # Create pending run immediately, then queue background ETL execution.
        run = ETLRun.objects.create(
            data_source=ds,
            client=ds.client,
            status=ETLRun.Status.PENDING,
        )

        try:
            async_result = run_etl_pipeline.apply_async(args=[ds.id, run.id])
            logger.info(
                "Manual ETL queued: task_id=%s run_id=%s data_source_id=%s client_id=%s campaign_id=%s",
                async_result.id,
                run.id,
                ds.id,
                ds.client_id,
                ds.campaign_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Manual ETL queueing failed for data_source_id=%s run_id=%s",
                ds.id,
                run.id,
            )
            run.status = ETLRun.Status.FAILED
            run.error_message = f"Failed to enqueue ETL task: {exc}"
            run.save(update_fields=["status", "error_message"])
            return Response(
                {
                    "status": "error",
                    "detail": "Unable to queue ETL run.",
                    "error": str(exc),
                    "run_id": run.id,
                    "data_source_id": ds.id,
                    "campaign_id": ds.campaign_id,
                    "campaign_name": ds.campaign_name or ds.campaign_id,
                    "client_id": ds.client_id,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Keep legacy fields (run_id/status) for frontend compatibility and
        # add task metadata similar to KPI async flow.
        return Response(
            {
                "status": "queued",
                "run_id": run.id,
                "task_id": async_result.id,
                "data_source_id": ds.id,
                "campaign_id": ds.campaign_id,
                "campaign_name": ds.campaign_name or ds.campaign_id,
                "client_id": ds.client_id,
            },
            status=status.HTTP_202_ACCEPTED,
        )


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
