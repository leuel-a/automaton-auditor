import json
from pathlib import Path

from src.state import AgentState, RubricMetadata


def _validate(repo_url: str, pdf_path: str) -> bool:
    # !(todo) -> Add validation for the repo_url to be a valid github repository
    # !(todo) -> Add validation for pdf_path to be a valid pdf file
    return True


def _load_rubric_data() -> dict:
    rubric_path = (
        Path(__file__).resolve().parent / "../../rubric/week_2.json"
    ).resolve()

    if not rubric_path.exists():
        raise FileNotFoundError(f"RUBRIC_PATH does not exist: {rubric_path}")

    return json.loads(rubric_path.read_text(encoding="utf-8"))


def context_builder(state: AgentState) -> AgentState:
    if not _validate(state["repo_url"], state["pdf_path"]):
        raise ValueError("Missing repo_url or pdf_path")

    rubric = _load_rubric_data()
    rubric_dimensions = rubric.get("dimensions", [])
    rubric_synthesis_rules = rubric.get("synthesis_rules", {})

    return {
        **state,
        "rubric_meta_data": RubricMetadata(
            name=rubric.get("metadata.name", ""),
            grading_target=rubric.get("metadata.grading_target", ""),
            version=rubric.get("metadata.version", ""),
        ),
        "rubric_dimensions": rubric_dimensions,
        "rubric_synthesis_rules": rubric_synthesis_rules,
    }
