from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "health-check"
    host: str = "0.0.0.0"
    port: int = 8006
    log_level: str = "info"
    environment: str = "development"

    model_config = {"env_prefix": "HEALTHCHECK_"}


settings = Settings()
