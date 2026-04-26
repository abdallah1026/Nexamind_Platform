from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class EpisodicMemory:
    """Records significant agent interactions for learning and context"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def record(self, session_id: str, agent_name: str, 
                     user_input: str, response: str, feedback_score: Optional[float] = None):
        await self.db.execute(
            text("""INSERT INTO agent_conversations 
                (session_id, tenant_id, agent_name, role, content, metadata)
                VALUES (:sid, :tid, :agent, 'assistant', :content, :meta)"""),
            {
                "sid": session_id,
                "tid": self.tenant_id,
                "agent": agent_name,
                "content": response,
                "meta": {"user_input": user_input, "feedback_score": feedback_score}
            }
        )

    async def get_recent(self, agent_name: str, limit: int = 5) -> List[Dict]:
        result = await self.db.execute(
            text("""SELECT content, metadata, created_at 
                FROM agent_conversations 
                WHERE tenant_id=:tid AND agent_name=:agent
                ORDER BY created_at DESC LIMIT :lim"""),
            {"tid": self.tenant_id, "agent": agent_name, "lim": limit}
        )
        return [{"content": r[0], "metadata": r[1], "created_at": str(r[2])} for r in result.fetchall()]

from typing import Optional
