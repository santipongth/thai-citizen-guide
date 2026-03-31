import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from tortoise.exceptions import DoesNotExist
from app.models import Agency, ConnectionLog, User
from app.auth.dependencies import require_admin

router = APIRouter(prefix="/connection-logs", tags=["Connection Logs"])

# ---------------------------------------------------------------------------
# Connection logs
# ---------------------------------------------------------------------------

class ConnectionLogItem(BaseModel):
    id: str
    agency_id: str
    action: str
    connection_type: str
    status: str
    latency_ms: int
    detail: str
    created_at: str

class ListConnectionLogResponse(BaseModel):
    search: str | None = None
    page: int
    page_size: int

    items: list[ConnectionLogItem]
    total_items: int

@router.get(
    "",
    
    response_model=ListConnectionLogResponse,
    summary="List connection logs",
)
async def list_connection_logs(
    search: str | None = Query(None, description="Search in detail"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
)-> ListConnectionLogResponse:
    
    start = time.time()

    qs = ConnectionLog.all()

    if search:
        qs = qs.filter(detail__icontains=search)

    qs_pagination = qs

    if page and limit:
        offset = (page - 1) * limit
        qs_pagination = qs.offset(offset).limit(limit)

    logs = await qs_pagination.order_by("-created_at")

    return ListConnectionLogResponse(
        search=search,
        page=page,
        page_size=limit,
        items=[
            ConnectionLogItem(
                id=str(log.id),
                agency_id=str(log.agency_id) if log.agency_id else "",
                action=log.action,
                connection_type=log.connection_type,
                status=log.status,
                latency_ms=log.latency_ms,
                detail=log.detail,
                created_at=log.created_at.isoformat(),
            )
            for log in logs
        ],
        total_items=await qs.count()
    )
