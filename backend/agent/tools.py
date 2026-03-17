# ==============================================================================
# agent/tools.py - Tool Definitions for the LangGraph Agent
# ==============================================================================
# Defines all tools the agent can use: file management + code execution.
#
# KEY CONCEPTS FOR INTERNS:
#   - LangChain provides PREBUILT tools we can use directly:
#     * FileManagementToolkit: read, write, list, copy, move, delete files
#   - We also create CUSTOM tools when prebuilt ones don't fit:
#     * run_python_file: executes a Python script in a subprocess
#   - Tools are decorated with @tool so LangGraph can call them
#   - Each tool has a docstring that the LLM reads to decide when to use it
#   - The working_directory restricts file access for safety
#
# PREBUILT TOOLS USED:
#   - langchain_community.agent_toolkits.FileManagementToolkit
#     Provides: ReadFileTool, WriteFileTool, ListDirectoryTool,
#               CopyFileTool, MoveFileTool, FileSearchTool
#
# CUSTOM TOOLS:
#   - run_python_file: Runs a .py file with subprocess + timeout
# ==============================================================================

import os
import subprocess
import sys
from pathlib import Path

from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_core.tools import tool


def _get_venv_python() -> str:
    """
    Get the path to the Python executable inside the project's venv.

    WHY: When Django runs, sys.executable points to the venv Python.
    But scripts executed in a subprocess need the venv Python too,
    so they can import packages installed there (pandas, etc.).

    Falls back to sys.executable if no venv is found.
    """
    from django.conf import settings

    # Look for venv in the project root
    project_root = Path(settings.BASE_DIR)

    # Windows: venv\Scripts\python.exe
    # Linux/Mac: venv/bin/python
    candidates = [
        project_root / "venv" / "Scripts" / "python.exe",   # Windows
        project_root / "venv" / "bin" / "python",           # Linux/Mac
        project_root / ".venv" / "Scripts" / "python.exe",  # Windows alt
        project_root / ".venv" / "bin" / "python",          # Linux/Mac alt
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    # Fallback: use whatever Python is running this process
    return sys.executable


def get_file_tools(working_directory: str) -> list:
    """
    Get prebuilt file management tools from LangChain, scoped to a directory.

    LangChain's FileManagementToolkit provides these tools out of the box:
      - ReadFileTool:      Read contents of a file
      - WriteFileTool:     Write content to a file (create or overwrite)
      - ListDirectoryTool: List files in a directory
      - CopyFileTool:      Copy a file
      - MoveFileTool:      Move/rename a file
      - FileSearchTool:    Search for files by name pattern

    We only select the ones we need for ETL work:
      read_file, write_file, list_directory

    Args:
        working_directory: The root directory the tools are allowed to access.

    Returns:
        A list of LangChain Tool objects.
    """
    # Create the toolkit scoped to our workspace directory
    toolkit = FileManagementToolkit(
        root_dir=working_directory,
        # Only include the tools we need (safety: no delete/move)
        selected_tools=["read_file", "write_file", "list_directory"],
    )
    return toolkit.get_tools()


@tool
def run_python_file(file_path: str) -> str:
    """
    Execute a Python file and return its stdout and stderr output.

    This tool runs a Python script in a SEPARATE subprocess for safety.
    It has a 30-second timeout to prevent infinite loops.

    Args:
        file_path: Absolute path to the .py file to execute.

    Returns:
        A string containing stdout and stderr from the execution.
        If the script fails, includes the error traceback.
    """
    file_path = Path(file_path)

    # --- Safety checks ---
    if not file_path.exists():
        return f"ERROR: File not found: {file_path}"

    if not file_path.suffix == ".py":
        return f"ERROR: Not a Python file: {file_path}"

    try:
        # Get the venv Python so installed packages (pandas etc.) are available
        python_exe = _get_venv_python()

        # Run the Python script in a subprocess
        # - python_exe points to the venv Python interpreter
        # - capture_output=True captures stdout and stderr
        # - text=True returns strings instead of bytes
        # - timeout=30 kills the process after 30 seconds
        result = subprocess.run(
            [python_exe, str(file_path)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(file_path.parent),  # Run from the file's directory
        )

        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        if result.returncode != 0:
            output += f"\nEXIT CODE: {result.returncode} (non-zero = error)"
        else:
            output += "\nEXIT CODE: 0 (success)"

        return output if output.strip() else "Script executed successfully (no output)."

    except subprocess.TimeoutExpired:
        return "ERROR: Script execution timed out after 30 seconds. Possible infinite loop."
    except Exception as e:
        return f"ERROR: Failed to execute script: {type(e).__name__}: {e}"

@tool
def run_pytest(path: str = "") -> str:
    """
    Runs pytest on the given path and returns a detailed output report.

    Args:
        path: Path to the test file or directory to run pytest on.
              Must be provided — no default path is assumed.
    """
    # ── Validate path ──────────────────────────────────────────────────────────
    if not path or path.strip() == "":
        return (
            "❌ ERROR: No path provided.\n"
            "You must specify a path to a test file or directory.\n"
            "Example: run_pytest('tests/test_transform.py')"
        )

    if not os.path.exists(path):
        return (
            f"❌ ERROR: Path does not exist: '{path}'\n"
            f"Please provide a valid path to a test file or directory."
        )

    # ── Run pytest ─────────────────────────────────────────────────────────────
    python_exe = _get_venv_python()

    result = subprocess.run(
        [python_exe, "-m", "pytest", path, "-v", "--tb=short", "--no-header"],
        capture_output=True,
        text=True
    )

    # ── Build output ───────────────────────────────────────────────────────────
    sep = "═" * 60
    lines = []

    lines.append(f"\n{sep}")
    lines.append(f"  🧪 PYTEST REPORT")
    lines.append(f"  📁 Path    : {path}")
    lines.append(f"  🐍 Python  : {python_exe}")
    lines.append(sep)

    # Main pytest output
    if result.stdout.strip():
        lines.append("\n📋 OUTPUT:\n")
        lines.append(result.stdout.strip())

    # Warnings / import errors from stderr
    if result.stderr.strip():
        lines.append("\n⚠️  WARNINGS / ERRORS:\n")
        lines.append(result.stderr.strip())

    # Final verdict
    lines.append(f"\n{sep}")
    if result.returncode == 0:
        lines.append("  ✅ RESULT   : ALL TESTS PASSED")
    else:
        lines.append("  ❌ RESULT   : SOME TESTS FAILED")
    lines.append(f"  🔢 EXIT CODE : {result.returncode}")
    lines.append(sep)

    return "\n".join(lines)

def get_all_tools(working_directory: str) -> list:
    """
    Assemble all tools (prebuilt + custom) for the agent.

    This is the main entry point for getting the tool list.
    The LangGraph agent will have access to all these tools.

    Args:
        working_directory: Root directory for file operations.

    Returns:
        Combined list of all available tools.
    """
    # Get prebuilt file management tools
    file_tools = get_file_tools(working_directory)

    # Add our custom tools
    custom_tools = [run_python_file, run_pytest]

    all_tools = file_tools + custom_tools

    return all_tools








