#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.graph import build_graph
from src.state import AgentState


@dataclass
class AutomatonAuditorAgent:
    graph: Any

    @classmethod
    def create(cls) -> "AutomatonAuditorAgent":
        graph = build_graph()
        return cls(graph=graph)

    def run(self, github_repo_url: str, pdf_path: str) -> AgentState:
        state: AgentState = {"repo_url": github_repo_url, "pdf_path": pdf_path}
        return self.graph.invoke(state)
