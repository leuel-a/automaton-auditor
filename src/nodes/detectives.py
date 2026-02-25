from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.llm_provider import GenericLLMProvider
from src.prompts.prompt_family import PromptFamily
from src.state import AgentState
from src.tools.repo_tools import ast_parse, file_read, git_clone, git_log

tools = [git_clone, git_log, file_read, ast_parse]
TOOL_MAP = {tool.name: tool for tool in tools}


def _github_repo_dimensions(state: AgentState) -> List[Dict]:
    dimensions = list(state.get("rubric_dimensions") or [])
    return [
        dimension
        for dimension in dimensions
        if dimension.get("target_artifact") == "github_repo"
    ]


def repo_investigator(state: AgentState) -> AgentState:
    model = GenericLLMProvider.from_provider(os.getenv("LLM_PROVIDER", "gemini"))
    model_with_tools = model.bind_tools(tools)

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

        messages.append(ToolMessage(content=str(result), tool_call_id=tool_call.get("id")))

    out_state = {**state, "repo_investigator_messages": messages}
    if repo_path:
        out_state["repo_path"] = repo_path

    return out_state


def doc_analyst(state: AgentState):
    pass


def vision_inspector(state: AgentState):
    pass
