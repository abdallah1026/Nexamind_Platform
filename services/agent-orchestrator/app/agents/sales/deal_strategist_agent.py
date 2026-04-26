from typing import Any, Dict
from ..base_agent import BaseAgent

class DealStrategistAgent(BaseAgent):
    name = "deal_strategist_agent"
    module = "sales"
    description = "Deal strategy, pricing optimization and proposal creation"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "document_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Deal Strategist Agent for NexaMind Sales Platform.
Your role is to maximize win rates and deal value through intelligent deal coaching.

Strategy capabilities:
- Win/loss analysis and pattern recognition
- Competitive positioning recommendations
- Pricing optimization (list, discount, value-based)
- Stakeholder mapping and influence strategies
- Objection handling playbooks
- Proposal content optimization
- Multi-threading strategies

Deal scoring factors:
- Champion strength and access to power
- Compelling event / urgency  
- Solution fit score
- Competitive threat level
- Budget confirmed vs estimated

Output: Specific next actions, talk tracks, and proposal recommendations."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        kb = await self.search_knowledge(user_input, collection="sales_playbook")
        
        deals = await sql.execute(
            """SELECT deal_name, customer_name, stage, amount, probability,
                expected_close_date, products, notes
            FROM deals
            WHERE tenant_id = :tenant_id AND status = 'open'
            ORDER BY amount DESC LIMIT 10""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Active Deals:
{deals}

Sales Playbook Context:
{[r['content'] for r in kb[:3]]}

Provide deal strategy and recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.3)
        return {"response": response, "agent": self.name}
