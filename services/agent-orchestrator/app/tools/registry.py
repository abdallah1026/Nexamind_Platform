from typing import Dict, Type
from .sql_tool import SQLTool
from .calculation_tool import CalculationTool
from .rag_tool import RAGTool
from .api_tool import APITool
from .document_tool import DocumentTool
from .webhook_tool import WebhookTool
from .email_tool import EmailTool

TOOL_REGISTRY: Dict[str, type] = {
    "sql_tool": SQLTool,
    "calculation_tool": CalculationTool,
    "rag_tool": RAGTool,
    "api_tool": APITool,
    "document_tool": DocumentTool,
    "webhook_tool": WebhookTool,
    "email_tool": EmailTool,
}

def get_tool(name: str, **kwargs):
    cls = TOOL_REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown tool: {name}")
    return cls(**kwargs)
