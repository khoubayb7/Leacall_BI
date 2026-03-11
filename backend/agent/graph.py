import ast
import json
import subprocess
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from agent.state import AgentState
from agent.tools import _get_venv_python

STEP_TO_REFERENCE_KEY = {
    "E": "extract_ref_path",
    "T": "transform_ref_path",
    "L": "load_ref_path",
}

STEP_TO_LABEL = {
    "E": "extract",
    "T": "transform",
    "L": "load",
}


def prepare_current_step(state: AgentState) -> dict[str, Any]:
    step_order = state.get("step_order", ["E", "T", "L"])
    current_index = state.get("current_step_index", 0)

    if current_index >= len(step_order):
        has_failed = any(
            result.get("status") != "success"
            for result in state.get("step_results", {}).values()
        )
        return {"status": "failed" if has_failed else "done"}

    step = step_order[current_index]
    reference_key = STEP_TO_REFERENCE_KEY.get(step, "")
    reference_file_path = state.get(reference_key, "")

    output_dir = Path(state["output_dir"])
    output_file_path = output_dir / f"{step}_{state['user_id']}_{state['campaign_id']}.py"
    pytest_file_path = output_dir / f"test_{step}_{state['user_id']}_{state['campaign_id']}.py"

    return {
        "current_step": step,
        "reference_file_path": str(reference_file_path),
        "output_file_path": str(output_file_path),
        "pytest_file_path": str(pytest_file_path),
        "reference_code": "",
        "generated_code": "",
        "generated_test_code": "",
        "execution_result": "",
        "validation_ok": False,
        "test_exit_code": -1,
        "error_count": 0,
        "status": "reading",
    }


def read_reference(state: AgentState) -> dict[str, Any]:
    reference_file = Path(state["reference_file_path"])

    if not reference_file.exists():
        return {
            "reference_code": (
                f"# Missing reference file: {reference_file}\n"
                "# Build this step from scratch while keeping ETL conventions."
            ),
            "status": "generating",
            "messages": [
                HumanMessage(
                    content=f"Reference file missing for step {state['current_step']}: {reference_file}"
                )
            ],
        }

    content = reference_file.read_text(encoding="utf-8")
    return {
        "reference_code": content,
        "status": "generating",
        "messages": [
            HumanMessage(
                content=(
                    f"Read reference for step {state['current_step']} "
                    f"from {reference_file} ({len(content)} chars)."
                )
            )
        ],
    }


def plan_and_generate(state: AgentState) -> dict[str, Any]:
    step = state["current_step"]
    step_label = STEP_TO_LABEL.get(step, "etl")
    fields_csv = ", ".join(state.get("new_fields", []))

    system_prompt = (
        "You are an expert Python ETL engineer.\n"
        "Generate one complete Python file for the requested ETL step.\n"
        "Keep the same architecture as the reference file but update field usage.\n"
        "Return only Python code with no markdown."
    )
    user_prompt = (
        f"Current ETL step: {step} ({step_label})\n"
        f"Task: {state['task']}\n"
        f"New fields that must be used: {fields_csv}\n"
        f"Output file name target: {Path(state['output_file_path']).name}\n\n"
        "Reference code:\n"
        f"{state['reference_code']}\n\n"
        "Requirements:\n"
        "- Keep the ETL step behavior aligned to this step only.\n"
        "- Replace old field usage with the requested new fields where relevant.\n"
        "- Preserve runnable Python quality (imports, typing, docs, and error handling)."
    )

    llm = _get_llm()
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )

    generated_code = _clean_code_response(response.content)
    return {
        "generated_code": generated_code,
        "status": "validating",
        "messages": [
            AIMessage(
                content=(
                    f"Generated code for step {step} "
                    f"({len(generated_code)} chars)."
                )
            )
        ],
    }


def validate_generated_code(state: AgentState) -> dict[str, Any]:
    try:
        ast.parse(state["generated_code"])
    except SyntaxError as exc:
        return {
            "validation_ok": False,
            "execution_result": f"Syntax validation failed: {exc}",
            "status": "evaluating",
        }

    return {
        "validation_ok": True,
        "execution_result": "Syntax validation passed.",
        "status": "saving",
    }


def save_code(state: AgentState) -> dict[str, Any]:
    output_file = Path(state["output_file_path"])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(state["generated_code"], encoding="utf-8")

    return {
        "status": "testing",
        "messages": [
            AIMessage(
                content=f"Saved generated code to {output_file}."
            )
        ],
    }


