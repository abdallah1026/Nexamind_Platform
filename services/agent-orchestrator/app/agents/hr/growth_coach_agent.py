from typing import Any, Dict
from ..base_agent import BaseAgent

class GrowthCoachAgent(BaseAgent):
    name = "growth_coach_agent"
    module = "hr"
    description = "Career development and skill gap analysis"
    tools = ["sql_tool", "rag_tool", "document_tool", "email_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Growth Coach Agent for NexaMind HR Platform.
Your role is to accelerate employee career development through personalized coaching.

Coaching capabilities:
- Individual skill gap analysis vs role requirements
- Personalized learning path creation
- Career trajectory mapping
- Mentorship matching recommendations
- Stretch assignment identification
- 30/60/90 day development plan creation

Development plan structure:
1. Current state assessment (strengths and gaps)
2. Target state (6-12 month goals)
3. Specific learning actions (with resources)
4. Milestone checkpoints
5. Success metrics
6. Manager support required

Always tie development to business outcomes. Generic plans get ignored."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        kb = await self.search_knowledge(user_input, collection="hr_development")
        
        employee_data = await sql.execute(
            """SELECT e.full_name, e.job_title, e.department, e.skills,
                dp.objectives, dp.skill_gaps, dp.progress
            FROM employees e
            LEFT JOIN development_plans dp ON dp.employee_id = e.id
            WHERE e.tenant_id = :tenant_id AND e.is_active = true
            LIMIT 10""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Employee Development Data:
{employee_data}

Learning Resources Available:
{[r['content'] for r in kb[:3]]}

Create personalized development recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.4)
        return {"response": response, "agent": self.name}
