import subprocess
import sys
from pathlib import Path

from django.conf import settings
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_core.tools import tool


def _get_venv_python() -> str:
    """
    Return a Python executable from local venv when available.

    This keeps script execution consistent with project dependencies.
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


@tool
def execute_python_file(file_path: str) -> str:
    """
    Execute a Python file and return stdout/stderr.

    Agent can call this tool to validate generated KPI scripts.
    """

    target = Path(file_path)
    if not target.exists():
        return f"ERROR: file not found: {target}"
    if target.suffix != ".py":
        return f"ERROR: only .py files are supported: {target}"

    try:
        result = subprocess.run(
            [_get_venv_python(), str(target)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(target.parent),
        )
        chunks = []
        if result.stdout:
            chunks.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            chunks.append(f"STDERR:\n{result.stderr}")
        chunks.append(f"EXIT CODE: {result.returncode}")
        return "\n".join(chunks)
    except subprocess.TimeoutExpired:
        return "ERROR: execution timed out after 30 seconds"
    except Exception as exc:
        return f"ERROR: unexpected execution failure: {type(exc).__name__}: {exc}"


def get_kpi_tools(workspace_dir: str) -> list:
    """
    Build the full tool list for the KPI ReAct agent.

    Included tools:
    - write_file / read_file / list_directory (LangChain toolkit)
    - execute_python_file (custom execution tool)
    """

    toolkit = FileManagementToolkit(
        root_dir=workspace_dir,
        selected_tools=["write_file", "read_file", "list_directory"],
    )
    return toolkit.get_tools() + [execute_python_file]

