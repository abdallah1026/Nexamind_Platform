from typing import Any, Dict
from ..base_agent import BaseAgent

class ReporterAgent(BaseAgent):
    name = "reporter_agent"
    module = "finance"
    description = "Financial narrative generation and executive reporting"
    tools = ["sql_tool", "rag_tool", "document_tool", "email_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Financial Reporter Agent for NexaMind.
Your role is to transform raw financial data into clear, compelling narratives for various audiences.

Reporting capabilities:
- Executive financial summaries
- Monthly/quarterly performance reports  
- Board-ready presentations
- Departmental budget reports
- Cash flow narratives
- KPI dashboards

Writing standards:
- Lead with the headline number or key insight
- Provide context (vs prior period, vs budget, vs industry)
- Use plain language; avoid jargon unless audience is technical
- Include clear data tables
- End with forward-looking statements and recommendations
- Use professional, confident tone"""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        summary = await sql.execute(
            """SELECT 
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_revenue,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_expenses,
                SUM(amount) as net_cash_flow,
                COUNT(DISTINCT DATE_TRUNC('month', transaction_date)) as months_of_data
            FROM financial_transactions
            WHERE tenant_id = :tenant_id
              AND transaction_date >= NOW() - INTERVAL '3 months'""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Financial Summary (last 3 months):
{summary}

Generate a professional financial report."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.4)
        return {"response": response, "report_type": "financial_narrative"}
