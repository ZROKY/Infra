"""Pydantic models for the Grounding Engine."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────


class GroundingLevel(StrEnum):
    excellent = "excellent"  # 90-100
    good = "good"  # 70-89
    degraded = "degraded"  # 50-69
    poor = "poor"  # 30-49
    critical = "critical"  # 0-29


class EvaluationType(StrEnum):
    faithfulness = "faithfulness"
    answer_relevancy = "answer_relevancy"
    context_precision = "context_precision"
    context_recall = "context_recall"
    hallucination = "hallucination"
    consistency = "consistency"
    golden_test = "golden_test"
    retrieval_quality = "retrieval_quality"


# ── Input Models ───────────────────────────────────────────────────────


class RetrievedChunk(BaseModel):
    id: str = ""
    content: str = ""
    score: float | None = None


class RAGContext(BaseModel):
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    vector_store_type: str = ""
    retrieval_score: float | None = None
    query: str = ""


class GroundingEventInput(BaseModel):
    event_id: str = ""
    client_id: str = ""
    agent_id: str = ""
    session_id: str = ""
    prompt: str = ""
    response: str = ""
    model: str = ""
    rag_context: RAGContext | None = None
    ground_truth: str | None = None  # For golden test evaluation
    metadata: dict = Field(default_factory=dict)


# ── Evaluation Result Models ───────────────────────────────────────────


class EvaluationResult(BaseModel):
    evaluation_type: EvaluationType
    score: float = 0.0  # 0-100
    confidence: float = 1.0  # 0-1
    details: dict = Field(default_factory=dict)


class RagasMetrics(BaseModel):
    faithfulness: float = 0.0  # 0-100
    answer_relevancy: float = 0.0  # 0-100
    context_precision: float = 0.0  # 0-100
    context_recall: float = 0.0  # 0-100


class DeepEvalMetrics(BaseModel):
    hallucination_rate: float = 0.0  # 0-100 (percentage hallucinated)
    contextual_relevancy: float = 0.0  # 0-100
    answer_correctness: float = 0.0  # 0-100


class GroundingDetails(BaseModel):
    retrieval_relevance: float = 0.0
    faithfulness_score: float = 0.0
    answer_relevancy: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    hallucination_rate: float = 0.0
    contextual_relevancy: float = 0.0
    answer_correctness: float = 0.0
    golden_test_score: float | None = None
    vector_db_distance: float | None = None
    ragas_evaluation: RagasMetrics = Field(default_factory=RagasMetrics)
    deepeval_evaluation: DeepEvalMetrics = Field(default_factory=DeepEvalMetrics)
    evaluation_latency_ms: int = 0
    vector_db_type: str = ""


# ── Engine Output ──────────────────────────────────────────────────────


class GroundingEngineResult(BaseModel):
    event_id: str = ""
    client_id: str = ""
    agent_id: str = ""
    grounding_score: float = 0.0  # 0-100 final score
    grounding_level: GroundingLevel = GroundingLevel.good
    evaluations: list[EvaluationResult] = Field(default_factory=list)
    details: GroundingDetails = Field(default_factory=GroundingDetails)
    has_rag_context: bool = False
    hallucination_override_applied: bool = False
