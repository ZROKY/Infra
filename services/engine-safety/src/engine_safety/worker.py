"""Pub/Sub consumer — subscribes to safety events topic and processes them."""

from __future__ import annotations

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from google.cloud import pubsub_v1

from .config import settings
from .engine import SafetyEngine
from .models import SafetyEventInput
from .storage import SafetyStorage

logger = logging.getLogger(__name__)


class SafetyWorker:
    """
    Pub/Sub pull subscriber for the safety events topic.

    Receives events, runs Safety Engine, stores results.
    Designed for async operation alongside the FastAPI server.
    """

    def __init__(
        self,
        engine: SafetyEngine,
        storage: SafetyStorage,
    ):
        self._engine = engine
        self._storage = storage
        self._subscriber: pubsub_v1.SubscriberClient | None = None
        self._streaming_future = None
        self._executor = ThreadPoolExecutor(max_workers=4)

    def start(self) -> None:
        """Start the Pub/Sub streaming pull subscription."""
        self._subscriber = pubsub_v1.SubscriberClient()
        subscription_path = self._subscriber.subscription_path(
            settings.gcp_project_id,
            settings.pubsub_subscription,
        )

        self._streaming_future = self._subscriber.subscribe(
            subscription_path,
            callback=self._callback,
            flow_control=pubsub_v1.types.FlowControl(max_messages=100),
        )
        logger.info("Safety Worker subscribed to %s", subscription_path)

    def _callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        """Handle a single Pub/Sub message (runs in thread pool)."""
        try:
            data = json.loads(message.data.decode("utf-8"))
            event = SafetyEventInput(**data)

            # Run async engine in event loop
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(self._engine.analyze(event))
                loop.run_until_complete(self._storage.store(result))
            finally:
                loop.close()

            message.ack()
            logger.debug(
                "Processed event %s — score=%d threat=%s",
                event.event_id, result.safety_score, result.threat_level.value,
            )
        except Exception:
            logger.error("Failed to process message", exc_info=True)
            message.nack()

    def stop(self) -> None:
        """Gracefully stop the subscriber."""
        if self._streaming_future:
            self._streaming_future.cancel()
            self._streaming_future.result(timeout=10)
        if self._subscriber:
            self._subscriber.close()
        self._executor.shutdown(wait=False)
        logger.info("Safety Worker stopped")
