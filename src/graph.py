#!/usr/bin/env python3
from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from src.nodes import context_builder, doc_analyst, evidence_aggregator
from src.nodes.detectives import doc_analyst, doc_tools, repo_investigator, repo_tools
from src.state import AgentState


def _needs_tools_repo_investigator(state: AgentState) -> str:
    messages = state.get("repo_investigator_messages") or []
    last_message = next(
        (message for message in reversed(messages) if isinstance(message, AIMessage)),
        None,
    )

    tool_calls = getattr(last_message, "tool_calls", None) if last_message else None
    return "repo_tools" if tool_calls else "evidence_aggregator"


def _needs_doc_tools(state: AgentState) -> str:
    messages = state.get("doc_analyst_messages") or []
    last_message = next(
        (message for message in reversed(messages) if isinstance(message, AIMessage)),
        None,
    )

    tool_calls = getattr(last_message, "tool_calls", None) if last_message else None
    return "doc_tools" if tool_calls else "evidence_aggregator"


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

    builder.add_conditional_edges(
        "repo_investigator",
        _needs_tools_repo_investigator,
        {"repo_tools": "repo_tools", "evidence_aggregator": "evidence_aggregator"},
    )
    builder.add_edge("repo_tools", "repo_investigator")

    builder.add_conditional_edges(
        "doc_analyst",
        _needs_doc_tools,
        {"doc_tools": "doc_tools", "evidence_aggregator": "evidence_aggregator"},
    )
    builder.add_edge("doc_tools", "doc_analyst")

    builder.add_edge("evidence_aggregator", END)
    return builder.compile()
