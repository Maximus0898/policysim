import openai
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from typing import List, Dict, Optional, Any
from backend.llm.base import LLMProvider, LLMMessage, LLMResponse
from backend.config import settings

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.default_model = "gpt-4o"

    def _is_retryable(self, exception):
        return isinstance(exception, (openai.APIConnectionError, openai.RateLimitError))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(lambda e: isinstance(e, (openai.APIConnectionError, openai.RateLimitError)))
    )
    async def chat(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: int = 1024,
        response_format: Optional[str] = None
    ) -> LLMResponse:
        # Map messages
        openai_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        
        # Configure response format if requested
        rf = None
        if response_format == "json_object":
            rf = {"type": "json_object"}

        response = await self.client.chat.completions.create(
            model=self.default_model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=rf
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model_name=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            raw_response=response
        )

    def get_token_count(self, text: str) -> int:
        # Rough estimate for planning (4 chars per token)
        return len(text) // 4
