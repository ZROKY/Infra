from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Safety Engine configuration."""

    app_name: str = "engine-safety"
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "info"
    environment: str = "development"

    model_config = {"env_prefix": "SAFETY_"}


settings = Settings()
