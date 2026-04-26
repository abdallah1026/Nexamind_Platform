from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/v1/hr", tags=["Hr"])

class ModuleRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None

@router.post("/{endpoint:path}")
async def handle_request(
    endpoint: str,
    request: ModuleRequest,
    x_tenant_id: Optional[str] = Header(None)
):
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    from ..main import get_coordinator
    coordinator = await get_coordinator(x_tenant_id)
    query = request.query or endpoint.replace("/", " ").replace("-", " ")
    result = await coordinator.route_and_run(
        query, context=request.context, force_module="hr"
    )
    return result
