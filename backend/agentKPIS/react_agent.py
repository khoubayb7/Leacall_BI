from pathlib import Path

from django.conf import settings
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agentKPIS.tools import get_kpi_tools


def generate_kpi_file(
    user_id: int,
    campaign_id: str,
    campaign_name: str = "",
    campaign_type: str = "general",
    dataset_file_path: str = "",
) -> dict:
    """
    Generate one KPI python file using a simple ReAct agent.

    The agent writes a file under workspace/kpi_output and can also execute files
    through tools if it wants to self-check.

    File naming is deterministic: kpi_<user_id>_<campaign_id>.py
    so each refresh replaces the same logical artifact.
    """

    workspace_dir = Path(settings.WORKSPACE_DIR)
    output_dir = workspace_dir / "kpi_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_path = workspace_dir / "examples" / "sample_kpi.py"
    try:
        reference_code = reference_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        reference_code = f"# Missing reference file: {reference_path}"
    except OSError as exc:
        reference_code = f"# Failed to read reference file: {reference_path}\n# {type(exc).__name__}: {exc}"

    # Use stable filenames to avoid accumulating random-suffix KPI files.
    # We pass a relative path because file tools are rooted at WORKSPACE_DIR.
    safe_campaign_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in campaign_id)
    relative_path = f"kpi_output/kpi_{user_id}_{safe_campaign_id}.py"
    absolute_path = output_dir / f"kpi_{user_id}_{safe_campaign_id}.py"

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
        timeout=25,
        max_retries=1,
    )
    tools = get_kpi_tools(str(workspace_dir))
    agent = create_react_agent(llm, tools)

    prompt = (
        "You are a senior Python engineer responsible for generating production-ready KPI code.\n"
        "Use the reference file as the mandatory template, not only inspiration.\n"
        "Do not modify the reference file under any circumstance.\n\n"
        "--- REFERENCE KPI CODE ---\n"
        f"{reference_code}\n"
        "--- END REFERENCE KPI CODE ---\n\n"
        "Task:\n"
        "Generate a new KPI Python script for the selected campaign context.\n"
        "Do not request any additional user input.\n\n"
        "Campaign context:\n"
        f"- campaign_id: {campaign_id}\n"
        f"- campaign_name: {campaign_name or 'N/A'}\n"
        f"- campaign_type: {campaign_type}\n\n"
        "Data source for KPI computation (mandatory):\n"
        f"- dataset_file_path: {dataset_file_path}\n"
        "- This JSON file contains ETL-loaded records from CampaignRecord and latest ETL run metadata.\n"
        "- You MUST compute KPIs strictly from this file.\n"
        "- Do NOT call external APIs or database in the generated script.\n\n"
        "Output location:\n"
        f"Write the file exactly at: {relative_path}\n\n"
        "Strict template contract (must match reference structure):\n"
        "1) Keep the same high-level module organization as the reference.\n"
        "2) Keep function names load_dataset and generate_kpis.\n"
        "3) Keep helper-style design (safe parsing, extraction helpers, divide helper).\n"
        "4) Keep output style deterministic and JSON-serializable.\n"
        "5) Keep KPI sections in the same shape as the reference when fields are available, and use safe defaults when missing.\n\n"
        "Implementation requirements:\n"
        "1) Output must be valid Python code only (no markdown, no explanations).\n"
        "2) Use only Python standard library modules.\n"
        "3) Define a function load_dataset() that reads dataset_file_path.\n"
        "4) Define generate_kpis() that returns KPI dictionary computed from dataset['records'].\n"
        "5) Include if __name__ == '__main__' and print JSON output only.\n"
        "6) Keep implementation concise, readable, and deterministic.\n"
        "7) Follow clean naming and professional code style.\n"
        "8) If any field alias is unknown, gracefully fallback to 0/False/empty instead of failing.\n\n"
        "Final step:\n"
        "After writing the file, run execute_python_file on the generated file and ensure it exits with code 0. "
        "If it fails, fix and rerun until success, then confirm completion."
    )

    response = agent.invoke({"messages": [("user", prompt)]})

    return {
        "file_path": str(absolute_path.resolve()),
        "agent_messages": response.get("messages", []),
    }
