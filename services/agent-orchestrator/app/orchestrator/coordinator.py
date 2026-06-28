

from typing import Dict, Any, Optional, List
import re

MODULE_KEYWORDS = {
    "finance": [
        "revenue", "expense", "budget", "cost", "forecast", "cash", "profit", 
        "invoice", "transaction", "financial", "anomaly", "fraud", "report", 
        "spend", "money", "payment", "billing"
    ],
    "hr": [
        "employee", "hire", "talent", "attrition", "retention", "culture", 
        "engagement", "performance", "salary", "career", "development", 
        "skill", "training", "recruit", "staff", "workforce"
    ],
    "operations": [
        "inventory", "supply", "demand", "logistics", "shipping", "warehouse",
        "quality", "supplier", "procurement", "route", "delivery", "stock",
        "product", "manufacturing"
    ],
    "sales": [
        "deal", "pipeline", "churn", "customer", "quota", "opportunity",
        "close", "proposal", "pricing", "win", "loss", "crm", "lead", "prospect"
    ],
    "support": [
        "ticket", "issue", "complaint", "help", "resolve", "sentiment", 
        "knowledge", "article", "escalate", "response", "satisfaction", 
        "csat", "nps", "bug", "problem"
    ],
}

AGENT_TASK_MAP = {
    "finance": {
        "forecast": "forecaster_agent",
        "predict": "forecaster_agent",
        "anomaly": "detector_agent",
        "fraud": "detector_agent",
        "suspicious": "detector_agent",
        "budget": "advisor_agent",
        "recommend": "advisor_agent",
        "optimize": "advisor_agent",
        "report": "reporter_agent",
        "summary": "reporter_agent",
        "default": "reporter_agent",
    },
    "hr": {
        "recruit": "talent_scout_agent",
        "hire": "talent_scout_agent",
        "candidate": "talent_scout_agent",
        "attrition": "retention_guard_agent",
        "leaving": "retention_guard_agent",
        "quit": "retention_guard_agent",
        "development": "growth_coach_agent",
        "career": "growth_coach_agent",
        "skills": "growth_coach_agent",
        "culture": "culture_builder_agent",
        "engagement": "culture_builder_agent",
        "morale": "culture_builder_agent",
        "default": "retention_guard_agent",
    },
    "operations": {
        "demand": "demand_planner_agent",
        "inventory": "demand_planner_agent",
        "reorder": "demand_planner_agent",
        "supplier": "supply_optimizer_agent",
        "procurement": "supply_optimizer_agent",
        "vendor": "supply_optimizer_agent",
        "logistics": "logistics_coordinator_agent",
        "delivery": "logistics_coordinator_agent",
        "shipping": "logistics_coordinator_agent",
        "quality": "quality_guardian_agent",
        "defect": "quality_guardian_agent",
        "default": "demand_planner_agent",
    },
    "sales": {
        "forecast": "revenue_forecaster_agent",
        "pipeline": "revenue_forecaster_agent",
        "revenue": "revenue_forecaster_agent",
        "churn": "churn_guardian_agent",
        "leaving": "churn_guardian_agent",
        "deal": "deal_strategist_agent",
        "pricing": "deal_strategist_agent",
        "proposal": "deal_strategist_agent",
        "coach": "sales_coach_agent",
        "performance": "sales_coach_agent",
        "default": "revenue_forecaster_agent",
    },
    "support": {
        "ticket": "ticket_resolver_agent",
        "resolve": "ticket_resolver_agent",
        "issue": "ticket_resolver_agent",
        "sentiment": "sentiment_analyst_agent",
        "feeling": "sentiment_analyst_agent",
        "knowledge": "knowledge_curator_agent",
        "article": "knowledge_curator_agent",
        "faq": "knowledge_curator_agent",
        "quality": "quality_analyst_agent",
        "default": "ticket_resolver_agent",
    },
}

def detect_module(text: str) -> Optional[str]:
    """figure out which module the user is asking about"""
    text_lower = text.lower()
    scores = {}
    
    for module, keywords in MODULE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[module] = score

    if max(scores.values()) == 0:
        return None
    
    return max(scores, key=scores.get)

