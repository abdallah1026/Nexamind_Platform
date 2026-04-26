import json
import re
from typing import Any, Dict, List, Optional

DANGEROUS_PATTERNS = re.compile(
    r'\b(DROP|TRUNCATE|DELETE\s+FROM|ALTER|CREATE|INSERT|UPDATE|GRANT|REVOKE)\b',
    re.IGNORECASE
)

class SQLTool:
    name = "sql_tool"
    description = "Execute read-only SQL queries against the tenant database"

    def __init__(self, db_session=None, tenant_id: str = None):
        self.db = db_session
        self.tenant_id = tenant_id

    async def execute(self, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        if DANGEROUS_PATTERNS.search(query):
            return {"error": "Query contains forbidden operations. Only SELECT is allowed."}
        
        if self.tenant_id and "tenant_id" not in query.lower():
            return {"error": "Query must filter by tenant_id for data isolation"}
        
        try:
            from sqlalchemy import text
            result = await self.db.execute(text(query), params or {})
            rows = result.mappings().all()
            return {
                "rows": [dict(r) for r in rows],
                "count": len(rows)
            }
        except Exception as e:
            return {"error": str(e)}

    def schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "query": {"type": "string", "description": "SQL SELECT query"},
                "params": {"type": "object", "description": "Query parameters"}
            }
        }
