

from typing import Any, Dict
from ..base_agent import BaseAgent

class RetentionGuardAgent(BaseAgent):
    name = "retention_guard_agent"
    module = "hr"
    description = "predicts attrition risk and suggests retention strategies"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "webhook_tool"]

    def get_system_prompt(self) -> str:
        return """You are an HR assistant that helps predict and prevent employee attrition.

Look at the employee data and identify who might be at risk of leaving.

Risk levels:
- Low (0-30): normal, no action needed
- Medium (31-60): worth checking in with the employee  
- High (61-80): manager should have a conversation
- Critical (81-100): needs immediate attention from leadership

For each at-risk employee please say:
- their risk level
- top reasons why they might leave
- specific things the company can do to keep them
- rough estimate of cost if they do leave (replacement usually costs 1-2x salary)

Keep it practical, not just generic HR advice."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")

        result = await sql.execute(
            """SELECT 
                e.full_name, 
                e.department, 
                e.job_title, 
                e.hire_date,
                e.performance_score, 
                e.engagement_score,
                e.salary,
                ar.risk_score, 
                ar.risk_level
            FROM employees e
            LEFT JOIN attrition_risks ar ON ar.employee_id = e.id
            WHERE e.tenant_id = :tenant_id 
              AND e.is_active = true
            ORDER BY ar.risk_score DESC NULLS LAST 
            LIMIT 20""",
            {"tenant_id": self.tenant_id}
        )

        surveys = await sql.execute(
            """SELECT 
                e.department,
                AVG(es.overall_score) as avg_score,
                COUNT(*) as response_count
            FROM engagement_surveys es
            JOIN employees e ON e.id = es.employee_id
            WHERE es.tenant_id = :tenant_id
              AND es.survey_date >= NOW() - INTERVAL '90 days'
            GROUP BY e.department""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{
            "role": "user", 
            "content": f"""
question: {user_input}

employee data (sorted by risk, highest first):
{result}

recent engagement survey results by department:
{surveys}

please analyze and give retention recommendations
"""
        }]
        
        response = await self.call_llm(
            messages, 
            system=self.get_system_prompt(),
            temperature=0.25
        )
        
        return {
            "response": response,
            "employees_checked": result.get("count", 0)
        }
