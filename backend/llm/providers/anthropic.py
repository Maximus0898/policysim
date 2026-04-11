import anthropic
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from typing import List, Dict, Optional
from backend.llm.base import LLMProvider, LLMMessage, LLMResponse
from backend.config import settings

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.default_model = "claude-3-5-sonnet-20241022"

    def _is_retryable(self, exception):
        return isinstance(exception, (anthropic.APIConnectionError, anthropic.RateLimitError))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(lambda e: isinstance(e, (anthropic.APIConnectionError, anthropic.RateLimitError)))
    )
    async def chat(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: int = 1024,
        response_format: Optional[str] = None
    ) -> LLMResponse:
        # Map messages
        anthropic_messages = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]
        system_message = next((m.content for m in messages if m.role == "system"), None)

        response = await self.client.messages.create(
            model=self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message,
            messages=anthropic_messages
        )

        return LLMResponse(
            content=response.content[0].text,
            model_name=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            raw_response=response
        )

    def get_token_count(self, text: str) -> int:
        # Rough estimate for planning (4 chars per token)
        return len(text) // 4
