"""Pub/Sub streaming pull worker for the Consistency Engine."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from .config import settings
from .models import ConsistencyEventInput

if TYPE_CHECKING:
    from google.cloud.pubsub_v1 import SubscriberClient
    from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture

    from .engine import ConsistencyEngine
    from .storage import ConsistencyStorage

logger = logging.getLogger(__name__)


class ConsistencyWorker:
    """Consumes consistency events from Cloud Pub/Sub."""

    def __init__(self, engine: ConsistencyEngine, storage: ConsistencyStorage):
        self._engine = engine
        self._storage = storage
        self._subscriber: SubscriberClient | None = None
        self._future: StreamingPullFuture | None = None

    def start(self) -> None:
        from google.cloud import pubsub_v1

        self._subscriber = pubsub_v1.SubscriberClient()
        subscription_path = self._subscriber.subscription_path(
            settings.gcp_project_id, settings.pubsub_subscription
        )
        flow_control = pubsub_v1.types.FlowControl(max_messages=100)
        self._future = self._subscriber.subscribe(
            subscription_path, callback=self._callback, flow_control=flow_control
        )
        logger.info("Consistency worker started: %s", subscription_path)

    def stop(self) -> None:
        if self._future:
            self._future.cancel()
            logger.info("Consistency worker stopped")

    def _callback(self, message) -> None:  # noqa: ANN001
        import asyncio

        try:
            data = json.loads(message.data.decode("utf-8"))
            event = ConsistencyEventInput(
                event_id=data.get("event_id", ""),
                client_id=data.get("client_id", ""),
                agent_id=data.get("agent_id", ""),
                session_id=data.get("session_id", ""),
                prompt=data.get("prompt", ""),
                response=data.get("response", ""),
                model=data.get("model", ""),
                model_version_str=data.get("model_version_str", ""),
                prompt_tokens=data.get("prompt_tokens", 0),
                completion_tokens=data.get("completion_tokens", 0),
                latency_ms=data.get("latency_ms", 0),
                metadata=data.get("metadata", {}),
            )

            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(self._engine.analyze(event))
                loop.run_until_complete(self._storage.store(result))
            finally:
                loop.close()

            message.ack()
            logger.debug("Processed consistency event %s → score %.1f", event.event_id, result.consistency_score)
        except Exception:
            logger.exception("Failed to process consistency message")
            message.nack()
