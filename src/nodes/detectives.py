from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.llm_provider import GenericLLMProvider
from src.prompts.prompt_family import PromptFamily
from src.state import AgentState
from src.tools.doc_tools import (
    cross_reference,
    markdown_read,
    pdf_parse_ingest_pdf,
    pdf_parse_query_pdf,
)
from src.tools.repo_tools import ast_parse, file_read, git_clone, git_log

tools = [
    git_clone,
    git_log,
    file_read,
    ast_parse,
    cross_reference,
    markdown_read,
    pdf_parse_ingest_pdf,
    pdf_parse_query_pdf,
]
TOOL_MAP = {tool.name: tool for tool in tools}

model = GenericLLMProvider.from_provider(os.getenv("LLM_PROVIDER", "gemini"))
model_with_tools = model.bind_tools(tools)


def _github_repo_dimensions(state: AgentState) -> List[Dict]:
    dimensions = list(state.get("rubric_dimensions") or [])
    return [
        dimension
        for dimension in dimensions
        if dimension.get("target_artifact") == "github_repo"
    ]


def repo_investigator(state: AgentState) -> AgentState:

    # COMPILE MASTER PROMPT ONCE (CACHE IN STATE)
    get_dimensions_prompt: Optional[str] = state.get("repo_dimensions_prompt")
    if not get_dimensions_prompt:
        dimensions = _github_repo_dimensions(state)
        compiler_msgs = [
            SystemMessage(
                content=PromptFamily.repo_dimensions_compiler_system_prompt()
            ),
            HumanMessage(
                content=json.dumps({"dimensions": dimensions}, ensure_ascii=False)
            ),
        ]

        compiled_ai_message: AIMessage = model.invoke(compiler_msgs)
        get_dimensions_prompt = (compiled_ai_message.content or "").strip()

    # INVESTIGATION STEP (TOOL-CAPABLE)
    repo_investigator_messages = list(state.get("repo_investigator_messages") or [])

    if not repo_investigator_messages:
        repo_investigator_messages = [
            SystemMessage(content=PromptFamily.repo_investigator_system_prompt()),
            HumanMessage(
                content=json.dumps(
                    {
                        "repo_url": state["repo_url"],
                        "repo_path": state.get("repo_path"),
                        "repo_dimensions_prompt": get_dimensions_prompt,
                        "note": "Proceed. If you need tools, emit tool calls. If done, emit final JSON.",
                    },
                    ensure_ascii=False,
                )
            ),
        ]

    ai_message: AIMessage = model_with_tools.invoke(repo_investigator_messages)
    repo_investigator_messages.append(ai_message)

    print(f"AI Message: {ai_message}")
    return {
        **state,
        "repo_dimensions_prompt": get_dimensions_prompt,
        "repo_investigator_messages": repo_investigator_messages,
    }


def repo_tools(state: AgentState) -> AgentState:
    messages = list(state.get("repo_investigator_messages") or [])
    last_message = next(
        (message for message in reversed(messages) if isinstance(message, AIMessage)),
        None,
    )
    if not last_message:
        return state

    repo_path: Optional[str] = state.get("repo_path")
    tool_calls = getattr(last_message, "tool_calls", None) or []

    for tool_call in tool_calls:
        name = tool_call.get("name")
        args = tool_call.get("args", {}) or {}

        if name == "git_clone" and "repo_url" not in args:
            args["repo_url"] = state["repo_url"]

        if name in ("git_log", "file_read") and "repo_path" not in args and repo_path:
            args["repo_path"] = repo_path

        try:
            result = (
                TOOL_MAP[name].invoke(args)
                if name in TOOL_MAP
                else f"ERROR: unknown tool {name}"
            )

            if name == "git_clone" and isinstance(result, str) and result.strip():
                repo_path = result.strip()
        except Exception as e:
            result = f"ERROR: {type(e).__name__}: {e}"

        messages.append(
            ToolMessage(content=str(result), tool_call_id=tool_call.get("id"))
        )

    out_state = {**state, "repo_investigator_messages": messages}
    if repo_path:
        out_state["repo_path"] = repo_path

    return out_state


def _group_evidences(raw: Any) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convert either:
      - list[Evidence] where each item has evidence_class
      - dict[str, list[Evidence]] already grouped
    into dict[str, list[Evidence]] for state["evidences"] (operator.ior friendly).
    """
    if raw is None:
        return {}

    # Already grouped
    if isinstance(raw, dict):
        return raw  # assume correct shape

    grouped: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    if isinstance(raw, list):
        for ev in raw:
            if isinstance(ev, dict):
                cls = ev.get("evidence_class") or ev.get("class") or "Unclassified"
                grouped[str(cls)].append(ev)
            else:
                grouped["Unclassified"].append({"raw": ev})
    else:
        grouped["Unclassified"].append({"raw": raw})

    return dict(grouped)


def _safe_json_load(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        # If the model accidentally returns extra text, attempt to salvage the first JSON object.
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(s[start : end + 1])
        raise


def doc_analyst(state: AgentState) -> Dict[str, Any]:
    master_prompt = state.get("doc_dimensions_prompt")
    if not master_prompt:
        raise ValueError(
            "Missing doc_dimensions_prompt in state. Compile it from rubric_dimensions first."
        )

    # Persist messages across tool loops (same idea as repo_investigator_messages)
    msgs = state.get("doc_analyst_messages") or []
    if not msgs:
        msgs = [
            SystemMessage(content=PromptFamily.doc_analyst_system_prompt()),
            HumanMessage(
                content=json.dumps(
                    {
                        "repo_url": state["repo_url"],
                        "repo_path": state.get("repo_path"),
                        "pdf_path": state["pdf_path"],
                        "pdf_doc_id": state.get("pdf_doc_id"),
                        "master_prompt": master_prompt,
                    },
                    ensure_ascii=False,
                )
            ),
        ]

    # Bind doc tools and invoke
    ai_message: AIMessage = model.invoke(msgs)

    updates: Dict[str, Any] = {"doc_analyst_messages": [ai_message]}

    # If no tool calls, we expect final JSON output
    tool_calls = getattr(ai_message, "tool_calls", None)
    if not tool_calls:
        content = ai_message.content or ""
        data = _safe_json_load(cast(str, content))

        # persist pdf_doc_id if present
        pdf_doc_id = data.get("pdf_doc_id") or data.get("doc_id")
        if pdf_doc_id:
            updates["pdf_doc_id"] = str(pdf_doc_id)

        # merge evidences into state["evidences"]
        grouped = _group_evidences(data.get("evidences"))
        if grouped:
            updates["evidences"] = grouped

    return updates


def doc_tools(state: AgentState) -> Dict[str, Any]:
    messages = state.get("doc_analyst_messages") or []
    last_message = next(
        (
            messages
            for messages in reversed(messages)
            if isinstance(messages, AIMessage)
        ),
        None,
    )
    if not last_message:
        return {}

    tool_calls = getattr(last_message, "tool_calls", None) or []
    tool_messages: List[ToolMessage] = []

    for tool_call in tool_calls:
        name = tool_call.get("name")
        args = tool_call.get("args") or {}
        tool_obj = TOOL_MAP.get(name)
        if tool_obj is None:
            result = f"Unknown tool: {name}"
        else:
            result = tool_obj.invoke(args)

        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call.get("id"),
            )
        )

    return {"doc_analyst_messages": tool_messages}


def vision_inspector(state: AgentState):
    pass
