from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "engine-grounding"
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "info"
    environment: str = "development"

    model_config = {"env_prefix": "ENGINEGROUNDING_"}


settings = Settings()
