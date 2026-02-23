from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Session ───────────────────────────────────────────────────────────────
    session_ttl_seconds: int = 3600

    # ── LLM provider: "ollama" (default) or "openai" ─────────────────────────
    llm_provider: str = "ollama"

    # ── Ollama (used when llm_provider=ollama) ────────────────────────────────
    ollama_url: str = "http://host-gateway:11434"
    ollama_model: str = "llama3.2:latest"

    # ── OpenAI-compatible API (used when llm_provider=openai) ────────────────
    # Works with OpenRouter, OpenAI, or any OpenAI-compatible endpoint.
    openai_api_key: str = ""
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "anthropic/claude-3-5-sonnet"

    class Config:
        env_file = ".env"


settings = Settings()
