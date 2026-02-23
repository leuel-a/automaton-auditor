#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict

from .graph.builder import build_graph
from .graph.state import AgentState


@dataclass
class AutomatonAuditorAgent:
    """
    High-level wrapper around a LangGraph workflow.

    This class encapsulates the graph construction and execution logic,
    providing a simple interface for:
    """

    graph: Any  # TODO: Replace `Any` with the concrete LangGraph type.

    @classmethod
    def create(cls) -> "AutomatonAuditorAgent":
        """
        Factory method that builds the underlying LangGraph instance
        and returns a ready-to-use agent.

        Returns:
            AutomatonAuditorAgent: An initialized agent instance.
        """
        graph = build_graph()
        return cls(graph=graph)

    def run(self, user_message: str) -> AgentState:
        """
        Executes the graph synchronously.

        Args:
            user_message (str): The input message from the user.

        Returns:
            AgentState: The final state produced by the graph execution.
        """
        state: AgentState = {
            "user_message": user_message,
        }
        return self.graph.invoke(state)

    async def arun(self, user_message: str) -> AgentState:
        """
        Executes the graph asynchronously.
        This method is suitable for async frameworks such as FastAPI.

        Args:
            user_message (str): The input message from the user.

        Returns:
            AgentState: The final state produced by the graph execution.
        """
        state: AgentState = {"user_message": user_message}
        return await self.graph.ainvoke(state)

    async def astream(self, user_message: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Streams execution events from the graph asynchronously.

        Useful for:
        - Server-Sent Events (SSE)
        - WebSocket streaming
        - Incremental UI updates

        Args:
            user_message (str): The input message from the user.

        Yields:
            Dict[str, Any]: Individual graph execution events.
        """
        state: AgentState = {"user_message": user_message}

        async for event in self.graph.astream_events(state):
            yield event
