from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str

@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int]  # {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    model_name: str
    raw_response: Any = None


class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[str] = None # e.g. "json_object"
    ) -> LLMResponse:
        """Execute a chat completion request."""
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Estimate token count for a given text."""
        pass
