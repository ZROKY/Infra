from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Safety Engine configuration."""

    app_name: str = "engine-safety"
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "info"
    environment: str = "development"

    # GCP
    gcp_project_id: str = "zroky-platform"
    pubsub_subscription: str = "zroky-dev-safety-events-sub"
    pubsub_emulator_host: str = ""

    # Databases
    database_url: str = "postgresql://zroky_app:zroky_dev@localhost:5432/zroky"
    redis_url: str = "redis://localhost:6379/0"
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "zroky"

    # LLM Safety Judge
    llm_judge_url: str = "http://localhost:8010/v1/chat/completions"
    llm_judge_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    llm_judge_timeout: float = 2.0

    # Thresholds
    judge_trigger_min: int = 40
    judge_trigger_max: int = 80
    campaign_threshold: int = 50
    campaign_window_seconds: int = 3600

    model_config = {"env_prefix": "SAFETY_"}


settings = Settings()
