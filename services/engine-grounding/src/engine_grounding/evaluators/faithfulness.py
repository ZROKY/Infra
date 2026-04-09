"""Faithfulness evaluator — claim-level attribution via LLM judge (Ragas-style).

Breaks response into individual claims, checks each against source chunks,
and scores the ratio of supported claims to total claims.
"""

from __future__ import annotations

import json
import logging
import re

import httpx

from ..config import settings
from ..models import EvaluationResult, EvaluationType

logger = logging.getLogger(__name__)

CLAIM_EXTRACTION_PROMPT = """Extract all factual claims from the following AI response as a JSON array of strings.
Each claim should be a single, atomic factual statement.

Response:
{response}

Return ONLY a JSON array. Example: ["claim 1", "claim 2"]"""

CLAIM_VERIFICATION_PROMPT = """You are a grounding verification judge. For each claim, determine if it is SUPPORTED or UNSUPPORTED by the source context.

Source context:
{context}

Claims to verify:
{claims}

For each claim, respond with a JSON array of objects:
[{{"claim": "...", "verdict": "supported" or "unsupported", "evidence": "brief quote or reason"}}]

Return ONLY the JSON array."""


class FaithfulnessEvaluator:
    """Ragas-style faithfulness: supported_claims / total_claims × 100."""

    async def evaluate(
        self,
        response: str,
        source_chunks: list[str],
    ) -> EvaluationResult:
        if not source_chunks:
            return EvaluationResult(
                evaluation_type=EvaluationType.faithfulness,
                score=50.0,
                confidence=0.3,
                details={"reason": "no_source_chunks_provided"},
            )

        context = "\n---\n".join(source_chunks)

        try:
            claims = await self._extract_claims(response)
            if not claims:
                return EvaluationResult(
                    evaluation_type=EvaluationType.faithfulness,
                    score=75.0,
                    confidence=0.5,
                    details={"reason": "no_claims_extracted"},
                )

            verdicts = await self._verify_claims(claims, context)
            supported = sum(1 for v in verdicts if v.get("verdict") == "supported")
            total = len(verdicts) if verdicts else len(claims)
            score = (supported / total) * 100 if total > 0 else 50.0

            return EvaluationResult(
                evaluation_type=EvaluationType.faithfulness,
                score=round(score, 1),
                confidence=0.85,
                details={
                    "total_claims": total,
                    "supported_claims": supported,
                    "unsupported_claims": total - supported,
                    "verdicts": verdicts[:10],  # Cap details for storage
                },
            )
        except (httpx.HTTPError, TimeoutError):
            logger.warning("LLM judge unavailable for faithfulness — using heuristic")
            return self._heuristic_faithfulness(response, source_chunks)

    async def _extract_claims(self, response: str) -> list[str]:
        prompt = CLAIM_EXTRACTION_PROMPT.format(response=response)
        result = await self._call_llm(prompt)
        return self._parse_json_array(result)

    async def _verify_claims(self, claims: list[str], context: str) -> list[dict]:
        claims_text = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(claims))
        prompt = CLAIM_VERIFICATION_PROMPT.format(context=context, claims=claims_text)
        result = await self._call_llm(prompt)
        parsed = self._parse_json_array(result)
        if parsed and isinstance(parsed[0], dict):
            return parsed
        return [{"claim": c, "verdict": "unsupported", "evidence": ""} for c in claims]

    @staticmethod
    async def _call_llm(prompt: str) -> str:
        async with httpx.AsyncClient(timeout=settings.llm_judge_timeout) as client:
            resp = await client.post(
                settings.llm_judge_url,
                json={
                    "model": settings.llm_judge_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 2048,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_json_array(text: str) -> list:
        text = text.strip()
        # Strip markdown fences
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()
        # Find JSON array
        bracket_match = re.search(r"\[[\s\S]*\]", text)
        if bracket_match:
            try:
                return json.loads(bracket_match.group())
            except json.JSONDecodeError:
                pass
        return []

    @staticmethod
    def _heuristic_faithfulness(response: str, source_chunks: list[str]) -> EvaluationResult:
        """Fallback: word overlap heuristic when LLM judge is unavailable."""
        response_words = set(response.lower().split())
        source_text = " ".join(source_chunks).lower()
        source_words = set(source_text.split())

        if not response_words:
            return EvaluationResult(
                evaluation_type=EvaluationType.faithfulness, score=50.0, confidence=0.2
            )

        overlap = len(response_words & source_words) / len(response_words)
        score = min(100.0, overlap * 120)  # Scale up: 83% overlap → 100 score

        return EvaluationResult(
            evaluation_type=EvaluationType.faithfulness,
            score=round(score, 1),
            confidence=0.4,
            details={"method": "word_overlap_heuristic", "overlap_ratio": round(overlap, 3)},
        )
