from typing import Any, Dict
from ..base_agent import BaseAgent

class TalentScoutAgent(BaseAgent):
    name = "talent_scout_agent"
    module = "hr"
    description = "Candidate screening and recruitment optimization"
    tools = ["sql_tool", "document_tool", "rag_tool", "api_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Talent Scout Agent for NexaMind HR Platform.
Your role is to optimize the recruitment process using data-driven insights.

Capabilities:
- Job description optimization for better candidate attraction
- Resume/CV screening and scoring
- Culture fit assessment based on company values
- Interview question generation tailored to role
- Pipeline bottleneck identification
- Diversity and inclusion metrics analysis

Evaluation criteria:
1. Skills match (technical and soft skills)
2. Experience relevance  
3. Career progression quality
4. Cultural alignment indicators
5. Growth potential signals

Always be objective and bias-aware. Focus on skills and outcomes, not demographics."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        kb = await self.search_knowledge(user_input, collection="hr")
        
        dept_data = await sql.execute(
            """SELECT department, COUNT(*) as headcount, AVG(performance_score) as avg_perf
            FROM employees WHERE tenant_id = :tenant_id AND is_active = true
            GROUP BY department ORDER BY headcount DESC""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Current Workforce by Department:
{dept_data}

HR Knowledge Base Context:
{[r['content'] for r in kb[:3]]}

Provide talent acquisition recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.3)
        return {"response": response, "agent": self.name}
