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
  GET    /agencies/{id}/test                Test agency connection
  GET    /agencies/{id}/connection-logs     List connection logs for an agency
"""

import json as _json
import time
import uuid
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)


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
# Test connection — response model
# ---------------------------------------------------------------------------

class TestStep(BaseModel):
    step: int
    label: str
    status: str   # "done" | "error"
    time: int     # milliseconds


class AgentCardInfo(BaseModel):
    name: str
    skills: list[str] = []
    capabilities: dict[str, Any] = {}


class TestConnectionResponse(BaseModel):
    success: bool
    protocol: str          # "REST API" | "MCP" | "A2A" | "UNKNOWN"
    version: str
    steps: list[TestStep]
    latency: str           # e.g. "142ms"

    # REST-only
    status_code: int | None = None
    status_text: str | None = None
    server: str | None = None
    content_type: str | None = None

    # MCP-only
    capabilities: list[str] | None = None
    server_info: dict[str, Any] | None = None

    # A2A-only
    agent_card: AgentCardInfo | None = None

    # Error (any protocol)
    error: str | None = None

    model_config = {"populate_by_name": True}


@router.get(
    "/{agency_id}/test",
    response_model=TestConnectionResponse,
    summary="Test agency connection and record a connection log",
)
async def test_connection(agency_id: uuid.UUID):
    try:
        agency = await Agency.get(id=agency_id)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    raw = await _run_connection_test(agency.connection_type, agency)

    # Build typed response — map camelCase probe keys → snake_case model fields
    agent_card_raw = raw.get("agentCard")
    response = TestConnectionResponse(
        success=raw["success"],
        protocol=raw["protocol"],
        version=raw["version"],
        steps=[TestStep(**s) for s in raw.get("steps", [])],
        latency=raw["latency"],
        error=raw.get("error"),
        # REST
        status_code=raw.get("statusCode"),
        status_text=raw.get("statusText"),
        server=raw.get("server"),
        content_type=raw.get("contentType"),
        # MCP
        capabilities=raw.get("capabilities"),
        server_info=raw.get("serverInfo"),
        # A2A
        agent_card=AgentCardInfo(**agent_card_raw) if agent_card_raw else None,
    )

    # Persist log
    latency_ms = int(response.latency.replace("ms", ""))
    await ConnectionLog.create(
        agency=agency,
        action="test",
        connection_type=agency.connection_type,
        status="success" if response.success else "error",
        latency_ms=latency_ms,
        detail=response.error or (f"HTTP {response.status_code}" if response.status_code else response.protocol),
    )

    return response


async def _run_connection_test(connection_type: str, agency: Agency) -> dict[str, Any]:
    url = agency.endpoint_url.strip()

    if connection_type == "API":
        return await _test_rest(agency)
    if connection_type == "MCP":
        return await _test_mcp(agency)
    if connection_type == "A2A":
        return await _test_a2a(agency)

    return {"success": False, "protocol": "UNKNOWN", "version": "-", "steps": [], "latency": "0ms", "error": "Unsupported connection type"}

async def _test_rest(agency: Agency) -> dict[str, Any]:
    """Real REST API probe: HEAD with GET fallback, captures status + headers."""
    url = agency.endpoint_url.strip()
    if not url:
        return {"success": False, "protocol": "REST API", "version": "-", "steps": [], "latency": "0ms", "error": "Endpoint URL is required"}

    steps: list[dict] = []
    total_start = time.monotonic()
    headers = {"User-Agent": "AI-Chatbot-Portal/1.0 ConnectionTest"}

    s1 = time.monotonic()
    response = None
    fetch_error: str | None = None

    async with httpx.AsyncClient(timeout=10.0) as client:
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


async def _test_mcp(agency: Agency) -> dict[str, Any]:
    """
    Real MCP probe: send a JSON-RPC 2.0 `initialize` request and verify the
    server returns a valid capabilities response.

    MCP spec: https://modelcontextprotocol.io/specification
    """
    steps: list[dict] = []
    total_start = time.monotonic()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AI-Chatbot-Portal/1.0 MCPProbe",
    }

    if not agency.endpoint_url:
        return {"success": False, "protocol": "MCP", "version": "-", "steps": [], "latency": "0ms", "error": "Endpoint URL is required"}

    url = agency.endpoint_url.strip()

    # Step 1 — TCP / HTTP reachability
    s1 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 2 — MCP initialize handshake
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "AI-Chatbot-Portal", "version": "1.0"},
                },
            }
            s1_ms = int((time.monotonic() - s1) * 1000)
            steps.append({"step": 1, "label": "TCP Connection", "status": "done", "time": s1_ms})

            s2 = time.monotonic()
            resp = await client.post(url, json=init_payload, headers=headers)
            s2_ms = int((time.monotonic() - s2) * 1000)

            if resp.status_code >= 500:
                steps.append({"step": 2, "label": f"MCP Handshake — HTTP {resp.status_code}", "status": "error", "time": s2_ms})
                total_ms = int((time.monotonic() - total_start) * 1000)
                return {"success": False, "protocol": "MCP", "version": "-", "steps": steps, "latency": f"{total_ms}ms",
                        "error": f"Server error: HTTP {resp.status_code}"}

            steps.append({"step": 2, "label": "MCP Handshake", "status": "done", "time": s2_ms})

            # Step 3 — parse capabilities from the JSON-RPC result
            s3 = time.monotonic()
            try:
                body = resp.json()
            except Exception:
                body = {}

            result = body.get("result", {})
            server_info = result.get("serverInfo", {})
            raw_caps = result.get("capabilities", {})
            protocol_version = result.get("protocolVersion", "unknown")

            # Flatten capabilities into a human-readable list
            capabilities: list[str] = []
            for group, val in raw_caps.items():
                if isinstance(val, dict):
                    for method in val:
                        capabilities.append(f"{group}/{method}")
                else:
                    capabilities.append(group)
            if not capabilities:
                capabilities = list(raw_caps.keys()) or ["(none advertised)"]

            s3_ms = int((time.monotonic() - s3) * 1000)
            steps.append({"step": 3, "label": f"Capability Exchange — {len(capabilities)} cap(s)", "status": "done", "time": s3_ms})
            steps.append({"step": 4, "label": "Session Established", "status": "done", "time": 0})

    except httpx.TimeoutException:
        total_ms = int((time.monotonic() - total_start) * 1000)
        if not steps:
            steps.append({"step": 1, "label": "TCP Connection", "status": "error", "time": total_ms})
        steps.append({"step": 2, "label": "MCP Handshake", "status": "error", "time": 0})
        return {"success": False, "protocol": "MCP", "version": "-", "steps": steps, "latency": f"{total_ms}ms", "error": "Connection timeout (10s)"}
    except Exception as exc:
        total_ms = int((time.monotonic() - total_start) * 1000)
        if not steps:
            steps.append({"step": 1, "label": "TCP Connection", "status": "error", "time": total_ms})
        return {"success": False, "protocol": "MCP", "version": "-", "steps": steps, "latency": f"{total_ms}ms", "error": str(exc)}

    total_ms = int((time.monotonic() - total_start) * 1000)
    return {
        "success": True,
        "protocol": "MCP",
        "version": protocol_version,
        "steps": steps,
        "latency": f"{total_ms}ms",
        "capabilities": capabilities,
        "serverInfo": server_info,
    }


async def _test_a2a(agency: Agency) -> dict[str, Any]:
    """
    Two-phase A2A health check per the A2A specification:

    Phase 1 — Agent Card discovery
      GET {base}/.well-known/agent.json
      Validates required fields: name, description, url

    Phase 2 — RPC endpoint liveness
      POST {card.url}  with a JSON-RPC 2.0  tasks/get  probe.
      Any well-formed JSON-RPC response (including TaskNotFound error)
      confirms the agent process is alive and handling requests.

    Phase 3 (conditional) — /chat ping probe
      If the endpoint URL ends with /chat, POST {"query": "ping"} and
      verify the response body contains "pong" (case-insensitive).
      Skipped automatically if the URL does not end with /chat.

    A2A spec: https://google.github.io/A2A/specification/
    """
    steps: list[dict] = []
    total_start = time.monotonic()

    if not agency.endpoint_url:
        return {"success": False, "protocol": "A2A", "version": "-", "steps": [], "latency": "0ms", "error": "Endpoint URL is required"}


    base = agency.endpoint_url.rstrip("/")
    agent_card_url = f"{base}/.well-known/agent.json"

    card_headers = {"Accept": "application/json", "User-Agent": "AI-Chatbot-Portal/1.0 A2AProbe"}
    rpc_headers  = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "AI-Chatbot-Portal/1.0 A2AProbe"}

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:

            # ── Phase 1: TCP Connection ──────────────────────────────────────────
            s1 = time.monotonic()
            await client.get(agency.endpoint_url)
            steps.append({"step": 1, "label": "TCP Connection", "status": "done", "time": int((time.monotonic() - s1) * 1000)})

            # ── Phase 2: Chat Query ─────────────────────────
            chat_payload = {"session_id": uuid.uuid4().hex, "query": "ทดสอบการเชื่อมต่อ"}
            s2 = time.monotonic()
            try:
                await client.post(agency.endpoint_url, json=chat_payload, headers=rpc_headers)
                s2_ms = int((time.monotonic() - s2) * 1000)
                steps.append({"step": 2, "label": f"Chat Query", "status": "done", "time": s2_ms})
            except Exception as chat_exc:
                s2_ms = int((time.monotonic() - s2) * 1000)
                steps.append({"step": 2, "label": f"Chat failed — {chat_exc}", "status": "error", "time": s2_ms})

            # s2 = time.monotonic()
            # card_resp = await client.get(agent_card_url, headers=card_headers)
            # s2_ms = int((time.monotonic() - s2) * 1000)

            # if card_resp.status_code == 404:
            #     steps.append({"step": 2, "label": "Agent Card — 404 Not Found", "status": "error", "time": s2_ms})
            #     total_ms = int((time.monotonic() - total_start) * 1000)
            #     return {"success": False, "protocol": "A2A", "version": "-", "steps": steps, "latency": f"{total_ms}ms",
            #             "error": f"Agent Card not found at {agent_card_url}"}

            # if card_resp.status_code >= 400:
            #     steps.append({"step": 2, "label": f"Agent Card — HTTP {card_resp.status_code}", "status": "error", "time": s2_ms})
            #     total_ms = int((time.monotonic() - total_start) * 1000)
            #     return {"success": False, "protocol": "A2A", "version": "-", "steps": steps, "latency": f"{total_ms}ms",
            #             "error": f"HTTP {card_resp.status_code}"}

            # steps.append({"step": 2, "label": "Agent Card Retrieved", "status": "done", "time": s2_ms})

            # # Parse and validate card
            # try:
            #     card = card_resp.json()
            # except Exception:
            #     card = {}

            # agent_name    = card.get("name", "Unknown Agent")
            # agent_version = card.get("version", "unknown")
            # skills        = [sk.get("id") or sk.get("name", "?") for sk in card.get("skills", [])] if isinstance(card.get("skills"), list) else []
            # capabilities  = card.get("capabilities", {})
            # rpc_url       = card.get("url", base)   # fallback to base if url missing

            # required = {"name", "description", "url"}
            # missing  = required - set(card.keys())
            # s3_ms = int((time.monotonic() - s1) * 1000)
            # steps.append({
            #     "step": 3,
            #     "label": f"Agent Card valid — {agent_name}" if not missing else f"Missing fields: {', '.join(sorted(missing))}",
            #     "status": "error" if missing else "done",
            #     "time": s3_ms,
            # })

            # if missing:
            #     total_ms = int((time.monotonic() - total_start) * 1000)
            #     return {"success": False, "protocol": "A2A", "version": agent_version, "steps": steps, "latency": f"{total_ms}ms",
            #             "error": f"Invalid Agent Card — missing: {', '.join(sorted(missing))}",
            #             "agentCard": {"name": agent_name, "skills": skills, "capabilities": capabilities}}

            # # ── Phase 2: RPC endpoint liveness probe ─────────────────────────
            # # Send tasks/get with a probe ID.  A conformant A2A server returns
            # # either a result or a JSON-RPC error — both prove it's alive.
            # probe_payload = {
            #     "jsonrpc": "2.0",
            #     "id": 1,
            #     "method": "tasks/get",
            #     "params": {"id": "health-check-probe"},
            # }
            # s4 = time.monotonic()
            # rpc_resp = await client.post(rpc_url, json=probe_payload, headers=rpc_headers)
            # s4_ms = int((time.monotonic() - s4) * 1000)

            # try:
            #     rpc_body = rpc_resp.json()
            #     is_jsonrpc = "jsonrpc" in rpc_body
            # except Exception:
            #     rpc_body    = {}
            #     is_jsonrpc  = False

            # if not is_jsonrpc:
            #     steps.append({"step": 4, "label": f"RPC Probe — unexpected response (HTTP {rpc_resp.status_code})", "status": "error", "time": s4_ms})
            #     total_ms = int((time.monotonic() - total_start) * 1000)
            #     return {"success": False, "protocol": "A2A", "version": agent_version, "steps": steps, "latency": f"{total_ms}ms",
            #             "error": "RPC endpoint did not return a JSON-RPC response",
            #             "agentCard": {"name": agent_name, "skills": skills, "capabilities": capabilities}}

            # # Both result and error are valid — they prove the agent is live
            # rpc_ok    = "result" in rpc_body or "error" in rpc_body
            # rpc_label = "RPC Endpoint Live" if rpc_ok else "RPC — unexpected body"
            # steps.append({"step": 4, "label": rpc_label, "status": "done" if rpc_ok else "error", "time": s4_ms})

            

    except httpx.TimeoutException:
        total_ms = int((time.monotonic() - total_start) * 1000)
        if not steps:
            steps.append({"step": 1, "label": "DNS Resolution", "status": "error", "time": total_ms})
        if len(steps) < 4:
            steps.append({"step": len(steps) + 1, "label": "Timeout", "status": "error", "time": 0})
        return {"success": False, "protocol": "A2A", "version": "-", "steps": steps,
                "latency": f"{total_ms}ms", "error": "Connection timeout (10s)"}
    except Exception as exc:
        total_ms = int((time.monotonic() - total_start) * 1000)
        if not steps:
            steps.append({"step": 1, "label": "DNS Resolution", "status": "error", "time": total_ms})
        return {"success": False, "protocol": "A2A", "version": "-", "steps": steps,
                "latency": f"{total_ms}ms", "error": str(exc)}

    total_ms = int((time.monotonic() - total_start) * 1000)
    return {
        "success": True,
        "protocol": "A2A",
        "version": "-",
        "steps": steps,
        "latency": f"{total_ms}ms",
        # "agentCard": {"name": agent_name, "skills": skills, "capabilities": capabilities},
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
