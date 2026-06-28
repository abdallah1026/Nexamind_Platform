

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
import json

class BaseAgent(ABC):
    
    name: str = ""
    module: str = ""
    description: str = ""
    tools: List[str] = []

    def __init__(
        self, 
        tenant_id: str, 
        llm_gateway_url: str, 
        rag_service_url: str,
        db_session=None, 
        redis_client=None, 
        config: Dict = None
    ):
        self.tenant_id = tenant_id
        self.llm_url = llm_gateway_url
        self.rag_url = rag_service_url
        self.db = db_session
        self.redis = redis_client
        self.config = config or {}

        self._tools = {}

    def get_tool(self, tool_name: str):
        """get a tool instance (creates it if doesnt exist)"""
        if tool_name in self._tools:
            return self._tools[tool_name]
        
        from ..tools.registry import get_tool

        kwargs = {"tenant_id": self.tenant_id}
        
        if tool_name == "sql_tool":
            kwargs["db_session"] = self.db
        elif tool_name == "rag_tool":
            kwargs["rag_service_url"] = self.rag_url
        elif tool_name == "email_tool":
            kwargs["smtp_host"] = self.config.get("smtp_host", "")
            kwargs["smtp_port"] = self.config.get("smtp_port", 587)
            kwargs["smtp_user"] = self.config.get("smtp_user", "")
            kwargs["smtp_password"] = self.config.get("smtp_password", "")
        
        tool = get_tool(tool_name, **kwargs)
        self._tools[tool_name] = tool
        return tool

    async def call_llm(
        self, 
        messages: List[Dict], 
        system: Optional[str] = None,
        model: str = "default", 
        max_tokens: int = 2000, 
        temperature: float = 0.3
    ) -> str:
        """send messages to LLM gateway and get response"""
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            payload["system"] = system
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.llm_url}/api/v1/chat/completions",
                json=payload,
                headers={"X-Tenant-Id": self.tenant_id}
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"]

    async def search_knowledge(self, query: str, collection: str = "default", n: int = 5) -> List[Dict]:
        """search the knowledge base"""
        tool = self.get_tool("rag_tool")
        result = await tool.execute(query, collection=collection, n_results=n)
        return result.get("results", [])

    @abstractmethod
    def get_system_prompt(self) -> str:
        """each agent must define its own system prompt"""
        pass

    @abstractmethod
    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        """each agent must implement this"""
        pass

    async def run(self, user_input: str, context: Dict = None, session_id: str = None) -> Dict[str, Any]:
        """main entry point - wraps process() with error handling"""
        ctx = context or {}
        
        try:
            result = await self.process(user_input, ctx)
            result.setdefault("agent", self.name)
            result.setdefault("module", self.module)
            return result
            
        except httpx.TimeoutException:
            
            return {
                "agent": self.name,
                "module": self.module,
                "error": "timeout",
                "response": "Sorry the request timed out. Please try again."
            }
        except Exception as e:
            
            print(f"error in agent {self.name}: {e}")  
            return {
                "agent": self.name,
                "module": self.module,
                "error": str(e),
                "response": f"Something went wrong: {str(e)}"
            }
