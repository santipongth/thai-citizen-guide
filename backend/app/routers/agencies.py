"""
REST API routes for agency management.

Endpoints
---------
  GET    /agencies                          List agencies (with optional filters)
  POST   /agencies                          Create a new agency
  POST   /agencies/parse-spec               Parse an OpenAPI spec via LLM
  GET    /agencies/{id}                     Get a single agency
  PUT    /agencies/{id}                     Full replace of an agency
  PATCH  /agencies/{id}                     Partial update of an agency
  DELETE /agencies/{id}                     Delete an agency
  POST   /agencies/{id}/increment-calls     Increment the total_calls counter
  POST   /agencies/{id}/test                Test agency connection
  GET    /agencies/{id}/connection-logs     List connection logs for an agency
"""

import asyncio
import json as _json
import random
import time
import uuid
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from tortoise.exceptions import DoesNotExist

from app.config import settings
from app.models.agency import Agency
from app.models.connection_log import ConnectionLog
from app.schemas.agency import (
    AgencyCreate,
    AgencyListResponse,
    AgencyResponse,
    AgencyUpdate,
)

router = APIRouter(prefix="/agencies", tags=["Agencies"])


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_model=AgencyListResponse, summary="List agencies")
async def list_agencies(
    status_filter: Literal["active", "inactive", "all"] = Query(
        "all", alias="status", description="Filter by agency status"
    ),
    connection_type: str | None = Query(None, description="Filter by connection type: MCP, API, A2A"),
    search: str | None = Query(None, description="Search by name or short_name"),
):
    qs = Agency.all()

    if status_filter != "all":
        qs = qs.filter(status=status_filter)

    if connection_type:
        qs = qs.filter(connection_type=connection_type.upper())

    if search:
        qs = qs.filter(name__icontains=search)

    agencies = await qs
    total = await qs.count()

    return AgencyListResponse(
        data=[AgencyResponse.model_validate(a) for a in agencies],
        total=total,
    )


# ---------------------------------------------------------------------------
# Get single
# ---------------------------------------------------------------------------

