"""Shared environment configuration for all Python ML services."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings. Override via .env at the service root."""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Model config
    model_cache_dir: str = "./models"
    sbert_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    scibert_model_name: str = "allenai/scibert_scivocab_uncased"
    sentiment_model_name: str = "bert-base-uncased"
    summarizer_model_name: str = "facebook/bart-large-cnn"

    # HuggingFace
    hf_token: str = ""

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
