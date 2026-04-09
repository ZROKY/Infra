from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "engine-grounding"
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "info"
    environment: str = "development"

    # GCP Pub/Sub
    gcp_project_id: str = "zroky-dev"
    pubsub_subscription: str = "zroky-dev-grounding-events-sub"

    # Databases
    database_url: str = "postgresql://zroky:zroky@localhost:5432/zroky"
    redis_url: str = "redis://localhost:6379/0"
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "zroky"

    # LLM Judge (vLLM-compatible endpoint for evaluation)
    llm_judge_url: str = "http://localhost:8080/v1/chat/completions"
    llm_judge_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    llm_judge_timeout: float = 5.0

    # Embedding endpoint (for consistency + golden tests)
    embedding_url: str = "http://localhost:8081/v1/embeddings"
    embedding_model: str = "text-embedding-3-small"
    embedding_timeout: float = 3.0

    # Grounding thresholds
    hallucination_critical_rate: float = 0.10  # > 10% in 1h → override
    hallucination_override_penalty: int = 20
    faithfulness_critical: float = 50.0
    retrieval_relevance_alert: float = 75.0
    golden_test_degradation_pct: float = 5.0

    # Score weights (5 sub-dimensions)
    weight_retrieval_quality: float = 0.25
    weight_answer_source_consistency: float = 0.25
    weight_factual_consistency: float = 0.15
    weight_claim_attribution: float = 0.20
    weight_hallucination_metrics: float = 0.15

    model_config = {"env_prefix": "ENGINEGROUNDING_"}


settings = Settings()
