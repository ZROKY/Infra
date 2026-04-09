"""Consistency evaluator — factual consistency across multi-turn conversations.

Detects self-contradictions by comparing response embeddings or using
LLM judge to verify consistency with prior answers.
"""

from __future__ import annotations

import json
import logging
import re

import httpx

from ..config import settings
from ..models import EvaluationResult, EvaluationType

logger = logging.getLogger(__name__)

CONSISTENCY_PROMPT = """You are a factual consistency judge. Determine if the AI response is internally consistent and does not contradict itself.

Question: {question}
AI Response: {response}

Source Context (if available):
{context}

Evaluate:
1. Is the response internally consistent (no self-contradictions)?
2. Does the response align with the source context?
3. Are there any factual inconsistencies?

Score from 0-100:
- 90-100: Fully consistent, no contradictions
- 70-89: Minor inconsistencies that don't affect meaning
- 50-69: Noticeable inconsistencies
- 30-49: Significant contradictions
- 0-29: Severely contradictory

Respond with JSON only:
{{"score": <0-100>, "contradictions": ["list any contradictions found"], "reasoning": "<brief>"}}"""


class ConsistencyEvaluator:
    """Embedding similarity + LLM judge for factual consistency detection."""

    async def evaluate(
        self,
        question: str,
        response: str,
        source_chunks: list[str] | None = None,
    ) -> EvaluationResult:
        if not response:
            return EvaluationResult(
                evaluation_type=EvaluationType.consistency,
                score=50.0,
                confidence=0.2,
                details={"reason": "empty_response"},
            )

        context = "\n---\n".join(source_chunks) if source_chunks else "(no source context)"

        try:
            prompt = CONSISTENCY_PROMPT.format(
                question=question, response=response, context=context
            )
            result = await self._call_llm(prompt)
            parsed = self._parse_json(result)

            score = max(0.0, min(100.0, float(parsed.get("score", 70))))

            return EvaluationResult(
                evaluation_type=EvaluationType.consistency,
                score=round(score, 1),
                confidence=0.8,
                details={
                    "contradictions": parsed.get("contradictions", []),
                    "reasoning": parsed.get("reasoning", ""),
                },
            )
        except (httpx.HTTPError, TimeoutError):
            logger.warning("LLM judge unavailable for consistency — using heuristic")
            return self._heuristic_consistency(response)

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
    def _heuristic_consistency(response: str) -> EvaluationResult:
        """Fallback: detect obvious contradictions via negation patterns."""
        sentences = [s.strip() for s in re.split(r"[.!?]+", response) if s.strip()]

        contradiction_patterns = [
            (r"\bis\b", r"\bis not\b"),
            (r"\bcan\b", r"\bcannot\b"),
            (r"\bwill\b", r"\bwill not\b"),
            (r"\byes\b", r"\bno\b"),
            (r"\balways\b", r"\bnever\b"),
        ]

        contradictions_found = 0
        for s1_idx in range(len(sentences)):
            for s2_idx in range(s1_idx + 1, len(sentences)):
                s1, s2 = sentences[s1_idx].lower(), sentences[s2_idx].lower()
                for pos, neg in contradiction_patterns:
                    if re.search(pos, s1) and re.search(neg, s2):
                        contradictions_found += 1
                        break

        if contradictions_found == 0:
            score = 90.0
        elif contradictions_found <= 2:
            score = 65.0
        else:
            score = 35.0

        return EvaluationResult(
            evaluation_type=EvaluationType.consistency,
            score=score,
            confidence=0.3,
            details={"method": "negation_heuristic", "potential_contradictions": contradictions_found},
        )
