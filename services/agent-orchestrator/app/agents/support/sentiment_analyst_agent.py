from typing import Any, Dict
from ..base_agent import BaseAgent

class SentimentAnalystAgent(BaseAgent):
    name = "sentiment_analyst_agent"
    module = "support"
    description = "Customer sentiment tracking and at-risk identification"
    tools = ["sql_tool", "api_tool", "rag_tool", "webhook_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Sentiment Analyst Agent for NexaMind Support Platform.
Your role is to monitor and interpret customer sentiment signals across all touchpoints.

Sentiment analysis scope:
- Support ticket language and tone
- Customer feedback surveys (NPS, CSAT, CES)
- Chat conversation analysis
- Email communication patterns
- Escalation frequency and patterns

Sentiment classifications:
- Positive (score 0.6-1.0): Loyal, likely to expand
- Neutral (score 0.4-0.59): Passive, needs engagement
- Negative (score 0.2-0.39): At risk, requires attention
- Critical (score 0-0.19): Churn risk, executive escalation

Output: Customer health overview, sentiment trends, at-risk alerts, recommended actions."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        sentiment_data = await sql.execute(
            """SELECT customer_name, 
                AVG(sentiment_score) as avg_sentiment,
                COUNT(*) as ticket_count,
                SUM(CASE WHEN priority IN ('P1','P2') THEN 1 ELSE 0 END) as critical_tickets
            FROM support_tickets
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY customer_name
            ORDER BY avg_sentiment ASC NULLS LAST LIMIT 20""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Customer Sentiment Data (last 30 days):
{sentiment_data}

Provide sentiment analysis and at-risk customer identification."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.2)
        return {"response": response, "customers_analyzed": sentiment_data.get("count", 0)}