def generate_pytest(state: AgentState) -> dict[str, Any]:
    target_literal = json.dumps(str(Path(state["output_file_path"])))
    fields_literal = json.dumps(state.get("new_fields", []), ensure_ascii=True)

    test_code = f"""from pathlib import Path
import ast

TARGET_FILE = Path({target_literal})
REQUIRED_FIELDS = {fields_literal}


def test_generated_file_exists():
    assert TARGET_FILE.exists(), f"Missing generated file: {{TARGET_FILE}}"


def test_generated_file_has_valid_syntax():
    source = TARGET_FILE.read_text(encoding="utf-8")
    ast.parse(source)


def test_generated_file_mentions_requested_fields():
    source = TARGET_FILE.read_text(encoding="utf-8")
    missing = [field for field in REQUIRED_FIELDS if field not in source]
    assert not missing, f"Missing requested fields in generated file: {{missing}}"
"""

    return {
        "generated_test_code": test_code,
        "status": "saving",
    }


def save_pytest(state: AgentState) -> dict[str, Any]:
    pytest_file = Path(state["pytest_file_path"])
    pytest_file.parent.mkdir(parents=True, exist_ok=True)
    pytest_file.write_text(state["generated_test_code"], encoding="utf-8")

    return {
        "status": "testing",
        "messages": [
            AIMessage(content=f"Saved pytest file to {pytest_file}.")
        ],
    }


