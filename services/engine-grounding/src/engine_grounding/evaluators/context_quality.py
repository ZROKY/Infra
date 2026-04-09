"""Context quality evaluator — precision and recall of retrieved chunks.

Precision: What fraction of retrieved chunks were useful?
Recall: Did retrieval find everything needed to answer?
"""

from __future__ import annotations

import json
import logging
import re

import httpx

from ..config import settings
from ..models import EvaluationResult, EvaluationType

logger = logging.getLogger(__name__)

CONTEXT_QUALITY_PROMPT = """You are evaluating the quality of retrieved context for answering a question.

Question: {question}
AI Response: {response}

Retrieved Context Chunks:
{chunks}

Evaluate TWO metrics:

1. CONTEXT PRECISION: What percentage of the retrieved chunks are actually relevant and useful for answering the question? (0-100)
2. CONTEXT RECALL: Does the retrieved context contain ALL the information needed to fully answer the question? (0-100)

Respond with JSON only:
{{"precision": <0-100>, "recall": <0-100>, "precision_reasoning": "<brief>", "recall_reasoning": "<brief>"}}"""


class ContextQualityEvaluator:
    """Ragas-style context precision and context recall via LLM judge."""

    async def evaluate(
        self,
        question: str,
        response: str,
        source_chunks: list[str],
    ) -> tuple[EvaluationResult, EvaluationResult]:
        """Returns (precision_result, recall_result)."""

        if not source_chunks:
            return (
                EvaluationResult(
                    evaluation_type=EvaluationType.context_precision,
                    score=50.0,
                    confidence=0.2,
                    details={"reason": "no_chunks"},
                ),
                EvaluationResult(
                    evaluation_type=EvaluationType.context_recall,
                    score=50.0,
                    confidence=0.2,
                    details={"reason": "no_chunks"},
                ),
            )

        chunks_text = "\n".join(
            f"[Chunk {i + 1}]: {chunk[:500]}" for i, chunk in enumerate(source_chunks)
        )

        try:
            prompt = CONTEXT_QUALITY_PROMPT.format(
                question=question, response=response, chunks=chunks_text
            )
            result = await self._call_llm(prompt)
            parsed = self._parse_json(result)

            precision = max(0.0, min(100.0, float(parsed.get("precision", 50))))
            recall = max(0.0, min(100.0, float(parsed.get("recall", 50))))

            precision_result = EvaluationResult(
                evaluation_type=EvaluationType.context_precision,
                score=round(precision, 1),
                confidence=0.8,
                details={"reasoning": parsed.get("precision_reasoning", "")},
            )
            recall_result = EvaluationResult(
                evaluation_type=EvaluationType.context_recall,
                score=round(recall, 1),
                confidence=0.8,
                details={"reasoning": parsed.get("recall_reasoning", "")},
            )
            return precision_result, recall_result

        except (httpx.HTTPError, TimeoutError):
            logger.warning("LLM judge unavailable for context quality — using heuristic")
            return self._heuristic_context_quality(question, response, source_chunks)

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
    def _heuristic_context_quality(
        question: str, response: str, source_chunks: list[str]
    ) -> tuple[EvaluationResult, EvaluationResult]:
        """Fallback: word overlap between chunks and response/question."""
        q_words = set(question.lower().split())
        r_words = set(response.lower().split())

        relevant_chunks = 0
        for chunk in source_chunks:
            chunk_words = set(chunk.lower().split())
            q_overlap = len(q_words & chunk_words) / max(len(q_words), 1)
            r_overlap = len(r_words & chunk_words) / max(len(r_words), 1)
            if q_overlap > 0.1 or r_overlap > 0.15:
                relevant_chunks += 1

        precision = (relevant_chunks / len(source_chunks) * 100) if source_chunks else 50.0
        # Recall heuristic: more relevant chunks = better recall
        recall = min(100.0, relevant_chunks * 30.0) if source_chunks else 50.0

        return (
            EvaluationResult(
                evaluation_type=EvaluationType.context_precision,
                score=round(precision, 1),
                confidence=0.3,
                details={"method": "heuristic", "relevant_chunks": relevant_chunks, "total_chunks": len(source_chunks)},
            ),
            EvaluationResult(
                evaluation_type=EvaluationType.context_recall,
                score=round(recall, 1),
                confidence=0.3,
                details={"method": "heuristic", "relevant_chunks": relevant_chunks},
            ),
        )
