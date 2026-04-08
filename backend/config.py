from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "PolicySim API"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./policysim.db"
    
    # LLM Settings
    llm_provider: str = "lmstudio"  # anthropic, openai, ollama, lmstudio
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    lmstudio_base_url: str = "http://localhost:1234"
    lmstudio_model: str = "local-model"  # override with your loaded model identifier
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
