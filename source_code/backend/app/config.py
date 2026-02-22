from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_url: str = "http://host-gateway:11434"
    ollama_model: str = "llama3.2:latest"
    session_ttl_seconds: int = 3600

    class Config:
        env_file = ".env"


settings = Settings()
