from typing import Any, Dict
from ..base_agent import BaseAgent

class TicketResolverAgent(BaseAgent):
    name = "ticket_resolver_agent"
    module = "support"
    description = "Ticket triage and automated response drafting"
    tools = ["sql_tool", "rag_tool", "api_tool", "email_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Ticket Resolver Agent for NexaMind Support Platform.
Your role is to rapidly triage and resolve customer support tickets.

Triage methodology:
1. Classify ticket: Category (technical/billing/feature/general), Priority (P1-P4), Sentiment
2. Search knowledge base for matching resolutions
3. Draft personalized response based on customer context
4. Identify escalation triggers (VIP customer, legal risk, repeated issue)

Priority mapping:
- P1 (Critical): Service down, data loss, security issue → < 1 hour response
- P2 (High): Core feature broken, significant business impact → < 4 hours
- P3 (Medium): Non-critical bug, workaround available → < 24 hours  
- P4 (Low): Feature request, general inquiry → < 72 hours

Response quality standards:
- Acknowledge the issue explicitly
- Provide root cause (if known) or ETA for investigation
- Give specific next steps
- Use customer's name
- Professional but warm tone"""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        rag = self.get_tool("rag_tool")

        kb_results = await rag.execute(user_input, collection="knowledge_base", n_results=5)
        
        recent_tickets = await sql.execute(
            """SELECT ticket_number, subject, category, priority, status,
                sentiment, created_at, description
            FROM support_tickets
            WHERE tenant_id = :tenant_id AND status = 'open'
            ORDER BY created_at DESC LIMIT 10""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Ticket/Request: {user_input}

Similar Knowledge Base Articles:
{[r['content'][:300] for r in kb_results.get('results', [])[:3]]}

Recent Open Tickets Context:
{recent_tickets}

Provide: 1) Ticket classification 2) Priority level 3) Draft response 4) Escalation recommendation."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.3)
        return {"response": response, "kb_articles_found": len(kb_results.get("results", []))}
