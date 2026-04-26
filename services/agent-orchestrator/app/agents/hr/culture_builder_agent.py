from typing import Any, Dict
from ..base_agent import BaseAgent

class CultureBuilderAgent(BaseAgent):
    name = "culture_builder_agent"
    module = "hr"
    description = "Employee sentiment analysis and engagement insights"
    tools = ["sql_tool", "rag_tool", "api_tool", "document_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Culture Builder Agent for NexaMind HR Platform.
You analyze employee sentiment, engagement data, and culture signals to help build thriving workplaces.

Analysis capabilities:
- Engagement survey interpretation
- Sentiment trend analysis across departments
- Cultural health scoring
- Manager effectiveness ratings
- DEI metric tracking
- eNPS (Employee Net Promoter Score) analysis

Output format:
- Culture Health Score (0-100)
- Key strengths (top 3)
- Critical concerns (top 3 with urgency)
- Department-level breakdown
- Recommended initiatives with expected impact
- Communication strategies"""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        survey_data = await sql.execute(
            """SELECT department, AVG(overall_score) as avg_engagement,
                COUNT(*) as responses, AVG(CASE WHEN sentiment='positive' THEN 1 
                WHEN sentiment='neutral' THEN 0 ELSE -1 END) as sentiment_score
            FROM engagement_surveys es
            JOIN employees e ON e.id = es.employee_id
            WHERE es.tenant_id = :tenant_id
              AND es.survey_date >= NOW() - INTERVAL '6 months'
            GROUP BY department""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Engagement Survey Results by Department:
{survey_data}

Provide culture analysis and engagement recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.3)
        return {"response": response, "agent": self.name}
