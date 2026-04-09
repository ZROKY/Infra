from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "trust-computer"
    host: str = "0.0.0.0"
    port: int = 8005
    log_level: str = "info"
    environment: str = "development"

    model_config = {"env_prefix": "TRUSTCOMPUTER_"}


settings = Settings()
