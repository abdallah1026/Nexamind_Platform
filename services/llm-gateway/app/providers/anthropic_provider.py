import anthropic
import uuid
from .base import BaseLLMProvider, CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.default_model = "claude-sonnet-4-20250514"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        messages = [{"role": m.role, "content": m.content} for m in request.messages if m.role != "system"]
        system = request.system or next((m.content for m in request.messages if m.role == "system"), None)
        
        kwargs = dict(
            model=request.model if request.model != "default" else self.default_model,
            max_tokens=request.max_tokens,
            messages=messages,
            temperature=request.temperature,
        )
        if system:
            kwargs["system"] = system
        
        response = await self.client.messages.create(**kwargs)
        return CompletionResponse(
            id=response.id,
            model=response.model,
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            finish_reason=response.stop_reason or "stop"
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise NotImplementedError("Anthropic does not support embeddings; use OpenAI provider")

    async def list_models(self) -> list[str]:
        return ["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]