def run_pytest(state: AgentState) -> dict[str, Any]:
    pytest_file = Path(state["pytest_file_path"])
    python_exe = _get_venv_python()

    result = subprocess.run(
        [python_exe, "-m", "pytest", str(pytest_file), "-q", "--tb=short", "--no-header"],
        capture_output=True,
        text=True,
        cwd=str(pytest_file.parent),
    )

    output_parts = []
    if result.stdout:
        output_parts.append(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        output_parts.append(f"STDERR:\n{result.stderr}")
    output_parts.append(f"EXIT CODE: {result.returncode}")

    return {
        "test_exit_code": result.returncode,
        "execution_result": "\n".join(output_parts),
        "status": "evaluating",
    }


def evaluate_step(state: AgentState) -> dict[str, Any]:
    validation_ok = state.get("validation_ok", False)
    pytest_ok = state.get("test_exit_code", 1) == 0
    is_success = validation_ok and pytest_ok

    if is_success:
        step_results = _record_step_result(
            state=state,
            result_status="success",
            attempts=state.get("error_count", 0),
        )
        return {
            "status": "advancing",
            "step_results": step_results,
            "messages": [
                AIMessage(content=f"Step {state['current_step']} completed successfully.")
            ],
        }

    next_error_count = state.get("error_count", 0) + 1
    if next_error_count < state["max_retries"]:
        return {
            "error_count": next_error_count,
            "status": "fixing",
            "messages": [
                AIMessage(
                    content=(
                        f"Step {state['current_step']} failed "
                        f"(attempt {next_error_count}/{state['max_retries']}). "
                        "Generating a fix."
                    )
                )
            ],
        }

    step_results = _record_step_result(
        state=state,
        result_status="failed",
        attempts=next_error_count,
    )
    return {
        "error_count": next_error_count,
        "status": "advancing",
        "step_results": step_results,
        "messages": [
            AIMessage(
                content=(
                    f"Step {state['current_step']} failed after "
                    f"{next_error_count} attempts. Moving to next step."
                )
            )
        ],
    }


def fix_code(state: AgentState) -> dict[str, Any]:
    step = state["current_step"]
    step_label = STEP_TO_LABEL.get(step, "etl")
    fields_csv = ", ".join(state.get("new_fields", []))

    system_prompt = (
        "You are an expert Python ETL debugger.\n"
        "Fix the provided ETL code based on validation/pytest failures.\n"
        "Return only complete Python code with no markdown."
    )
    user_prompt = (
        f"Current ETL step: {step} ({step_label})\n"
        f"Task: {state['task']}\n"
        f"Required fields: {fields_csv}\n\n"
        "Current code:\n"
        f"{state['generated_code']}\n\n"
        "Failure output:\n"
        f"{state['execution_result']}\n\n"
        "Fix the code while preserving structure."
    )

    llm = _get_llm()
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    fixed_code = _clean_code_response(response.content)

    return {
        "generated_code": fixed_code,
        "status": "validating",
        "messages": [
            AIMessage(
                content=(
                    f"Generated fix for step {step} "
                    f"(attempt {state.get('error_count', 0)})."
                )
            )
        ],
    }


def advance_step(state: AgentState) -> dict[str, Any]:
    next_index = state.get("current_step_index", 0) + 1
    step_order = state.get("step_order", ["E", "T", "L"])

    if next_index >= len(step_order):
        has_failed = any(
            item.get("status") != "success"
            for item in state.get("step_results", {}).values()
        )
        return {
            "current_step_index": next_index,
            "status": "failed" if has_failed else "done",
        }

    return {
        "current_step_index": next_index,
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
        "error_count": 0,
        "status": "preparing",
    }


def respond(state: AgentState) -> dict[str, Any]:
    lines = [
        f"Final status: {state.get('status', 'unknown')}",
        "Step results:",
    ]

    for step in state.get("step_order", ["E", "T", "L"]):
        result = state.get("step_results", {}).get(step)
        if not result:
            lines.append(f"- {step}: not processed")
            continue
        lines.append(
            f"- {step}: {result.get('status')} "
            f"(output={result.get('output_file')}, pytest={result.get('pytest_file')})"
        )

    return {"messages": [AIMessage(content="\n".join(lines))]}


def route_after_validation(state: AgentState) -> str:
    if state.get("validation_ok", False):
        return "save_code"
    return "evaluate_step"


def route_after_evaluate(state: AgentState) -> str:
    if state.get("status") == "fixing":
        return "fix_code"
    return "advance_step"


def route_after_advance(state: AgentState) -> str:
    if state.get("status") in {"done", "failed"}:
        return "respond"
    return "prepare_current_step"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("prepare_current_step", prepare_current_step)
    graph.add_node("read_reference", read_reference)
    graph.add_node("plan_and_generate", plan_and_generate)
    graph.add_node("validate_generated_code", validate_generated_code)
    graph.add_node("save_code", save_code)
    graph.add_node("generate_pytest", generate_pytest)
    graph.add_node("save_pytest", save_pytest)
    graph.add_node("run_pytest", run_pytest)
    graph.add_node("evaluate_step", evaluate_step)
    graph.add_node("fix_code", fix_code)
    graph.add_node("advance_step", advance_step)
    graph.add_node("respond", respond)

    graph.add_edge(START, "prepare_current_step")
    graph.add_edge("prepare_current_step", "read_reference")
    graph.add_edge("read_reference", "plan_and_generate")
    graph.add_edge("plan_and_generate", "validate_generated_code")

    graph.add_conditional_edges(
        "validate_generated_code",
        route_after_validation,
        {
            "save_code": "save_code",
            "evaluate_step": "evaluate_step",
        },
    )

    graph.add_edge("save_code", "generate_pytest")
    graph.add_edge("generate_pytest", "save_pytest")
    graph.add_edge("save_pytest", "run_pytest")
    graph.add_edge("run_pytest", "evaluate_step")

    graph.add_conditional_edges(
        "evaluate_step",
        route_after_evaluate,
        {
            "fix_code": "fix_code",
            "advance_step": "advance_step",
        },
    )

    graph.add_edge("fix_code", "validate_generated_code")

    graph.add_conditional_edges(
        "advance_step",
        route_after_advance,
        {
            "prepare_current_step": "prepare_current_step",
            "respond": "respond",
        },
    )

    graph.add_edge("respond", END)
    return graph.compile()


def _record_step_result(
    state: AgentState,
    result_status: str,
    attempts: int,
) -> dict[str, dict]:
    step = state.get("current_step", "?")
    results = dict(state.get("step_results", {}))
    results[step] = {
        "status": result_status,
        "attempts": attempts,
        "reference_file": state.get("reference_file_path", ""),
        "output_file": state.get("output_file_path", ""),
        "pytest_file": state.get("pytest_file_path", ""),
        "details": state.get("execution_result", ""),
    }
    return results


def _get_llm() -> ChatOpenAI:
    from django.conf import settings

    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.1,
    )


def _clean_code_response(text: str) -> str:
    text = text.strip()

    if text.startswith("```python"):
        text = text[len("```python") :]
    elif text.startswith("```"):
        text = text[len("```") :]

    if text.endswith("```"):
        text = text[: -len("```")]

    return text.strip()


def build_react_agent():
    from django.conf import settings
    from langgraph.prebuilt import create_react_agent

    from agent.tools import get_all_tools

    llm = _get_llm()
    tools = get_all_tools(str(settings.WORKSPACE_DIR))
    prompt = (
        "You are an ETL engineer agent. Read files, write files, and run code when needed."
    )
    return create_react_agent(model=llm, tools=tools, prompt=prompt)
