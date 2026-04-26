from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

class FeedbackCreate(BaseModel):
    conversation_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    categories: List[str] = []

class FeedbackResponse(BaseModel):
    id: uuid.UUID
    rating: int
    comment: Optional[str]
    created_at: str
