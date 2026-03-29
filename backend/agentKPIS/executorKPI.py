import json
import subprocess
import sys
from pathlib import Path

from django.conf import settings

from agentKPIS.models import KPIExecution
from agentKPIS.schema import validate_kpi_payload


def _get_venv_python() -> str:
    """
    Pick project venv python first so runtime dependencies are stable.
    """

    project_root = Path(settings.BASE_DIR)
    candidates = [
        project_root / "venv" / "Scripts" / "python.exe",
        project_root / "venv" / "bin" / "python",
        project_root / ".venv" / "Scripts" / "python.exe",
        project_root / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def execute_kpi_file(record_id: int) -> dict:
    """
    Execute generated KPI file and save results to DB.

    This is intentionally linear and simple:
    1) Load record and file path
    2) Run script
    3) Save stdout/stderr + parsed JSON (if valid)
    """

    record = KPIExecution.objects.get(id=record_id)
    target = Path(record.file_path)

    if not target.exists():
        record.status = "failed"
        record.error_message = f"Generated file does not exist: {target}"
        record.save(update_fields=["status", "error_message"])
        return {"status": "failed", "error": record.error_message}

    try:
        result = subprocess.run(
            [_get_venv_python(), str(target)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(target.parent),
        )

        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        output += f"EXIT CODE: {result.returncode}"

        payload = None
        validation_error = ""
        if result.stdout.strip():
            try:
                raw_payload = json.loads(result.stdout.strip())
                # Validate against KPI schema
                is_valid, error_msg, validated_payload = validate_kpi_payload(raw_payload)
                if is_valid:
                    payload = validated_payload.model_dump()
                else:
                    # Payload is not valid per schema but was parsed as JSON
                    validation_error = f"KPI payload validation failed: {error_msg}"
                    payload = raw_payload  # Store raw for debugging
            except json.JSONDecodeError:
                payload = None

        record.execution_output = output
        record.kpi_payload = payload
        record.status = "success" if result.returncode == 0 and not validation_error else "failed"
        record.error_message = validation_error or ("" if result.returncode == 0 else "Execution failed")
        record.save(
            update_fields=["execution_output", "kpi_payload", "status", "error_message"]
        )

        return {
            "status": record.status,
            "record_id": record.id,
            "kpi_payload": payload,
        }

    except subprocess.TimeoutExpired:
        record.status = "failed"
        record.error_message = "Execution timed out after 30 seconds."
        record.save(update_fields=["status", "error_message"])
        return {"status": "failed", "error": record.error_message}
    except Exception as exc:
        record.status = "failed"
        record.error_message = f"Unexpected execution error: {type(exc).__name__}: {exc}"
        record.save(update_fields=["status", "error_message"])
        return {"status": "failed", "error": record.error_message}

