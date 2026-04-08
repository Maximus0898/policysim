import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.llm import get_provider, LLMMessage, LLMResponse
from backend.llm.providers.anthropic import AnthropicProvider
from backend.llm.providers.openai import OpenAIProvider
from backend.config import settings

class TestLLMProviders(unittest.IsolatedAsyncioTestCase):
    
    @patch("backend.llm.providers.anthropic.AsyncAnthropic")
    async def test_anthropic_provider(self, mock_anthropic):
        # Setup mock
        mock_instance = mock_anthropic.return_value
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Claude's response")]
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_instance.messages.create = AsyncMock(return_value=mock_response)

        provider = AnthropicProvider(api_key="fake-key")
        messages = [LLMMessage(role="user", content="Hello")]
        
        response = await provider.chat(messages)
        
        self.assertEqual(response.content, "Claude's response")
        self.assertEqual(response.usage["prompt_tokens"], 10)
        self.assertEqual(response.usage["total_tokens"], 30)
        print("[OK] AnthropicProvider verified via mock")

    @patch("backend.llm.providers.openai.AsyncOpenAI")
    async def test_openai_provider(self, mock_openai):
        # Setup mock
        mock_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="GPT's response"))]
        mock_response.model = "gpt-4o"
        mock_response.usage = MagicMock(prompt_tokens=15, completion_tokens=25, total_tokens=40)
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAIProvider(api_key="fake-key")
        messages = [LLMMessage(role="user", content="Hello")]
        
        response = await provider.chat(messages)
        
        self.assertEqual(response.content, "GPT's response")
        self.assertEqual(response.usage["completion_tokens"], 25)
        self.assertEqual(response.usage["total_tokens"], 40)
        print("[OK] OpenAIProvider verified via mock")

    def test_provider_factory(self):
        # Mock settings
        with patch("backend.llm.factory.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            p = get_provider()
            self.assertIsInstance(p, AnthropicProvider)
            
            # Reset instances for clean test
            from backend.llm.factory import ProviderFactory
            ProviderFactory._instances = {}
            
            mock_settings.llm_provider = "openai"
            mock_settings.openai_api_key = "test"
            p = get_provider()
            self.assertIsInstance(p, OpenAIProvider)
            print("[OK] ProviderFactory verified logic")

if __name__ == "__main__":
    unittest.main()
