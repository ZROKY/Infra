from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "engine-system"
    host: str = "0.0.0.0"
    port: int = 8004
    log_level: str = "info"
    environment: str = "development"

    # GCP Pub/Sub
    gcp_project_id: str = "zroky-dev"
    pubsub_subscription: str = "zroky-dev-system-events-sub"

    # Databases
    database_url: str = "postgresql://zroky:zroky@localhost:5432/zroky"
    redis_url: str = "redis://localhost:6379/0"
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "zroky"

    # Latency thresholds (ms)
    latency_p50_target: int = 1000
    latency_p95_target: int = 3000
    latency_p99_target: int = 5000

    # Error rate
    error_rate_alert_pct: float = 5.0

    # Uptime
    uptime_target_pct: float = 99.9
    health_check_interval_s: int = 60

    # Throughput
    throughput_capacity_alert_pct: float = 80.0

    # Cost
    daily_cost_budget: float = 100.0
    monthly_cost_budget: float = 3000.0
    cost_alert_thresholds: list[int] = [50, 75, 90, 100]

    # Cost-per-outcome
    waste_ratio_alert_pct: float = 20.0

    # Performance-quality correlation
    correlation_alert_threshold: float = -0.5

    # Score weights (5 primary dimensions)
    weight_latency: float = 0.25
    weight_error_rate: float = 0.20
    weight_cost: float = 0.20
    weight_uptime: float = 0.20
    weight_throughput: float = 0.15

    model_config = {"env_prefix": "ENGINESYSTEM_"}


settings = Settings()
