# ==============================================================================
# agent/views.py - Django Views (API Endpoints)
# ==============================================================================
# POST /api/agent/generate/
#   Accepts a ClientDataSource ID, derives the client's campaign fields from
#   its field_mapping, then runs the LangGraph pipeline which reads the
#   canonical ETL/extractor.py, ETL/transformer.py, ETL/loader.py as
#   reference templates and produces per-client E/T/L scripts in workspace/.
#
# GET  /api/agent/health/
#   Liveness check — returns config details, no auth required.
# ==============================================================================

import traceback
from pathlib import Path

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ETL.models import ClientDataSource
from agent.graph import build_graph


class GenerateETLView(APIView):
    """
    POST /api/agent/generate/

    Run the LangGraph ETL code-generation pipeline for one ClientDataSource.

    The agent uses ETL/extractor.py, ETL/transformer.py and ETL/loader.py as
    structural references and produces client-specific scripts adapted to the
    campaign's fields.  Output files land in WORKSPACE_DIR:
        E_<user_id>_<campaign_id>.py
        T_<user_id>_<campaign_id>.py
        L_<user_id>_<campaign_id>.py

    Request body (JSON):
        data_source_id  int        Required. PK of the ClientDataSource.
        steps           list[str]  Optional. Subset of ["E","T","L"].
                                   Defaults to all three.
        fields          list[str]  Optional. Override the field list sent to
                                   the LLM. Defaults to the keys of
                                   field_mapping (or record_id_field).
        task            str        Optional. Extra free-text instruction.

    Response 200:
        { status, step_results, output_dir }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data_source_id = request.data.get("data_source_id")
        if not data_source_id:
            return Response(
                {"detail": "data_source_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_source = get_object_or_404(ClientDataSource, pk=data_source_id, is_active=True)

        # Clients may only generate code for their own data sources
        if request.user.role != "admin" and data_source.client != request.user:
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        # ── Derive fields ──────────────────────────────────────────────────────
        # Caller override > field_mapping keys > record_id_field fallback
        fields: list = request.data.get("fields") or []
        if not fields:
            mapping: dict = data_source.field_mapping or {}
            fields = list(mapping.keys()) if mapping else [data_source.record_id_field or "id"]

        # ── Build initial LangGraph state ──────────────────────────────────────
        steps: list = request.data.get("steps") or ["E", "T", "L"]
        user_id = str(data_source.client.pk)
        campaign_id = str(data_source.campaign_id)
        output_dir = str(settings.WORKSPACE_DIR)

        task: str = request.data.get("task") or (
            f"Generate an ETL pipeline for client '{data_source.client.username}', "
            f"campaign '{data_source.campaign_name or campaign_id}'. "
            f"Fields: {', '.join(fields)}. "
            f"Data is fetched from the LeaCall external system via "
            f"{data_source.get_api_endpoint()}."
        )

        initial_state = {
            "messages": [],
            "task": task,
            "new_fields": fields,
            # Point the agent at the canonical ETL files as reference
            "extract_ref_path": settings.ETL_EXTRACT_REF,
            "transform_ref_path": settings.ETL_TRANSFORM_REF,
            "load_ref_path": settings.ETL_LOAD_REF,
            "user_id": user_id,
            "campaign_id": campaign_id,
            "output_dir": output_dir,
            "step_order": steps,
            "current_step_index": 0,
            "current_step": "",
            "reference_file_path": "",
            "reference_code": "",
            "output_file_path": "",
            "pytest_file_path": "",
            "generated_code": "",
            "generated_test_code": "",
            "validation_ok": False,
            "test_exit_code": -1,
            "execution_result": "",
            "step_results": {},
            "error_count": 0,
            "max_retries": settings.MAX_RETRIES,
            "status": "preparing",
        }

        try:
            graph = build_graph()
            final_state = graph.invoke(initial_state)
        except Exception as exc:
            return Response(
                {"detail": str(exc), "traceback": traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            "status": final_state.get("status"),
            "step_results": final_state.get("step_results", {}),
            "output_dir": output_dir,
        })


class HealthView(APIView):
    """GET /api/agent/health/ — liveness check, no authentication required."""

    permission_classes = []

    def get(self, request):
        workspace = Path(settings.WORKSPACE_DIR)
        return Response({
            "status": "healthy",
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "model": settings.OPENAI_MODEL,
            "workspace_dir": str(workspace),
            "workspace_exists": workspace.exists(),
            "max_retries": settings.MAX_RETRIES,
            "etl_refs": {
                "extract": settings.ETL_EXTRACT_REF,
                "transform": settings.ETL_TRANSFORM_REF,
                "load": settings.ETL_LOAD_REF,
            },
        })


# Function-based aliases keep the existing urls.py working without change
generate_view = GenerateETLView.as_view()
health_view = HealthView.as_view()
