from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "trust-computer"
    host: str = "0.0.0.0"
    port: int = 8005
    log_level: str = "info"
    environment: str = "development"

    # Databases
    database_url: str = "postgresql://zroky:zroky@localhost:5432/zroky"
    redis_url: str = "redis://localhost:6379/0"
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "zroky"

    # Engine service URLs (for fetching live scores)
    safety_engine_url: str = "http://localhost:8001"
    grounding_engine_url: str = "http://localhost:8002"
    consistency_engine_url: str = "http://localhost:8003"
    system_engine_url: str = "http://localhost:8004"

    # V1 Trust Score weights
    weight_safety: float = 0.30
    weight_grounding: float = 0.25
    weight_consistency: float = 0.20
    weight_system: float = 0.10
    weight_coverage: float = 0.15

    # Override rules
    safety_floor_threshold: float = 40.0  # Safety < 40 → Trust ≤ 50
    safety_floor_cap: float = 50.0
    critical_incident_penalty: float = 15.0  # Minimum drop for critical incident
    low_coverage_threshold: float = 50.0  # Coverage < 50 → caveat displayed

    # Cold-start thresholds
    cold_start_no_score: int = 10  # 0-9 events → no score
    cold_start_provisional: int = 100  # 10-99 → PROVISIONAL
    cold_start_building: int = 500  # 100-499 → BUILDING, 500+ → STABLE

    # Coverage calculation
    coverage_variance_tolerance: float = 0.80  # Rolling 7-day avg × 0.80

    model_config = {"env_prefix": "TRUSTCOMPUTER_"}


settings = Settings()
