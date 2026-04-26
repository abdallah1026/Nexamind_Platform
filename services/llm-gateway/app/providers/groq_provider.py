# groq provider - fast inference, free tier available
# groq uses openai-compatible API so this is pretty straightforward
# models: llama-3.1-8b-instant, llama-3.1-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
#
# NOTE: groq does NOT support embeddings
# for embeddings we use sentence-transformers locally (see rag service)

from groq import AsyncGroq
from .base import BaseLLMProvider, CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse


class GroqProvider(BaseLLMProvider):
    
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
        # llama-3.3 70b is the best quality groq model currently
        self.default_model = "llama-3.3-70b-versatile"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        
        # build messages list
        messages = []
        
        # groq supports system messages differently - add as first message
        if request.system:
            messages.append({"role": "system", "content": request.system})
        
        # add the rest of messages (skip system ones if already added)
        for m in request.messages:
            if m.role == "system" and request.system:
                continue  # already handled above
            messages.append({"role": m.role, "content": m.content})
        
        # pick model
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
        # groq doesnt support embeddings
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
