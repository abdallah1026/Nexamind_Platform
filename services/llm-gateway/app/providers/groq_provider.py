

from groq import AsyncGroq
from .base import BaseLLMProvider, CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse

class GroqProvider(BaseLLMProvider):
    
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
        
        self.default_model = "llama-3.3-70b-versatile"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:

        messages = []

        if request.system:
            messages.append({"role": "system", "content": request.system})

        for m in request.messages:
            if m.role == "system" and request.system:
                continue  
            messages.append({"role": m.role, "content": m.content})

        model = request.model
        if model == "default":
            model = self.default_model
        
        response = await self.client.chat.completions.create(
            model=model,
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
            finish_reason=choice.finish_reason or "stop"
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        
        raise NotImplementedError(
            "Groq does not support embeddings. "
            "The RAG service uses sentence-transformers locally for this."
        )

    async def list_models(self) -> list[str]:
        return [
            "llama3-70b-8192",
            "llama3-8b-8192", 
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
        ]
