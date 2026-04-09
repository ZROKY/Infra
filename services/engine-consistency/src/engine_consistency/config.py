from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "engine-consistency"
    host: str = "0.0.0.0"
    port: int = 8003
    log_level: str = "info"
    environment: str = "development"

    model_config = {"env_prefix": "ENGINECONSISTENCY_"}


settings = Settings()
