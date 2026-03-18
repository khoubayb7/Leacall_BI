import json
from django.utils.decorators import method_decorator
from django.views import View

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ETL.models import ClientDataSource
from agentKPIS.executorKPI import execute_kpi_file
from agentKPIS.models import KPIExecution
from agentKPIS.tasks import generate_and_execute_kpi_task


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


def _to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _latest_file_path(campaign_id: str, campaign_name: str) -> str:
    qs = KPIExecution.objects.exclude(file_path="").order_by("-created_at")
    if campaign_id:
        qs = qs.filter(campaign_id=campaign_id)
    if campaign_name:
        qs = qs.filter(campaign_name=campaign_name)

    row = qs.first()
    return row.file_path if row and row.file_path else ""


@method_decorator(csrf_exempt, name="dispatch")
class GenerateKPIAPIView(View):
    """
    Queue KPI generation/execution task.

    This endpoint supports campaign selection by campaign_name (preferred)
    or campaign_id (fallback), and does not require ask text.
    Each call generates fresh KPIs for the selected campaign.
    """

    http_method_names = ["get", "post"]

    def get(self, request):
        campaign_name = str(request.GET.get("campaign_name", "")).strip()
        campaign_id = str(request.GET.get("campaign_id", "")).strip()
        campaign_type = str(request.GET.get("campaign_type", "")).strip()
        force_regenerate = _to_bool(request.GET.get("force_regenerate"), default=False)
        return self._queue_from_selection(
            request=request,
            campaign_name=campaign_name,
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            force_regenerate=force_regenerate,
        )

    def post(self, request):
        body = {}
        if request.body:
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "Invalid JSON body"}, status=400)
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
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Provide 'campaign_name' (preferred) or 'campaign_id'.",
                },
                status=400,
            )

        resolved = self._resolve_campaign(request, campaign_name=campaign_name, campaign_id=campaign_id)
        if isinstance(resolved, JsonResponse):
            return resolved

        return self._queue_task(
            campaign_id=resolved["campaign_id"],
            campaign_name=resolved["campaign_name"],
            campaign_type=campaign_type or resolved["campaign_type"],
            client_id=resolved["client_id"],
            force_regenerate=force_regenerate,
        )

    @staticmethod
    def _resolve_campaign(request, campaign_name: str, campaign_id: str):
        qs = ClientDataSource.objects.filter(is_active=True)

        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False) and getattr(user, "role", None) != "admin":
            qs = qs.filter(client=user)

        if campaign_name:
            matches = list(qs.filter(campaign_name=campaign_name))
            if not matches:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Campaign name '{campaign_name}' not found.",
                    },
                    status=404,
                )
            if len(matches) > 1:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": (
                            "Multiple campaigns share this name. "
                            "Please provide campaign_id as fallback."
                        ),
                    },
                    status=409,
                )
            ds = matches[0]
            return {
                "campaign_id": ds.campaign_id,
                "campaign_name": ds.campaign_name,
                "campaign_type": ds.campaign_type,
                "client_id": ds.client_id,
            }

        ds = qs.filter(campaign_id=campaign_id).first()
        if not ds:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Campaign id '{campaign_id}' not found.",
                },
                status=404,
            )

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
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
            file_path="",
            status="queued",
        )

        async_result = generate_and_execute_kpi_task.apply_async(
            args=[
                {
                    "record_id": record.id,
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "campaign_type": campaign_type,
                    "client_id": client_id,
                    "force_regenerate": force_regenerate,
                }
            ]
        )
        record.celery_task_id = async_result.id
        record.save(update_fields=["celery_task_id"])
        return JsonResponse(
            {
                "status": "queued",
                "execution_id": record.id,
                "task_id": async_result.id,
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "campaign_type": campaign_type,
                "force_regenerate": force_regenerate,
            },
            status=202,
        )


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class KPIExecutionDetailAPIView(View):
    """
    Read one KPI execution record from database.
    """

    def get(self, request, execution_id: int):
        try:
            row = KPIExecution.objects.get(id=execution_id)
        except KPIExecution.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Execution not found"}, status=404)

        return JsonResponse(_execution_to_dict(row))


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class KPIExecutionListAPIView(View):
    """
    Return recent KPI executions with optional limit.
    """

    def get(self, request):
        try:
            limit = int(request.GET.get("limit", "20"))
        except (TypeError, ValueError):
            limit = 20

        campaign_name = str(request.GET.get("campaign_name", "")).strip()
        campaign_id = str(request.GET.get("campaign_id", "")).strip()

        limit = max(1, min(limit, 100))
        qs = KPIExecution.objects.order_by("-created_at")
        if campaign_name:
            qs = qs.filter(campaign_name=campaign_name)
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)

        rows = qs[:limit]
        return JsonResponse(
            {
                "status": "ok",
                "count": len(rows),
                "results": [_execution_to_dict(row) for row in rows],
            }
        )


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class KPIExecutionByTaskAPIView(View):
    """
    Read one KPI execution by celery task id.
    """

    def get(self, request, task_id: str):
        row = KPIExecution.objects.filter(celery_task_id=task_id).order_by("-id").first()
        if not row:
            return JsonResponse({"status": "error", "message": "Execution not found yet"}, status=404)

        return JsonResponse(_execution_to_dict(row))


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class CampaignOptionsAPIView(View):
    """
    Return active campaign options for dropdowns.
    """

    def get(self, request):
        qs = ClientDataSource.objects.filter(is_active=True)

        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False) and getattr(user, "role", None) != "admin":
            qs = qs.filter(client=user)

        rows = qs.order_by("campaign_name", "campaign_id")
        options = [
            {
                "data_source_id": row.id,
                "campaign_name": row.campaign_name or row.campaign_id,
                "campaign_id": row.campaign_id,
                "campaign_type": row.campaign_type,
            }
            for row in rows
        ]
        return JsonResponse({"status": "ok", "campaigns": options})

