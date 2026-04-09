"""ZROKY REST API client — low-level HTTP wrapper."""

from __future__ import annotations

from typing import Any

import httpx

from zroky import __version__

DEFAULT_BASE_URL = "https://api.zroky.ai"
DEFAULT_INGEST_URL = "https://ingest.zroky.ai"
DEFAULT_TIMEOUT = 10.0


class ApiError(Exception):
    """Raised when the API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"ZROKY API {status_code}: {message}")


class ZrokyClient:
    """Low-level sync/async HTTP client for the ZROKY API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        ingest_url: str = DEFAULT_INGEST_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._ingest_url = ingest_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": f"zroky-python/{__version__}",
            "Content-Type": "application/json",
        }
        self._http = httpx.Client(timeout=timeout, headers=self._headers)

    # -- Ingestion -----------------------------------------------------------

    def send_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Send a single event to the ingestion endpoint."""
        return self._post(f"{self._ingest_url}/v1/events", json=event)

    def send_batch(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Send a batch of events (up to 1,000)."""
        return self._post(f"{self._ingest_url}/v1/events/batch", json={"events": events})

    # -- Query ---------------------------------------------------------------

    def get_trust_score(self, agent_id: str) -> dict[str, Any]:
        """Fetch current Trust Score for an agent."""
        return self._get(f"{self._base_url}/v1/trust-score/{agent_id}")

    def get_trust_score_history(
        self, agent_id: str, period: str = "30d", granularity: str = "1h"
    ) -> dict[str, Any]:
        """Fetch Trust Score history for an agent."""
        return self._get(
            f"{self._base_url}/v1/trust-score/{agent_id}/history",
            params={"period": period, "granularity": granularity},
        )

    def get_incidents(self, agent_id: str | None = None, **kwargs: Any) -> dict[str, Any]:
        """Fetch incidents, optionally filtered by agent_id."""
        params = {k: v for k, v in kwargs.items() if v is not None}
        if agent_id:
            params["agent_id"] = agent_id
        return self._get(f"{self._base_url}/v1/incidents", params=params)

    # -- HTTP helpers --------------------------------------------------------

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self._http.get(url, params=params)
        return self._handle_response(resp)

    def _post(self, url: str, json: Any) -> dict[str, Any]:
        resp = self._http.post(url, json=json)
        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code >= 400:
            raise ApiError(resp.status_code, resp.text)
        return resp.json()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> ZrokyClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