def detect_agent(text: str, module: str) -> str:
    """pick the right agent within a module"""
    text_lower = text.lower()
    task_map = AGENT_TASK_MAP.get(module, {})
    
    for keyword, agent_name in task_map.items():
        if keyword == "default":
            continue
        if keyword in text_lower:
            return agent_name

    return task_map.get("default", "reporter_agent")

def get_agent_class(agent_name: str):
    """returns module path and class name for dynamic import"""
    
    agent_map = {
        "forecaster_agent": ("app.agents.finance.forecaster_agent", "ForecasterAgent"),
        "detector_agent": ("app.agents.finance.detector_agent", "DetectorAgent"),
        "advisor_agent": ("app.agents.finance.advisor_agent", "AdvisorAgent"),
        "reporter_agent": ("app.agents.finance.reporter_agent", "ReporterAgent"),
        "talent_scout_agent": ("app.agents.hr.talent_scout_agent", "TalentScoutAgent"),
        "retention_guard_agent": ("app.agents.hr.retention_guard_agent", "RetentionGuardAgent"),
        "growth_coach_agent": ("app.agents.hr.growth_coach_agent", "GrowthCoachAgent"),
        "culture_builder_agent": ("app.agents.hr.culture_builder_agent", "CultureBuilderAgent"),
        "demand_planner_agent": ("app.agents.operations.demand_planner_agent", "DemandPlannerAgent"),
        "supply_optimizer_agent": ("app.agents.operations.supply_optimizer_agent", "SupplyOptimizerAgent"),
        "logistics_coordinator_agent": ("app.agents.operations.logistics_coordinator_agent", "LogisticsCoordinatorAgent"),
        "quality_guardian_agent": ("app.agents.operations.quality_guardian_agent", "QualityGuardianAgent"),
        "revenue_forecaster_agent": ("app.agents.sales.revenue_forecaster_agent", "RevenueForecasterAgent"),
        "churn_guardian_agent": ("app.agents.sales.churn_guardian_agent", "ChurnGuardianAgent"),
        "deal_strategist_agent": ("app.agents.sales.deal_strategist_agent", "DealStrategistAgent"),
        "sales_coach_agent": ("app.agents.sales.sales_coach_agent", "SalesCoachAgent"),
        "ticket_resolver_agent": ("app.agents.support.ticket_resolver_agent", "TicketResolverAgent"),
        "sentiment_analyst_agent": ("app.agents.support.sentiment_analyst_agent", "SentimentAnalystAgent"),
        "knowledge_curator_agent": ("app.agents.support.knowledge_curator_agent", "KnowledgeCuratorAgent"),
        "quality_analyst_agent": ("app.agents.support.quality_analyst_agent", "QualityAnalystAgent"),
    }
    return agent_map.get(agent_name)

class AgentCoordinator:
    """
    main coordinator class
    takes user input, figures out which agent to use, runs it and returns result
    """

    def __init__(self, tenant_id: str, llm_url: str, rag_url: str,
                 db_session=None, redis=None, config: Dict = None):
        self.tenant_id = tenant_id
        self.llm_url = llm_url
        self.rag_url = rag_url
        self.db = db_session
        self.redis = redis
        self.config = config or {}

    def _load_agent(self, agent_name: str):
        """dynamically load and create an agent instance"""
        mapping = get_agent_class(agent_name)
        if not mapping:
            raise ValueError(f"agent not found: {agent_name}")
        
        module_path, class_name = mapping
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        
        return cls(
            tenant_id=self.tenant_id,
            llm_gateway_url=self.llm_url,
            rag_service_url=self.rag_url,
            db_session=self.db,
            redis_client=self.redis,
            config=self.config
        )

    async def route_and_run(
        self, 
        user_input: str, 
        context: Dict = None,
        force_agent: str = None, 
        force_module: str = None
    ) -> Dict[str, Any]:

        if force_agent:
            agent_name = force_agent
        else:
            
            module = force_module or detect_module(user_input)
            
            if not module:
                
                return {
                    "response": "Sorry I'm not sure what you're asking about. Please mention if its related to Finance, HR, Operations, Sales or Support.",
                    "agent": "coordinator",
                    "module": "unknown"
                }
            
            agent_name = detect_agent(user_input, module)

        agent = self._load_agent(agent_name)
        result = await agent.run(user_input, context)
        return result
