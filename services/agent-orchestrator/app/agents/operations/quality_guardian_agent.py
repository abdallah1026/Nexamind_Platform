from typing import Any, Dict
from ..base_agent import BaseAgent

class QualityGuardianAgent(BaseAgent):
    name = "quality_guardian_agent"
    module = "operations"
    description = "Quality monitoring and defect analysis"
    tools = ["sql_tool", "calculation_tool", "document_tool", "rag_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Quality Guardian Agent for NexaMind Operations Platform.
Your role is to maintain and improve product/service quality standards.

Quality analysis:
- Defect rate trending (by product, supplier, batch)
- Root cause analysis frameworks (5-Why, Fishbone)
- Control chart interpretation (UCL, LCL, Cp, Cpk)
- Supplier quality correlation
- Cost of Poor Quality (COPQ) estimation

Output standards:
- Quantified defect rates (PPM preferred)
- Pareto analysis of defect types
- Corrective action recommendations (CAPA)
- Prevention vs detection cost analysis"""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        quality_data = await sql.execute(
            """SELECT ii.sku, ii.name, AVG(qm.defect_rate) as avg_defect_rate,
                AVG(qm.quality_score) as avg_quality, COUNT(qm.id) as measurements
            FROM quality_metrics qm
            JOIN inventory_items ii ON ii.id = qm.item_id
            WHERE qm.tenant_id = :tenant_id
              AND qm.measurement_date >= NOW() - INTERVAL '90 days'
            GROUP BY ii.id, ii.sku, ii.name
            ORDER BY avg_defect_rate DESC NULLS LAST LIMIT 20""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Quality Metrics (last 90 days):
{quality_data}

Provide quality analysis and improvement recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.2)
        return {"response": response, "agent": self.name}
