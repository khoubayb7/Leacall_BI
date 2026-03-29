import logging

from ETL.models import ClientDataSource
from agentKPIS.models import KPIExecution
from agentKPIS.tasks import generate_and_execute_kpi_task
from django.db.models import QuerySet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


logger = logging.getLogger(__name__)


def _execution_to_dict(row: KPIExecution) -> dict:
    return {
        "id": row.id,
        "status": row.status,
        "campaign_id": row.campaign_id,
        "campaign_name": row.campaign_name,
        "campaign_type": row.campaign_type,
        "file_path": row.file_path,
        "celery_task_id": row.celery_task_id,
        "kpi_payload": row.kpi_payload,
        "execution_output": row.execution_output,
        "error_message": row.error_message,
        "created_at": row.created_at.isoformat(),
    }


def _to_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _is_admin(user) -> bool:
    return getattr(user, "role", None) == "admin"


def _visible_campaign_sources(request) -> QuerySet[ClientDataSource]:
    qs = ClientDataSource.objects.filter(is_active=True)
    if not _is_admin(request.user):
        qs = qs.filter(client=request.user)
    return qs


def _visible_kpi_executions(request) -> QuerySet[KPIExecution]:
    qs = KPIExecution.objects.order_by("-created_at")
    if _is_admin(request.user):
        return qs
    return qs.filter(client=request.user)


