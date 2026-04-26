from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class LongTermMemory:
    """Persistent memory stored in PostgreSQL with vector similarity"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def store(self, agent_name: str, key: str, value: Any, memory_type: str = "fact"):
        await self.db.execute(
            text("""INSERT INTO agent_memory_long_term 
                (tenant_id, agent_name, memory_type, key, value)
                VALUES (:tid, :agent, :mtype, :key, :value)
                ON CONFLICT (tenant_id, agent_name, key) 
                DO UPDATE SET value = :value, access_count = agent_memory_long_term.access_count + 1"""),
            {"tid": self.tenant_id, "agent": agent_name, "mtype": memory_type,
             "key": key, "value": value}
        )

    async def retrieve(self, agent_name: str, key: str) -> Optional[Any]:
        result = await self.db.execute(
            text("SELECT value FROM agent_memory_long_term WHERE tenant_id=:tid AND agent_name=:agent AND key=:key"),
            {"tid": self.tenant_id, "agent": agent_name, "key": key}
        )
        row = result.scalar_one_or_none()
        return row

    async def list_keys(self, agent_name: str, prefix: str = "") -> List[str]:
        result = await self.db.execute(
            text("SELECT key FROM agent_memory_long_term WHERE tenant_id=:tid AND agent_name=:agent AND key LIKE :prefix"),
            {"tid": self.tenant_id, "agent": agent_name, "prefix": f"{prefix}%"}
        )
        return [r[0] for r in result.fetchall()]
