from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

class AgentState(BaseModel):
    agent_name: str
    tenant_id: str
    session_id: Optional[str] = None
    messages: List[Dict[str, str]] = []
    tool_calls: List[Dict[str, Any]] = []
    context: Dict[str, Any] = {}
    created_at: datetime = None
    
    class Config:
        arbitrary_types_allowed = True
