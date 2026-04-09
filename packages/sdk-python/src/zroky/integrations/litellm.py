"""ZROKY LiteLLM integration — auto-reads telemetry from LiteLLM callback system."""

from __future__ import annotations

import time
from typing import Any

from zroky.monitor import ZROKYMonitor


class ZROKYLiteLLMCallback:
    """LiteLLM success/failure callback that auto-sends events to ZROKY.

    Setup:
        import litellm
        from zroky.integrations.litellm import ZROKYLiteLLMCallback
        callback = ZROKYLiteLLMCallback(api_key="zk_ingest_...", agent_id="agent_abc123")
        litellm.success_callback = [callback.on_success]
        litellm.failure_callback = [callback.on_failure]

    Or via env: set ZROKY_API_KEY + ZROKY_AGENT_ID and use auto-setup.
    """

    def __init__(self, api_key: str, agent_id: str, **monitor_kwargs: Any) -> None:
        self._monitor = ZROKYMonitor(api_key=api_key, agent_id=agent_id, **monitor_kwargs)

    def on_success(self, kwargs: dict[str, Any], completion_response: Any, start_time: float, end_time: float) -> None:
        """Called by LiteLLM on successful completion."""
        messages = kwargs.get("messages", [])
        prompt = messages[-1].get("content", "") if messages else ""
        model = kwargs.get("model", "")

        # Extract response text
        response_text = ""
        choices = getattr(completion_response, "choices", None)
        if choices:
            message = getattr(choices[0], "message", None)
            if message:
                response_text = getattr(message, "content", "") or ""

        usage = getattr(completion_response, "usage", None)
        token_meta = {}
        if usage:
            token_meta = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }

        self._monitor.track(
            prompt=prompt,
            response=response_text,
            model=model,
            metadata={
                "source": "litellm",
                "latency_ms": round((end_time - start_time) * 1000, 2),
                **token_meta,
            },
        )

    def on_failure(self, kwargs: dict[str, Any], exception: Exception, start_time: float, end_time: float) -> None:
        """Called by LiteLLM on failure."""
        messages = kwargs.get("messages", [])
        prompt = messages[-1].get("content", "") if messages else ""
        model = kwargs.get("model", "")

        self._monitor.track(
            prompt=prompt,
            response=f"ERROR: {exception}",
            model=model,
            metadata={
                "source": "litellm",
                "error": True,
                "latency_ms": round((end_time - start_time) * 1000, 2),
            },
        )

    def close(self) -> None:
        """Flush and close the underlying monitor."""
        self._monitor.close()
