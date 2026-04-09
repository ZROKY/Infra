"""Tests for ZROKY LangChain integration."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch
from uuid import uuid4

from zroky.integrations.langchain import ZROKYCallbackHandler


class TestZROKYCallbackHandler:
    def test_on_llm_start_and_end(self) -> None:
        handler = ZROKYCallbackHandler(api_key="zk_test_123", agent_id="test")
        run_id = uuid4()
        serialized = {"kwargs": {"model_name": "gpt-4"}, "id": ["ChatOpenAI"]}

        handler.on_llm_start(serialized, ["What is AI?"], run_id=run_id)
        assert run_id in handler._run_starts

        # Mock LLM response
        response = MagicMock()
        gen = MagicMock()
        gen.text = "AI is artificial intelligence"
        response.generations = [[gen]]
        response.llm_output = {}

        with patch.object(handler._monitor, "track") as mock_track:
            handler.on_llm_end(response, run_id=run_id)
            mock_track.assert_called_once()
            call_kwargs = mock_track.call_args
            assert call_kwargs.kwargs["prompt"] == "What is AI?"
            assert call_kwargs.kwargs["response"] == "AI is artificial intelligence"
            assert call_kwargs.kwargs["model"] == "gpt-4"

        handler._monitor._closed = True

    def test_on_llm_error(self) -> None:
        handler = ZROKYCallbackHandler(api_key="zk_test_123", agent_id="test")
        run_id = uuid4()
        handler.on_llm_start({"id": ["gpt-4"]}, ["test prompt"], run_id=run_id)

        with patch.object(handler._monitor, "track") as mock_track:
            handler.on_llm_error(RuntimeError("timeout"), run_id=run_id)
            mock_track.assert_called_once()
            call_kwargs = mock_track.call_args
            assert "ERROR" in call_kwargs.kwargs["response"]

        handler._monitor._closed = True

    def test_unknown_run_id_ignored(self) -> None:
        handler = ZROKYCallbackHandler(api_key="zk_test_123", agent_id="test")
        response = MagicMock()
        response.generations = [[MagicMock(text="hello")]]

        with patch.object(handler._monitor, "track") as mock_track:
            handler.on_llm_end(response, run_id=uuid4())
            mock_track.assert_not_called()

        handler._monitor._closed = True
