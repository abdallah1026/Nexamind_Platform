from typing import Dict, List, Any, Optional

class WorkflowNode:
    def __init__(self, agent_name: str, condition: Optional[str] = None):
        self.agent_name = agent_name
        self.condition = condition
        self.next_nodes: List["WorkflowNode"] = []

    def add_next(self, node: "WorkflowNode") -> "WorkflowNode":
        self.next_nodes.append(node)
        return node

class WorkflowGraph:
    """Defines multi-agent workflow DAGs for complex tasks"""
    
    PREDEFINED_WORKFLOWS = {
        "financial_health_check": [
            "reporter_agent",    # Get current state
            "detector_agent",    # Check for anomalies  
            "forecaster_agent",  # Generate outlook
            "advisor_agent",     # Provide recommendations
        ],
        "employee_retention_review": [
            "retention_guard_agent",  # Identify at-risk
            "growth_coach_agent",     # Development gaps
            "culture_builder_agent",  # Engagement issues
        ],
        "sales_pipeline_review": [
            "revenue_forecaster_agent",  # Pipeline analysis
            "churn_guardian_agent",      # At-risk customers
            "deal_strategist_agent",     # Deal coaching
        ],
    }

    @classmethod
    def get_workflow_agents(cls, workflow_name: str) -> List[str]:
        return cls.PREDEFINED_WORKFLOWS.get(workflow_name, [])

    @classmethod
    def list_workflows(cls) -> Dict[str, List[str]]:
        return cls.PREDEFINED_WORKFLOWS