@router.get("/{agency_id}", response_model=AgencyResponse, summary="Get agency by ID")
async def get_agency(agency_id: uuid.UUID):
    try:
        agency = await Agency.get(id=agency_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    return AgencyResponse.model_validate(agency)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post("", response_model=AgencyResponse, status_code=status.HTTP_201_CREATED, summary="Create agency")
async def create_agency(body: AgencyCreate):
    data = body.model_dump()

    # Serialise nested Pydantic objects to plain dicts for JSON fields
    data["api_endpoints"] = [e.model_dump() for e in body.api_endpoints]
    data["response_schema"] = [f.model_dump() for f in body.response_schema]

    agency = await Agency.create(**data)
    return AgencyResponse.model_validate(agency)


# ---------------------------------------------------------------------------
# Full update (PUT)
# ---------------------------------------------------------------------------

@router.put("/{agency_id}", response_model=AgencyResponse, summary="Replace agency")
async def replace_agency(agency_id: uuid.UUID, body: AgencyCreate):
    try:
        agency = await Agency.get(id=agency_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    data = body.model_dump()
    data["api_endpoints"] = [e.model_dump() for e in body.api_endpoints]
    data["response_schema"] = [f.model_dump() for f in body.response_schema]

    await agency.update_from_dict(data).save()
    return AgencyResponse.model_validate(agency)


# ---------------------------------------------------------------------------
# Partial update (PATCH)
# ---------------------------------------------------------------------------

@router.patch("/{agency_id}", response_model=AgencyResponse, summary="Partial update agency")
async def update_agency(agency_id: uuid.UUID, body: AgencyUpdate):
    try:
        agency = await Agency.get(id=agency_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    update_data = body.model_dump(exclude_unset=True)

    # Serialise nested objects if present
    if "api_endpoints" in update_data and update_data["api_endpoints"] is not None:
        update_data["api_endpoints"] = [
            e.model_dump() if hasattr(e, "model_dump") else e
            for e in update_data["api_endpoints"]
        ]
    if "response_schema" in update_data and update_data["response_schema"] is not None:
        update_data["response_schema"] = [
            f.model_dump() if hasattr(f, "model_dump") else f
            for f in update_data["response_schema"]
        ]

    await agency.update_from_dict(update_data).save()
    return AgencyResponse.model_validate(agency)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete("/{agency_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete agency")
async def delete_agency(agency_id: uuid.UUID):
    try:
        agency = await Agency.get(id=agency_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    await agency.delete()


# ---------------------------------------------------------------------------
# Increment total_calls
# ---------------------------------------------------------------------------

@router.post(
    "/{agency_id}/increment-calls",
    response_model=AgencyResponse,
    summary="Increment agency call counter",
)
async def increment_calls(agency_id: uuid.UUID):
    try:
        agency = await Agency.get(id=agency_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    agency.total_calls += 1
    await agency.save(update_fields=["total_calls"])
    return AgencyResponse.model_validate(agency)


# ---------------------------------------------------------------------------
# Connection logs
# ---------------------------------------------------------------------------

class ConnectionLogResponse(BaseModel):
    id: str
    agency_id: str
    action: str
    connection_type: str
    status: str
    latency_ms: int
    detail: str
    created_at: str

    class Config:
        from_attributes = True


@router.get(
    "/{agency_id}/connection-logs",
    response_model=list[ConnectionLogResponse],
    summary="List connection logs for an agency",
)
async def list_connection_logs(agency_id: uuid.UUID, limit: int = Query(50, le=200)):
    try:
        agency = await Agency.get(id=agency_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    logs = await ConnectionLog.filter(agency=agency).limit(limit)
    return [
        ConnectionLogResponse(
            id=str(log.id),
            agency_id=str(agency_id),
            action=log.action,
            connection_type=log.connection_type,
            status=log.status,
            latency_ms=log.latency_ms,
            detail=log.detail,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]


# ---------------------------------------------------------------------------
# Test connection
# ---------------------------------------------------------------------------

class TestConnectionRequest(BaseModel):
    connection_type: str
    endpoint_url: str | None = None


@router.post(
    "/{agency_id}/test",
    summary="Test agency connection and record a connection log",
)
async def test_connection(agency_id: uuid.UUID, body: TestConnectionRequest):
    try:
        agency = await Agency.get(id=agency_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    result = await _run_connection_test(body.connection_type, body.endpoint_url or "")

    # Persist log
    latency_raw = result.get("latency", "0ms")
    latency_ms = int(latency_raw.replace("ms", "")) if isinstance(latency_raw, str) else 0
    await ConnectionLog.create(
        agency=agency,
        action="test",
        connection_type=body.connection_type,
        status="success" if result.get("success") else "error",
        latency_ms=latency_ms,
        detail=result.get("error") or f"HTTP {result.get('statusCode', '-')}" if body.connection_type == "API" else result.get("protocol", ""),
    )

    return result


async def _run_connection_test(connection_type: str, endpoint_url: str) -> dict[str, Any]:
    """Port of the Supabase agency-manage handleTest function."""

    # MCP / A2A — simulated test (no real endpoint to ping)
    if connection_type in ("MCP", "A2A"):
        return await _simulated_test(connection_type)

    # Real HTTP connection test for API type
    url = endpoint_url.strip()
    if not url:
        return {
            "success": False,
            "protocol": "REST API",
            "version": "-",
            "steps": [],
            "latency": "0ms",
            "error": "Endpoint URL is required",
        }

    steps: list[dict] = []
    total_start = time.monotonic()

    async with httpx.AsyncClient(timeout=10.0) as client:
        s1 = time.monotonic()
        response = None
        fetch_error: str | None = None

        headers = {"User-Agent": "AI-Chatbot-Portal/1.0 ConnectionTest"}
        try:
            response = await client.head(url, headers=headers)
        except Exception:
            try:
                response = await client.get(url, headers=headers)
            except httpx.TimeoutException:
                fetch_error = "Connection timeout (10s)"
            except Exception as exc:
                fetch_error = str(exc)

        s1_ms = int((time.monotonic() - s1) * 1000)

    steps.append({"step": 1, "label": "TCP Connection", "status": "error" if fetch_error else "done", "time": s1_ms})

    if fetch_error:
        total_ms = int((time.monotonic() - total_start) * 1000)
        steps.append({"step": 2, "label": "HTTP Response", "status": "error", "time": 0})
        return {"success": False, "protocol": "REST API", "version": "-", "steps": steps, "latency": f"{total_ms}ms", "error": fetch_error}

    status_code = response.status_code
    steps.append({"step": 2, "label": f"HTTP {status_code} {response.reason_phrase}", "status": "done" if status_code < 500 else "error", "time": s1_ms})

    content_type = response.headers.get("content-type", "unknown").split(";")[0]
    server = response.headers.get("server", "unknown")
    steps.append({"step": 3, "label": f"Content-Type: {content_type}", "status": "done", "time": 0})

    total_ms = int((time.monotonic() - total_start) * 1000)
    is_success = 200 <= status_code < 500
    steps.append({"step": 4, "label": "API Reachable" if is_success else "API Error", "status": "done" if is_success else "error", "time": 0})

    return {
        "success": is_success,
        "protocol": "REST API",
        "version": "v1",
        "steps": steps,
        "latency": f"{total_ms}ms",
        "statusCode": status_code,
        "statusText": response.reason_phrase,
        "server": server,
        "contentType": content_type,
    }


async def _simulated_test(connection_type: str) -> dict[str, Any]:
    delay = 0.1 + random.random() * 0.3
    await asyncio.sleep(delay)
    latency = int(delay * 1000)

    if connection_type == "MCP":
        return {
            "success": True,
            "protocol": "MCP",
            "version": "1.0",
            "steps": [
                {"step": 1, "label": "TCP Connection", "status": "done", "time": round(latency * 0.2)},
                {"step": 2, "label": "MCP Handshake", "status": "done", "time": round(latency * 0.4)},
                {"step": 3, "label": "Capability Exchange", "status": "done", "time": round(latency * 0.3)},
                {"step": 4, "label": "Session Established", "status": "done", "time": round(latency * 0.1)},
            ],
            "capabilities": ["tools/list", "tools/call", "resources/read"],
            "latency": f"{latency}ms",
        }
    return {
        "success": True,
        "protocol": "A2A",
        "version": "0.2",
        "steps": [
            {"step": 1, "label": "DNS Resolution", "status": "done", "time": round(latency * 0.15)},
            {"step": 2, "label": "Agent Card Request", "status": "done", "time": round(latency * 0.35)},
            {"step": 3, "label": "Capability Negotiation", "status": "done", "time": round(latency * 0.30)},
            {"step": 4, "label": "Agent Link Ready", "status": "done", "time": round(latency * 0.20)},
        ],
        "agentCard": {"name": "Remote Agent", "skills": ["query", "verify"]},
        "latency": f"{latency}ms",
    }


# ---------------------------------------------------------------------------
# Parse API spec (LLM-assisted)
# ---------------------------------------------------------------------------

class ParseSpecRequest(BaseModel):
    spec_text: str


@router.post("/parse-spec", summary="Parse an OpenAPI spec via LLM and extract structured metadata")
async def parse_api_spec(body: ParseSpecRequest):
    if not body.spec_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="spec_text is required")

    if not settings.LLM_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM API key not configured")

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an API specification parser. Extract structured information from OpenAPI/Swagger specs including response schemas.",
            },
            {
                "role": "user",
                "content": f"Parse this API specification and extract the details including response field schemas:\n\n{body.spec_text[:30000]}",
            },
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "extract_api_spec",
                    "description": "Extract structured API specification details including response schemas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "auth_method": {"type": "string", "enum": ["api_key", "oauth2", "basic_auth", "none"]},
                            "auth_header": {"type": "string"},
                            "base_path": {"type": "string"},
                            "rate_limit_rpm": {"type": "integer"},
                            "request_format": {"type": "string", "enum": ["json", "xml"]},
                            "endpoints": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                                        "path": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                    "required": ["method", "path", "description"],
                                    "additionalProperties": False,
                                },
                            },
                            "response_schema": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "field": {"type": "string"},
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                        "example": {"type": "string"},
                                    },
                                    "required": ["field", "type", "description"],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "required": ["auth_method", "auth_header", "base_path", "request_format", "endpoints", "response_schema"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
        "tool_choice": {"type": "function", "function": {"name": "extract_api_spec"}},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                settings.LLM_API_URL,
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
                json=payload,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LLM gateway error: {exc}")

    if resp.status_code == 429:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded, please try again later")
    if resp.status_code == 402:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment required")
    if not resp.is_success:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM gateway error")

    data = resp.json()
    tool_call = (data.get("choices") or [{}])[0].get("message", {}).get("tool_calls", [{}])[0]
    args_raw = tool_call.get("function", {}).get("arguments")

    if not args_raw:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to parse specification")

    parsed = _json.loads(args_raw)
    return {"success": True, "data": parsed}
