from typing import Any, Dict
from ..base_agent import BaseAgent

class QualityAnalystAgent(BaseAgent):
    name = "quality_analyst_agent"
    module = "support"
    description = "Support quality monitoring and agent coaching"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "email_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Quality Analyst Agent for NexaMind Support Platform.
Your role is to ensure and improve the quality of customer support interactions.

Quality dimensions evaluated:
1. Technical accuracy (30%): Is the solution correct?
2. Communication quality (25%): Clear, professional, empathetic?
3. Process adherence (20%): SLA met, proper escalation?
4. Customer effort score (15%): One-contact resolution?
5. Knowledge utilization (10%): KB articles referenced appropriately?

Scoring scale: 0-100 per dimension, weighted total
- 90-100: Excellent (share as best practice)
- 75-89: Good (minor coaching points)
- 60-74: Needs Improvement (coaching plan)
- Below 60: Performance Improvement Plan required

Provide specific, actionable feedback with examples."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        quality_data = await sql.execute(
            """SELECT tr.responder_name, AVG(qs.score) as avg_quality,
                COUNT(DISTINCT tr.ticket_id) as tickets_handled,
                AVG(st.csat_score) as avg_csat
            FROM ticket_responses tr
            LEFT JOIN quality_scores qs ON qs.ticket_id = tr.ticket_id
            LEFT JOIN support_tickets st ON st.id = tr.ticket_id
            WHERE tr.tenant_id = :tenant_id
              AND tr.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY tr.responder_name
            ORDER BY avg_quality ASC NULLS LAST""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Agent Quality Metrics (last 30 days):
{quality_data}

Provide quality analysis and coaching recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.3)
        return {"response": response, "agents_evaluated": quality_data.get("count", 0)}
