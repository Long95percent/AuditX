from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUDITX_", env_file=".env", extra="ignore")

    env: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8765
    storage_dir: str = ".data"
    llm_provider: str = "none"
    llm_model: str = ""
    llm_api_key: str = ""
    ocr_provider: str = "none"


def get_settings() -> Settings:
    return Settings()
