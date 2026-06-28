

from typing import Any, Dict
from ..base_agent import BaseAgent

class ChurnGuardianAgent(BaseAgent):
    name = "churn_guardian_agent"
    module = "sales"
    description = "predicts customer churn and recommends retention actions"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "webhook_tool"]

    def get_system_prompt(self) -> str:
        return """You are a customer success assistant focused on preventing churn.

Churn risk levels:
- 0-25: healthy customer (maybe upsell opportunity)
- 26-50: neutral, keep regular contact
- 51-75: at risk, customer success should reach out soon
- 76-100: critical, needs immediate executive attention

For each at-risk customer tell me:
1. their risk score and why
2. how much annual revenue is at risk
3. what specific action to take (and who should do it)
4. timeline - when to act

Be specific. "Reach out to the customer" is not helpful. Say exactly what to say and do."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")

        churn_data = await sql.execute(
            """SELECT 
                customer_name, 
                churn_score, 
                risk_level, 
                annual_revenue_at_risk,
                risk_factors, 
                predicted_churn_date
            FROM customer_churn_risks
            WHERE tenant_id = :tenant_id 
              AND status = 'active'
            ORDER BY churn_score DESC 
            LIMIT 20""",
            {"tenant_id": self.tenant_id}
        )

        feedback = await sql.execute(
            """SELECT customer_name, rating, sentiment, themes
            FROM customer_feedback
            WHERE tenant_id = :tenant_id
              AND feedback_date >= NOW() - INTERVAL '60 days'
            ORDER BY rating ASC
            LIMIT 10""",
            {"tenant_id": self.tenant_id}
        )

        messages = [{
            "role": "user",
            "content": f"""
request: {user_input}

customers ranked by churn risk (highest first):
{churn_data}

recent negative feedback:
{feedback}

analyze the situation and give me a specific action plan
"""
        }]

        response = await self.call_llm(
            messages,
            system=self.get_system_prompt(),
            temperature=0.2
        )
        
        return {
            "response": response,
            "customers_at_risk": churn_data.get("count", 0)
        }
