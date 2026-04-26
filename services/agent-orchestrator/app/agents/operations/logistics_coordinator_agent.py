from typing import Any, Dict
from ..base_agent import BaseAgent

class LogisticsCoordinatorAgent(BaseAgent):
    name = "logistics_coordinator_agent"
    module = "operations"
    description = "Route optimization and delivery planning"
    tools = ["sql_tool", "calculation_tool", "api_tool", "rag_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Logistics Coordinator Agent for NexaMind Operations Platform.
Your role is to optimize delivery operations and reduce logistics costs.

Optimization capabilities:
- Multi-stop route optimization
- Carrier selection and rate comparison
- Delivery time window management
- Load consolidation opportunities
- Carrier performance tracking
- Returns optimization

Key metrics to optimize:
- Cost per delivery
- On-time delivery rate  
- Utilization rate
- Carbon footprint

Provide specific carrier recommendations with cost-benefit analysis."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        kb = await self.search_knowledge(user_input, collection="logistics")
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Logistics Knowledge:
{[r['content'] for r in kb[:3]]}

Provide logistics optimization recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.3)
        return {"response": response, "agent": self.name}
