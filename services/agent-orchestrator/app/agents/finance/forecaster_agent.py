# forecaster agent - handles all the financial forecasting stuff
# written by me (graduation project 2024)
# TODO: add more forecasting methods later maybe ARIMA?

from typing import Any, Dict, List
from ..base_agent import BaseAgent


class ForecasterAgent(BaseAgent):
    name = "forecaster_agent"
    module = "finance"
    description = "does cash flow and revenue forecasting"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "api_tool"]

    def get_system_prompt(self) -> str:
        # i spent like 3 days writing this prompt lol
        return """You are a financial forecasting assistant.
Your job is to look at financial data and predict future values.

what you should do:
- look at historical transactions 
- find patterns and trends
- give a forecast for next 30/60/90 days
- mention if you are not confident about something

always give numbers not just vague answers. include best case and worst case."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        
        # first get data from db
        sql = self.get_tool("sql_tool")
        
        # TODO: maybe filter by category too? will think about this
        recent_data = await sql.execute(
            """SELECT 
                DATE_TRUNC('month', transaction_date) as month,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as revenue,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses,
                COUNT(*) as transaction_count
            FROM financial_transactions 
            WHERE tenant_id = :tenant_id
              AND transaction_date >= NOW() - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', transaction_date)
            ORDER BY month""",
            {"tenant_id": self.tenant_id}
        )
        
        # also search the knowledge base for any relevant stuff
        kb_results = await self.search_knowledge(user_input, collection="finance")
        
        # debug print - remove before final submission
        # print(f"got {recent_data.get('count')} months of data")
        
        messages = [{"role": "user", "content": f"""
the user asked: {user_input}

here is the last 12 months financial data:
{recent_data}

extra context from knowledge base:
{[r['content'] for r in kb_results[:2]]}

please give a forecast with explanation
"""}]
        
        response = await self.call_llm(
            messages, 
            system=self.get_system_prompt(), 
            temperature=0.2
        )
        
        return {
            "response": response,
            "data_points": recent_data.get("count", 0),
            "forecast_type": "financial",
        }
