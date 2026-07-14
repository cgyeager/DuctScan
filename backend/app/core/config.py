from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_service_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_KEY")

    llm_provider: str | None = Field(default=None, alias="LLM_PROVIDER")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-6", alias="ANTHROPIC_MODEL")

    voyage_api_key: str | None = Field(default=None, alias="VOYAGE_API_KEY")
    voyage_model: str = Field(default="voyage-3-large", alias="VOYAGE_MODEL")
    embedding_dimension: int = Field(default=1024, alias="EMBEDDING_DIMENSION")

    similarity_threshold: float = Field(default=0.40, alias="SIMILARITY_THRESHOLD")
    max_chunks_retrieved: int = Field(default=5, alias="MAX_CHUNKS_RETRIEVED")

settings = Settings()

