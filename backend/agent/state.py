from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    task: str
    new_fields: list[str]

    extract_ref_path: str
    transform_ref_path: str
    load_ref_path: str

    user_id: str
    campaign_id: str
    output_dir: str

    step_order: list[str]
    current_step_index: int
    current_step: str

    reference_file_path: str
    reference_code: str

    output_file_path: str
    pytest_file_path: str

    generated_code: str
    generated_test_code: str

    validation_ok: bool
    test_exit_code: int
    execution_result: str

    step_results: dict[str, dict]

    error_count: int
    max_retries: int

    status: Literal[
        "preparing",
        "reading",
        "generating",
        "validating",
        "saving",
        "testing",
        "evaluating",
        "fixing",
        "advancing",
        "done",
        "failed",
    ]
