from typing import Any, Dict
from ..base_agent import BaseAgent

class DemandPlannerAgent(BaseAgent):
    name = "demand_planner_agent"
    module = "operations"
    description = "Demand forecasting and inventory optimization"
    tools = ["sql_tool", "calculation_tool", "rag_tool", "api_tool"]

    def get_system_prompt(self) -> str:
        return """You are the Demand Planner Agent for NexaMind Operations Platform.
Your role is to optimize inventory levels through accurate demand forecasting.

Forecasting methods:
- Moving average and exponential smoothing
- Seasonal decomposition (additive and multiplicative)
- Trend extrapolation
- Event-driven demand spikes
- New product introduction curves

Inventory optimization outputs:
- Reorder points (ROP) by SKU
- Safety stock recommendations  
- Economic Order Quantity (EOQ)
- Days of Inventory Outstanding (DIO)
- Stockout risk scores

Always consider: lead times, demand variability, holding costs, stockout costs.
Target: 98% service level while minimizing excess inventory."""

    async def process(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        sql = self.get_tool("sql_tool")
        
        inventory = await sql.execute(
            """SELECT ii.sku, ii.name, ii.current_stock, ii.reorder_point,
                ii.lead_time_days, ii.unit_cost,
                AVG(df.predicted_demand::jsonb->0) as avg_forecast
            FROM inventory_items ii
            LEFT JOIN demand_forecasts df ON df.item_id = ii.id
            WHERE ii.tenant_id = :tenant_id AND ii.is_active = true
            GROUP BY ii.id ORDER BY ii.current_stock ASC LIMIT 20""",
            {"tenant_id": self.tenant_id}
        )
        
        messages = [{"role": "user", "content": f"""
Request: {user_input}

Inventory Status:
{inventory}

Provide demand forecast and inventory optimization recommendations."""}]
        
        response = await self.call_llm(messages, system=self.get_system_prompt(), temperature=0.2)
        return {"response": response, "skus_analyzed": inventory.get("count", 0)}
