from typing import Any, Dict
from ..base_agent import BaseAgent

class KnowledgeCuratorAgent(BaseAgent):
    name = "knowledge_curator_agent"
    module = "support"
    description = "Knowledge base management and article generation"
    tools = ["sql_tool", "document_tool", "rag_tool", "api_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Knowledge Curator Agent for NexaMind Support Platform.
Your role is to build and maintain a world-class knowledge base that deflects tickets and empowers customers.

Curation capabilities:
- Gap analysis (high-volume topics with no KB article)
- Article quality scoring and improvement
- Outdated content identification
- FAQ generation from ticket patterns
- Internal vs external content classification
- SEO optimization for self-service

Article structure (STAR format):
- Situation: What problem does this solve?
- Task: What does the user need to do?
- Action: Step-by-step instructions (numbered)
- Result: Expected outcome and verification

Quality standards:
- Clear title with target keywords
- Under 800 words for how-to articles  
- Include screenshots placeholders [SCREENSHOT: description]
- Related articles links
- Last updated date"""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        ticket_topics = await sql.execute(
            """SELECT category, COUNT(*) as ticket_count,
                AVG(CASE WHEN resolution IS NOT NULL THEN 1 ELSE 0 END) as resolution_rate
            FROM support_tickets
            WHERE tenant_id = :tenant_id
              AND created_at >= NOW() - INTERVAL '90 days'
            GROUP BY category ORDER BY ticket_count DESC LIMIT 10""",
            {"tenant_id": self.tenant_id}
        )
        
        kb_coverage = await sql.execute(
            """SELECT category, COUNT(*) as articles, AVG(view_count) as avg_views
            FROM knowledge_articles
            WHERE tenant_id = :tenant_id AND status = 'published'
            GROUP BY category""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Top Ticket Categories (last 90 days):
{ticket_topics}

Current KB Coverage:
{kb_coverage}

Provide knowledge base recommendations and generate requested content."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.4)
        return {"response": response, "agent": self.name}