class GenerateKPIAPIView(APIView):
    """
    Queue KPI generation/execution task.

    This endpoint supports campaign selection by campaign_name (preferred)
    or campaign_id (fallback), and does not require ask text.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        campaign_name = str(request.query_params.get("campaign_name", "")).strip()
        campaign_id = str(request.query_params.get("campaign_id", "")).strip()
        campaign_type = str(request.query_params.get("campaign_type", "")).strip()
        force_regenerate = _to_bool(request.query_params.get("force_regenerate"), default=False)
        return self._queue_from_selection(
            request=request,
            campaign_name=campaign_name,
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            force_regenerate=force_regenerate,
        )

    def post(self, request):
        body = request.data or {}
        campaign_name = str(body.get("campaign_name", "")).strip()
        campaign_id = str(body.get("campaign_id", "")).strip()
        campaign_type = str(body.get("campaign_type", "")).strip()
        force_regenerate = _to_bool(body.get("force_regenerate"), default=False)
        return self._queue_from_selection(
            request=request,
            campaign_name=campaign_name,
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            force_regenerate=force_regenerate,
        )

    def _queue_from_selection(
        self,
        request,
        campaign_name: str,
        campaign_id: str,
        campaign_type: str,
        force_regenerate: bool,
    ):
        if not campaign_name and not campaign_id:
            return Response(
                {
                    "status": "error",
                    "message": "Provide 'campaign_name' (preferred) or 'campaign_id'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolved = self._resolve_campaign(request, campaign_name=campaign_name, campaign_id=campaign_id)
        if isinstance(resolved, dict) and resolved.get("error") == "multiple_campaign_name_matches":
            return Response(
                {
                    "status": "error",
                    "message": (
                        "Multiple campaigns share this name. "
                        "Please provide campaign_id as fallback."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )
        if not resolved:
            if campaign_name:
                return Response(
                    {
                        "status": "error",
                        "message": f"Campaign name '{campaign_name}' not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                {
                    "status": "error",
                    "message": f"Campaign id '{campaign_id}' not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return self._queue_task(
            campaign_id=resolved["campaign_id"],
            campaign_name=resolved["campaign_name"],
            campaign_type=campaign_type or resolved["campaign_type"],
            client_id=resolved["client_id"],
            force_regenerate=force_regenerate,
        )

    @staticmethod
    def _resolve_campaign(request, campaign_name: str, campaign_id: str):
        qs = _visible_campaign_sources(request)

        if campaign_name:
            matches = list(qs.filter(campaign_name=campaign_name))
            if not matches:
                return None
            if len(matches) > 1:
                return {"error": "multiple_campaign_name_matches"}
            ds = matches[0]
            return {
                "campaign_id": ds.campaign_id,
                "campaign_name": ds.campaign_name,
                "campaign_type": ds.campaign_type,
                "client_id": ds.client_id,
            }

        ds = qs.filter(campaign_id=campaign_id).first()
        if not ds:
            return None

        return {
            "campaign_id": ds.campaign_id,
            "campaign_name": ds.campaign_name,
            "campaign_type": ds.campaign_type,
            "client_id": ds.client_id,
        }

    @staticmethod
    def _queue_task(campaign_id: str, campaign_name: str, campaign_type: str, client_id: int, force_regenerate: bool):
        record = KPIExecution.objects.create(
            ask="AUTO_INTERNAL_PROMPT",
            client_id=client_id,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
            file_path="",
            status="queued",
        )

        payload = {
            "record_id": record.id,
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "campaign_type": campaign_type,
            "client_id": client_id,
            "force_regenerate": force_regenerate,
        }

        try:
            async_result = generate_and_execute_kpi_task.apply_async(args=[payload])
            record.celery_task_id = async_result.id
            record.save(update_fields=["celery_task_id"])
            return Response(
                {
                    "status": "queued",
                    "execution_id": record.id,
                    "task_id": async_result.id,
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "campaign_type": campaign_type,
                    "force_regenerate": force_regenerate,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to queue KPI task; falling back to synchronous execution.")
            try:
                # Keep KPI generation usable even if broker/worker is unavailable.
                generate_and_execute_kpi_task.apply(args=[payload])
                record.refresh_from_db()
                return Response(
                    {
                        "status": "ok",
                        "mode": "sync_fallback",
                        "message": "KPI executed synchronously because queue is unavailable.",
                        "execution": _execution_to_dict(record),
                        "queue_error": str(exc),
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as sync_exc:  # noqa: BLE001
                record.status = "failed"
                record.error_message = f"KPI queue and sync fallback both failed: {sync_exc}"
                record.save(update_fields=["status", "error_message"])
                return Response(
                    {
                        "status": "error",
                        "message": "Unable to queue KPI generation.",
                        "detail": str(sync_exc),
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )


class KPIExecutionDetailAPIView(APIView):
    """Read one KPI execution record from database."""

    permission_classes = [IsAuthenticated]

    def get(self, request, execution_id: int):
        row = _visible_kpi_executions(request).filter(id=execution_id).first()
        if not row:
            return Response({"status": "error", "message": "Execution not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(_execution_to_dict(row))


class KPIExecutionListAPIView(APIView):
    """Return recent KPI executions with optional limit."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", "20"))
        except (TypeError, ValueError):
            limit = 20

        campaign_name = str(request.query_params.get("campaign_name", "")).strip()
        campaign_id = str(request.query_params.get("campaign_id", "")).strip()

        limit = max(1, min(limit, 100))
        qs = _visible_kpi_executions(request)
        if campaign_name:
            qs = qs.filter(campaign_name=campaign_name)
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)

        rows = list(qs[:limit])
        return Response(
            {
                "status": "ok",
                "count": len(rows),
                "results": [_execution_to_dict(row) for row in rows],
            }
        )


class KPIExecutionByTaskAPIView(APIView):
    """Read one KPI execution by celery task id."""

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id: str):
        row = _visible_kpi_executions(request).filter(celery_task_id=task_id).order_by("-id").first()
        if not row:
            return Response({"status": "error", "message": "Execution not found yet"}, status=status.HTTP_404_NOT_FOUND)

        return Response(_execution_to_dict(row))


class CampaignOptionsAPIView(APIView):
    """Return active campaign options for dropdowns."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = _visible_campaign_sources(request).order_by("campaign_name", "campaign_id")
        options = [
            {
                "data_source_id": row.id,
                "campaign_name": row.campaign_name or row.campaign_id,
                "campaign_id": row.campaign_id,
                "campaign_type": row.campaign_type,
            }
            for row in rows
        ]
        return Response({"status": "ok", "campaigns": options})
