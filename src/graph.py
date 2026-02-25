#!/usr/bin/env python3
from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from src.nodes import context_builder, doc_analyst, evidence_aggregator
from src.nodes.detectives import repo_investigator, repo_tools
from src.state import AgentState


def _needs_tools(state: AgentState) -> str:
    msgs = state.get("repo_investigator_messages") or []
    last_ai = next((m for m in reversed(msgs) if isinstance(m, AIMessage)), None)
    tool_calls = getattr(last_ai, "tool_calls", None) if last_ai else None
    return "repo_tools" if tool_calls else "evidence_aggregator"


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("context_builder", context_builder)
    builder.add_node("repo_investigator", repo_investigator)
    builder.add_node("repo_tools", repo_tools)
    builder.add_node("doc_analyst", doc_analyst)
    builder.add_node("evidence_aggregator", evidence_aggregator)

    builder.add_edge(START, "context_builder")
    builder.add_edge("context_builder", "repo_investigator")
    builder.add_edge("context_builder", "doc_analyst")

    # loop without repo_router
    builder.add_conditional_edges(
        "repo_investigator",
        _needs_tools,
        {"repo_tools": "repo_tools", "evidence_aggregator": "evidence_aggregator"},
    )
    builder.add_edge("repo_tools", "repo_investigator")

    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("evidence_aggregator", END)

    return builder.compile()
