from typing import Any, Dict
from ..base_agent import BaseAgent

class AdvisorAgent(BaseAgent):
    name = "advisor_agent"
    module = "finance"
    description = "Budget recommendations and cost optimization"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "document_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Budget Advisor Agent for NexaMind. 
Your role is to analyze spending patterns and provide actionable cost optimization recommendations.

Advisory capabilities:
- Budget allocation optimization
- Cost center analysis
- Vendor consolidation opportunities
- ROI analysis for major expenditures
- Cash flow optimization strategies
- Benchmark comparisons (if data available)

For each recommendation:
1. Current state (quantified)
2. Recommended action (specific and actionable)
3. Expected impact ($ savings or % improvement)
4. Implementation effort (low/medium/high)
5. Priority score (1-10)
6. Risk of not acting

Be specific with numbers. Vague advice has no value."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        spending = await sql.execute(
            """SELECT category, SUM(ABS(amount)) as total_spend, COUNT(*) as txn_count,
                AVG(ABS(amount)) as avg_transaction
            FROM financial_transactions
            WHERE tenant_id = :tenant_id AND amount < 0
              AND transaction_date >= NOW() - INTERVAL '6 months'
            GROUP BY category ORDER BY total_spend DESC LIMIT 20""",
            {"tenant_id": self.tenant_id}
        )
        
        kb = await self.search_knowledge(user_input, collection="finance")
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Spending by Category (last 6 months):
{spending}

Relevant Context:
{[r['content'] for r in kb[:3]]}

Provide specific, prioritized budget recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.3)
        return {"response": response, "categories_analyzed": spending.get("count", 0)}
