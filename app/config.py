from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Lexflow"
    database_url: str = "sqlite:///./lexflow.db"
    secret_key: str = "dev-only-secret-change-me"
    access_token_expire_minutes: int = 480
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 120
    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 10
    max_document_chars: int = 60000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
