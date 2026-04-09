"""ZROKY LangGraph wrapper — monitors graph execution with node-level granularity."""

from __future__ import annotations

import time
from typing import Any

from zroky.monitor import ZROKYMonitor


class ZROKYGraph:
    """Wraps a LangGraph CompiledGraph to auto-send events for each node execution.

    Usage:
        from zroky.integrations.langgraph import ZROKYGraph
        monitored = ZROKYGraph(graph, api_key="zk_ingest_...", agent_id="agent_abc123")
        result = monitored.invoke(input)
    """

    def __init__(self, graph: Any, api_key: str, agent_id: str, **monitor_kwargs: Any) -> None:
        self._graph = graph
        self._monitor = ZROKYMonitor(api_key=api_key, agent_id=agent_id, **monitor_kwargs)

    def invoke(self, input_data: Any, config: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """Invoke the graph and track execution."""
        start = time.time()

        # Use stream to capture node-level events
        final_state = None
        events: list[dict[str, Any]] = []

        try:
            for event in self._graph.stream(input_data, config=config, **kwargs):
                for node_name, node_output in event.items():
                    events.append({"node": node_name, "output_keys": list(node_output.keys()) if isinstance(node_output, dict) else []})
                final_state = event
        except Exception as e:
            self._monitor.track(
                prompt=str(input_data),
                response=f"ERROR: {e}",
                metadata={
                    "source": "langgraph",
                    "error": True,
                    "latency_ms": round((time.time() - start) * 1000, 2),
                },
            )
            raise

        latency_ms = round((time.time() - start) * 1000, 2)

        self._monitor.track(
            prompt=str(input_data),
            response=str(final_state) if final_state else "",
            metadata={
                "source": "langgraph",
                "latency_ms": latency_ms,
                "nodes_executed": [e["node"] for e in events],
                "node_count": len(events),
            },
        )

        return final_state

    async def ainvoke(self, input_data: Any, config: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """Async invoke the graph and track execution."""
        start = time.time()
        final_state = None
        events: list[dict[str, Any]] = []

        try:
            async for event in self._graph.astream(input_data, config=config, **kwargs):
                for node_name, node_output in event.items():
                    events.append({"node": node_name, "output_keys": list(node_output.keys()) if isinstance(node_output, dict) else []})
                final_state = event
        except Exception as e:
            self._monitor.track(
                prompt=str(input_data),
                response=f"ERROR: {e}",
                metadata={"source": "langgraph", "error": True, "latency_ms": round((time.time() - start) * 1000, 2)},
            )
            raise

        self._monitor.track(
            prompt=str(input_data),
            response=str(final_state) if final_state else "",
            metadata={
                "source": "langgraph",
                "latency_ms": round((time.time() - start) * 1000, 2),
                "nodes_executed": [e["node"] for e in events],
                "node_count": len(events),
            },
        )

        return final_state

    def close(self) -> None:
        """Flush and close the underlying monitor."""
        self._monitor.close()
