#!/usr/bin/env python3
from __future__ import annotations
from .state import AgentState
from langgraph.graph import StateGraph


def build_graph():
    g = StateGraph(AgentState)
    return g.compile()
