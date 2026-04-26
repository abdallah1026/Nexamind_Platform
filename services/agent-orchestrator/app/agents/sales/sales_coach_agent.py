from typing import Any, Dict
from ..base_agent import BaseAgent

class SalesCoachAgent(BaseAgent):
    name = "sales_coach_agent"
    module = "sales"
    description = "Rep performance analysis and personalized coaching"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "api_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Sales Coach Agent for NexaMind Sales Platform.
Your role is to develop sales rep capabilities through data-driven coaching.

Coaching methodology:
- Activity analysis (calls, emails, meetings, demos)
- Pipeline quality assessment
- Win rate benchmarking
- Skill gap identification from call analysis
- Personalized improvement plans
- Quota attainment trajectory

Coaching framework (GROW):
- Goal: What are we trying to improve?
- Reality: Where is the rep today (data)?
- Options: What coaching interventions?
- Way Forward: Specific actions and timeline

Be specific, data-driven, and motivational. Avoid generic advice."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        perf = await sql.execute(
            """SELECT owner as rep, COUNT(*) as deals, 
                SUM(CASE WHEN status='won' THEN 1 ELSE 0 END) as won,
                SUM(amount) as pipeline_value,
                AVG(CASE WHEN status='won' THEN amount END) as avg_deal_size
            FROM deals
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '90 days'
            GROUP BY owner ORDER BY pipeline_value DESC""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Rep Performance (last 90 days):
{perf}

Provide coaching recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.4)
        return {"response": response, "agent": self.name}
