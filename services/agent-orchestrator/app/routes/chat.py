from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    agent: Optional[str] = None
    module: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    agent: str
    module: str
    session_id: Optional[str]
    metadata: Optional[Dict] = None

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_tenant_id: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
):
    from ..main import get_coordinator
    
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    
    coordinator = await get_coordinator(x_tenant_id)
    result = await coordinator.route_and_run(
        request.message,
        context=request.context,
        force_agent=request.agent,
        force_module=request.module
    )
    
    return ChatResponse(
        response=result.get("response", ""),
        agent=result.get("agent", "unknown"),
        module=result.get("module", "unknown"),
        session_id=request.session_id,
        metadata={k: v for k, v in result.items() if k not in ("response", "agent", "module")}
    )

@router.get("/agents")
async def list_agents():
    from ..orchestrator.coordinator import AGENT_TASK_MAP
    agents = []
    for module, task_map in AGENT_TASK_MAP.items():
        seen = set()
        for agent_name in task_map.values():
            if agent_name not in seen:
                seen.add(agent_name)
                agents.append({"name": agent_name, "module": module})
    return {"agents": agents, "count": len(agents)}

@router.get("/agents/{agent_id}/status")
async def agent_status(agent_id: str, x_tenant_id: Optional[str] = Header(None)):
    from ..orchestrator.coordinator import get_agent_class
    mapping = get_agent_class(agent_id)
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return {"agent_id": agent_id, "status": "ready", "available": True}

@router.post("/agents/{agent_id}/invoke")
async def invoke_agent(
    agent_id: str,
    request: ChatRequest,
    x_tenant_id: Optional[str] = Header(None)
):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    
    request.agent = agent_id
    return await chat(request, x_tenant_id=x_tenant_id)
