"""Pub/Sub streaming pull worker for the Grounding Engine."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from .config import settings
from .models import GroundingEventInput, RAGContext, RetrievedChunk

if TYPE_CHECKING:
    from google.cloud.pubsub_v1 import SubscriberClient
    from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture

    from .engine import GroundingEngine
    from .storage import GroundingStorage

logger = logging.getLogger(__name__)


class GroundingWorker:
    """Consumes grounding events from Cloud Pub/Sub and runs them through the engine."""

    def __init__(self, engine: GroundingEngine, storage: GroundingStorage):
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
        logger.info("Grounding worker started: %s", subscription_path)

    def stop(self) -> None:
        if self._future:
            self._future.cancel()
            logger.info("Grounding worker stopped")

    def _callback(self, message) -> None:  # noqa: ANN001
        import asyncio

        try:
            data = json.loads(message.data.decode("utf-8"))
            event = self._parse_event(data)

            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(self._engine.analyze(event))
                loop.run_until_complete(self._storage.store(result))
            finally:
                loop.close()

            message.ack()
            logger.debug("Processed grounding event %s → score %.1f", event.event_id, result.grounding_score)
        except Exception:
            logger.exception("Failed to process grounding message")
            message.nack()

    @staticmethod
    def _parse_event(data: dict) -> GroundingEventInput:
        rag_raw = data.get("rag_context")
        rag_context = None
        if rag_raw and isinstance(rag_raw, dict):
            chunks = [
                RetrievedChunk(
                    id=c.get("id", ""),
                    content=c.get("content", ""),
                    score=c.get("score"),
                )
                for c in rag_raw.get("retrieved_chunks", [])
            ]
            rag_context = RAGContext(
                retrieved_chunks=chunks,
                vector_store_type=rag_raw.get("vector_store_type", ""),
                retrieval_score=rag_raw.get("retrieval_score"),
                query=rag_raw.get("query", ""),
            )

        return GroundingEventInput(
            event_id=data.get("event_id", ""),
            client_id=data.get("client_id", ""),
            agent_id=data.get("agent_id", ""),
            session_id=data.get("session_id", ""),
            prompt=data.get("prompt", ""),
            response=data.get("response", ""),
            model=data.get("model", ""),
            rag_context=rag_context,
            ground_truth=data.get("ground_truth"),
            metadata=data.get("metadata", {}),
        )
