from openai import AsyncOpenAI
import uuid
from .base import BaseLLMProvider, CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.default_model = "gpt-4o"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        if request.system:
            messages.insert(0, {"role": "system", "content": request.system})
        
        response = await self.client.chat.completions.create(
            model=request.model if request.model != "default" else self.default_model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        choice = response.choices[0]
        return CompletionResponse(
            id=response.id,
            model=response.model,
            content=choice.message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            finish_reason=choice.finish_reason
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        inputs = [request.input] if isinstance(request.input, str) else request.input
        response = await self.client.embeddings.create(model=request.model, input=inputs)
        return EmbeddingResponse(
            embeddings=[d.embedding for d in response.data],
            model=response.model,
            tokens_used=response.usage.total_tokens
        )

    async def list_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "text-embedding-3-small", "text-embedding-3-large"]
