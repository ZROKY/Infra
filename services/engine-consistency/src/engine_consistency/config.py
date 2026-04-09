from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "engine-consistency"
    host: str = "0.0.0.0"
    port: int = 8003
    log_level: str = "info"
    environment: str = "development"

    # GCP Pub/Sub
    gcp_project_id: str = "zroky-dev"
    pubsub_subscription: str = "zroky-dev-consistency-events-sub"

    # Databases
    database_url: str = "postgresql://zroky:zroky@localhost:5432/zroky"
    redis_url: str = "redis://localhost:6379/0"
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "zroky"

    # Embedding endpoint (for behavioral fingerprinting)
    embedding_url: str = "http://localhost:8081/v1/embeddings"
    embedding_model: str = "text-embedding-3-large"
    embedding_timeout: float = 5.0

    # Drift thresholds (Evidently-style)
    drift_psi_threshold: float = 0.20
    drift_kl_threshold: float = 0.15
    drift_wasserstein_threshold: float = 0.15
    drift_js_threshold: float = 0.15

    # Benchmark / regression
    benchmark_drop_alert_pct: float = 5.0
    fingerprint_delta_threshold: float = 0.10

    # Score weights (5 sub-dimensions)
    weight_benchmark: float = 0.20
    weight_regression: float = 0.25
    weight_drift: float = 0.25
    weight_fingerprint: float = 0.15
    weight_version_tracking: float = 0.15

    # GCP Pub/Sub
    gcp_project_id: str = "zroky-dev"
    pubsub_subscription: str = "zroky-dev-consistency-events-sub"

    # Databases
    database_url: str = "postgresql://zroky:zroky@localhost:5432/zroky"
    redis_url: str = "redis://localhost:6379/0"
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "zroky"

    # Embedding endpoint (for behavioral fingerprinting)
    embedding_url: str = "http://localhost:8081/v1/embeddings"
    embedding_model: str = "text-embedding-3-large"
    embedding_timeout: float = 5.0

    # Drift thresholds (Evidently-style)
    drift_psi_threshold: float = 0.20
    drift_kl_threshold: float = 0.15
    drift_wasserstein_threshold: float = 0.15
    drift_js_threshold: float = 0.15

    # Benchmark / regression
    benchmark_drop_alert_pct: float = 5.0
    fingerprint_delta_threshold: float = 0.10

    # Score weights (5 sub-dimensions)
    weight_benchmark: float = 0.20
    weight_regression: float = 0.25
    weight_drift: float = 0.25
    weight_fingerprint: float = 0.15
    weight_version_tracking: float = 0.15

    model_config = {"env_prefix": "ENGINECONSISTENCY_"}


settings = Settings()
