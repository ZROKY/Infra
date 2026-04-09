"""Answer relevancy evaluator — does the response actually answer the question?

Uses LLM judge to assess semantic alignment between query and response.
"""

from __future__ import annotations

import json
import logging
import re

import httpx

from ..config import settings
from ..models import EvaluationResult, EvaluationType

logger = logging.getLogger(__name__)

RELEVANCY_PROMPT = """You are an answer relevancy judge. Rate how well the AI response answers the user's question.

Question: {question}

Response: {response}

Score from 0-100:
- 90-100: Directly and completely answers the question
- 70-89: Mostly answers the question with minor gaps
- 50-69: Partially answers but missing key parts
- 30-49: Loosely related but doesn't really answer
- 0-29: Completely off-topic or irrelevant

Respond with JSON only:
{{"score": <number>, "reasoning": "<brief explanation>"}}"""


class AnswerRelevancyEvaluator:
    """Ragas-style answer relevancy scoring via LLM judge."""

    async def evaluate(self, question: str, response: str) -> EvaluationResult:
        if not question or not response:
            return EvaluationResult(
                evaluation_type=EvaluationType.answer_relevancy,
                score=50.0,
                confidence=0.2,
                details={"reason": "missing_question_or_response"},
            )

        try:
            prompt = RELEVANCY_PROMPT.format(question=question, response=response)
            result = await self._call_llm(prompt)
            parsed = self._parse_json(result)

            score = float(parsed.get("score", 50))
            score = max(0.0, min(100.0, score))

            return EvaluationResult(
                evaluation_type=EvaluationType.answer_relevancy,
                score=round(score, 1),
                confidence=0.85,
                details={"reasoning": parsed.get("reasoning", "")},
            )
        except (httpx.HTTPError, TimeoutError):
            logger.warning("LLM judge unavailable for answer relevancy — using heuristic")
            return self._heuristic_relevancy(question, response)

    @staticmethod
    async def _call_llm(prompt: str) -> str:
        async with httpx.AsyncClient(timeout=settings.llm_judge_timeout) as client:
            resp = await client.post(
                settings.llm_judge_url,
                json={
                    "model": settings.llm_judge_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 512,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_json(text: str) -> dict:
        text = text.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                pass
        return {}

    @staticmethod
    def _heuristic_relevancy(question: str, response: str) -> EvaluationResult:
        """Fallback: keyword overlap between question and response."""
        q_words = set(question.lower().split()) - {"the", "a", "an", "is", "are", "what", "how", "when", "where", "why", "do", "does", "can", "could"}
        r_words = set(response.lower().split())

        if not q_words:
            return EvaluationResult(
                evaluation_type=EvaluationType.answer_relevancy, score=50.0, confidence=0.2
            )

        overlap = len(q_words & r_words) / len(q_words)
        # Higher overlap = more likely relevant, but cap confidence
        score = min(100.0, overlap * 110)

        return EvaluationResult(
            evaluation_type=EvaluationType.answer_relevancy,
            score=round(score, 1),
            confidence=0.3,
            details={"method": "keyword_overlap", "overlap_ratio": round(overlap, 3)},
        )
