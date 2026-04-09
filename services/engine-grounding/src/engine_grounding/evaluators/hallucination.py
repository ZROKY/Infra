"""Hallucination evaluator — DeepEval-style hallucination rate detection.

Determines what percentage of the response is fabricated (not in sources).
"""

from __future__ import annotations

import json
import logging
import re

import httpx

from ..config import settings
from ..models import EvaluationResult, EvaluationType

logger = logging.getLogger(__name__)

HALLUCINATION_PROMPT = """You are a hallucination detection judge. Analyze the AI response and determine what percentage is fabricated (not supported by the source context).

Source context:
{context}

AI response:
{response}

Evaluate:
1. hallucination_rate: What percentage of the response content is NOT supported by the source? (0-100, where 0 = no hallucination, 100 = entirely fabricated)
2. contextual_relevancy: Is the response relevant to the source context? (0-100)
3. answer_correctness: Overall correctness combining semantic and factual accuracy (0-100)

Respond with JSON only:
{{"hallucination_rate": <0-100>, "contextual_relevancy": <0-100>, "answer_correctness": <0-100>, "fabricated_claims": ["list of fabricated statements if any"]}}"""

HALLUCINATION_NO_CONTEXT_PROMPT = """You are a hallucination detection judge. Without source context, evaluate the AI response for internal consistency and plausibility.

Question: {question}
AI response: {response}

Evaluate:
1. contextual_relevancy: Is the response relevant to the question? (0-100)
2. answer_correctness: Does the response seem factually plausible? (0-100)

Respond with JSON only:
{{"contextual_relevancy": <0-100>, "answer_correctness": <0-100>, "reasoning": "<brief>"}}"""


class HallucinationEvaluator:
    """DeepEval-style hallucination rate, contextual relevancy, and answer correctness."""

    async def evaluate(
        self,
        question: str,
        response: str,
        source_chunks: list[str],
    ) -> EvaluationResult:
        if source_chunks:
            return await self._evaluate_with_context(response, source_chunks)
        return await self._evaluate_without_context(question, response)

    async def _evaluate_with_context(
        self, response: str, source_chunks: list[str]
    ) -> EvaluationResult:
        context = "\n---\n".join(source_chunks)

        try:
            prompt = HALLUCINATION_PROMPT.format(context=context, response=response)
            result = await self._call_llm(prompt)
            parsed = self._parse_json(result)

            hallucination_rate = max(0.0, min(100.0, float(parsed.get("hallucination_rate", 20))))
            contextual_relevancy = max(0.0, min(100.0, float(parsed.get("contextual_relevancy", 70))))
            answer_correctness = max(0.0, min(100.0, float(parsed.get("answer_correctness", 70))))

            # Score = inverted hallucination rate (lower hallucination = higher score)
            score = 100.0 - hallucination_rate

            return EvaluationResult(
                evaluation_type=EvaluationType.hallucination,
                score=round(score, 1),
                confidence=0.85,
                details={
                    "hallucination_rate": round(hallucination_rate, 1),
                    "contextual_relevancy": round(contextual_relevancy, 1),
                    "answer_correctness": round(answer_correctness, 1),
                    "fabricated_claims": parsed.get("fabricated_claims", [])[:5],
                },
            )
        except (httpx.HTTPError, TimeoutError):
            logger.warning("LLM judge unavailable for hallucination — using heuristic")
            return self._heuristic_hallucination(response, source_chunks)

    async def _evaluate_without_context(self, question: str, response: str) -> EvaluationResult:
        try:
            prompt = HALLUCINATION_NO_CONTEXT_PROMPT.format(question=question, response=response)
            result = await self._call_llm(prompt)
            parsed = self._parse_json(result)

            contextual_relevancy = max(0.0, min(100.0, float(parsed.get("contextual_relevancy", 70))))
            answer_correctness = max(0.0, min(100.0, float(parsed.get("answer_correctness", 70))))

            # Without context, we can't measure hallucination rate directly
            score = (contextual_relevancy + answer_correctness) / 2

            return EvaluationResult(
                evaluation_type=EvaluationType.hallucination,
                score=round(score, 1),
                confidence=0.5,
                details={
                    "hallucination_rate": None,
                    "contextual_relevancy": round(contextual_relevancy, 1),
                    "answer_correctness": round(answer_correctness, 1),
                    "method": "no_context_evaluation",
                },
            )
        except (httpx.HTTPError, TimeoutError):
            return EvaluationResult(
                evaluation_type=EvaluationType.hallucination,
                score=65.0,
                confidence=0.2,
                details={"method": "default_no_judge"},
            )

    @staticmethod
    async def _call_llm(prompt: str) -> str:
        async with httpx.AsyncClient(timeout=settings.llm_judge_timeout) as client:
            resp = await client.post(
                settings.llm_judge_url,
                json={
                    "model": settings.llm_judge_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 1024,
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
    def _heuristic_hallucination(response: str, source_chunks: list[str]) -> EvaluationResult:
        """Fallback: word overlap to estimate grounding."""
        r_words = set(response.lower().split())
        source_text = " ".join(source_chunks).lower()
        s_words = set(source_text.split())

        if not r_words:
            return EvaluationResult(
                evaluation_type=EvaluationType.hallucination, score=50.0, confidence=0.2
            )

        grounded_ratio = len(r_words & s_words) / len(r_words)
        # Invert: higher grounding = higher score
        score = min(100.0, grounded_ratio * 120)

        return EvaluationResult(
            evaluation_type=EvaluationType.hallucination,
            score=round(score, 1),
            confidence=0.3,
            details={
                "method": "word_overlap_heuristic",
                "grounded_ratio": round(grounded_ratio, 3),
                "hallucination_rate": round((1 - grounded_ratio) * 100, 1),
            },
        )
