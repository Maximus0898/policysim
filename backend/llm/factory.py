from backend.config import settings
from backend.llm.base import LLMProvider
from backend.llm.providers.anthropic import AnthropicProvider
from backend.llm.providers.openai import OpenAIProvider

class ProviderFactory:
    _instances = {}

    @classmethod
    def get_provider(cls) -> LLMProvider:
        provider_name = settings.llm_provider.lower()
        
        if provider_name in cls._instances:
            return cls._instances[provider_name]

        if provider_name == "anthropic":
            key = settings.anthropic_api_key or ""
            if not key:
                raise ValueError("ANTHROPIC_API_KEY is required but not set or empty.")
            provider = AnthropicProvider(api_key=key)
        elif provider_name == "openai":
            key = settings.openai_api_key or ""
            if not key:
                raise ValueError("OPENAI_API_KEY is required but not set or empty.")
            provider = OpenAIProvider(api_key=key)
        elif provider_name == "ollama":
            # Use OpenAI compatible endpoint for Ollama
            provider = OpenAIProvider(
                api_key="none", 
                base_url=f"{settings.ollama_base_url}/v1"
            )
            provider.default_model = "llama3" # Default for Ollama
        elif provider_name == "lmstudio":
            # LM Studio uses OpenAI-compatible endpoint
            provider = OpenAIProvider(
                api_key="lm-studio",  # LM Studio ignores the key but needs a non-empty string
                base_url=f"{settings.lmstudio_base_url}/v1"
            )
            provider.default_model = settings.lmstudio_model
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

        cls._instances[provider_name] = provider
        return provider

def get_provider() -> LLMProvider:
    return ProviderFactory.get_provider()
