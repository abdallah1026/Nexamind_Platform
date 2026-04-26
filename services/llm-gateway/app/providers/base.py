from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class CompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int = 1000
    temperature: float = 0.7
    stream: bool = False
    system: Optional[str] = None

class CompletionResponse(BaseModel):
    id: str
    model: str
    content: str
    input_tokens: int
    output_tokens: int
    finish_reason: str

class EmbeddingRequest(BaseModel):
    model: str = "text-embedding-3-small"
    input: str | list[str]

class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    tokens_used: int

class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        pass

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        pass
