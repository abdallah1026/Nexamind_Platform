from typing import Any, Dict
from ..base_agent import BaseAgent

class SupplyOptimizerAgent(BaseAgent):
    name = "supply_optimizer_agent"
    module = "operations"
    description = "Procurement optimization and supplier performance analysis"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "webhook_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Supply Optimizer Agent for NexaMind Operations Platform.
Your role is to optimize the supply chain through intelligent procurement strategies.

Analysis dimensions:
- Supplier performance scoring (quality, delivery, cost, service)
- Single-source vs multi-source risk analysis
- Volume consolidation opportunities
- Contract optimization timing
- Emergency supplier identification
- Total Cost of Ownership (TCO) analysis

Supplier scoring (0-100):
- On-time delivery rate (30%)
- Quality defect rate (25%)
- Price competitiveness (25%)
- Service responsiveness (20%)

Provide actionable procurement recommendations with ROI estimates."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        suppliers = await sql.execute(
            """SELECT name, reliability_score, lead_time_days, is_preferred,
                categories, payment_terms
            FROM suppliers
            WHERE tenant_id = :tenant_id
            ORDER BY reliability_score DESC NULLS LAST""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Supplier Data:
{suppliers}

Provide supply chain optimization recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.2)
        return {"response": response, "suppliers_analyzed": suppliers.get("count", 0)}
