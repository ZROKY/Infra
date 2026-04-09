from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "engine-system"
    host: str = "0.0.0.0"
    port: int = 8004
    log_level: str = "info"
    environment: str = "development"

    model_config = {"env_prefix": "ENGINESYSTEM_"}


settings = Settings()
