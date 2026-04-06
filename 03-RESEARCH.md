# Phase 3: LLM Adapters - Research

## Swappable Provider Strategy (2025)
- **Primary SDKs**: `anthropic` (v0.x) and `openai` (v1.x) are the gold standards for async LLM communication.
- **Local LLM Compatibility**: Both **Ollama** and **LM Studio** now provide full OpenAI-compatible API layers. 
  - **Ollama**: `http://localhost:11434/v1`
  - **LM Studio**: `http://localhost:1234/v1` (Default)
- **Unified Interface**: Use the `LLMProvider` abstract base class to wrap these SDKs.

## Implementation Details
- **Anthropic (Claude)**: 
  - Use `AsyncAnthropic`.
  - Native JSON mode via prompt engineering + `max_tokens` management.
- **OpenAI (GPT-4/o)**:
  - Use `AsyncOpenAI`.
  - Native JSON mode via `response_format={"type": "json_object"}`.
- **Local Providers (Ollama/LM Studio)**:
  - Reuse the `OpenAIProvider` class with a custom `base_url` and `api_key="not-needed"`.
  - Resilience: Local models may be slower or more prone to timeouts; increase default timeout to 120s.

## Usage Tracking
- Track `prompt_tokens`, `completion_tokens`, and `total_tokens` uniformly across all providers.
- **Anthropic**: usage data is in `message.usage`.
- **OpenAI**: usage data is in `completion.usage`.

## Resilience & Retries
- Use `tenacity` for exponential backoff on `429` (Rate Limit) and `503` (Service Unavailable).
- Maximum 3 retries by default.

## Next Step Implementation
- I will implement a `ProviderFactory` that reads `LLM_PROVIDER` from `.env` and returns the singleton instance of the requested provider.

---
*Status: Complete*
