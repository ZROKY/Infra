"""ZROKY LangChain callback handler — auto-captures prompt, response, model, latency, tokens."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from zroky.monitor import ZROKYMonitor

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    # Graceful degradation if langchain is not installed
    class BaseCallbackHandler:  # type: ignore[no-redef]
        """Stub when langchain is not installed."""


class ZROKYCallbackHandler(BaseCallbackHandler):
    """LangChain callback that sends AI interaction events to ZROKY.

    Usage:
        from zroky.integrations.langchain import ZROKYCallbackHandler
        handler = ZROKYCallbackHandler(api_key="zk_ingest_...", agent_id="agent_abc123")
        result = chain.invoke(input, config={"callbacks": [handler]})
    """

    def __init__(self, api_key: str, agent_id: str, **monitor_kwargs: Any) -> None:
        super().__init__()
        self._monitor = ZROKYMonitor(api_key=api_key, agent_id=agent_id, **monitor_kwargs)
        self._run_starts: dict[UUID, dict[str, Any]] = {}

    def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], *, run_id: UUID, **kwargs: Any
    ) -> None:
        model = serialized.get("kwargs", {}).get("model_name", "") or serialized.get("id", [""])[-1]
        self._run_starts[run_id] = {
            "prompt": prompts[0] if prompts else "",
            "model": model,
            "start_time": time.time(),
        }

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        start = self._run_starts.pop(run_id, None)
        if not start:
            return

        generations = getattr(response, "generations", [[]])
        text = generations[0][0].text if generations and generations[0] else ""
        token_usage = getattr(response, "llm_output", {}) or {}

        self._monitor.track(
            prompt=start["prompt"],
            response=text,
            model=start.get("model", ""),
            metadata={
                "latency_ms": round((time.time() - start["start_time"]) * 1000, 2),
                "source": "langchain",
                **({k: v for k, v in token_usage.items() if k in ("token_usage",)}),
            },
        )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        start = self._run_starts.pop(run_id, None)
        if start:
            self._monitor.track(
                prompt=start["prompt"],
                response=f"ERROR: {error}",
                model=start.get("model", ""),
                metadata={"error": True, "source": "langchain"},
            )

    def close(self) -> None:
        """Flush and close the underlying monitor."""
        self._monitor.close()
