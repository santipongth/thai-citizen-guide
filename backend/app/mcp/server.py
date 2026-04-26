"""
FastMCP Server — AI Chatbot Portal
Exposes agency data as MCP resources so LLM clients (e.g. Claude) can
discover which government agencies are available and how to reach them.

Registered resources
--------------------
  agencies://list → list_agency()   All active agencies (summary)

Registered tools
----------------
    list_agency → list_agency()   All active agencies (summary)
"""

import json
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext
from starlette.datastructures import URLPath

from app.models.agency import Agency
from app.models.user import User

mcp = FastMCP(
    name="AI Chatbot Portal MCP",
    instructions=(
        "This server exposes Thai government agency data for the AI Chatbot Portal.\n\n"
        "Available tool:\n"
        "- list_agency: Returns a JSON object with an `agencies` array and `total` count. "
        "Each agency contains: id, name, description, connection_type "
        "(MCP | API | A2A), data_scope (list of data categories), "
        "endpoint_url, expected_payload.\n\n"
        "Always call list_agency before answering questions about available agencies. "
        "Never fabricate agency data."
    ),
)

class AuthMiddleware(Middleware):
    async def on_request(self, ctx: MiddlewareContext, call_next):

        user = await ctx.fastmcp_context.get_state("user_id") or None

        if not user:
            token = get_http_request().headers.get("Authorization", "Bearer anonymous")
            user = await User.filter(api_keys__key=token.split(" ")[-1]).first()
            if user: await ctx.fastmcp_context.set_state("user_id", user.id)
            if user: await ctx.fastmcp_context.set_state("user_is_admin", user.is_admin)

        return await call_next(ctx)

mcp.add_middleware(AuthMiddleware())

def _serialize(value):
    """JSON-serialise datetime and UUID objects."""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)

@mcp.resource("agencies://list")
async def list_agency_resource(ctx: Context = CurrentContext()) -> str:
    """
    Return a JSON array of all *active* government agencies.
    """
    return json.dumps(await _fetch_agencies(ctx), default=_serialize, ensure_ascii=False, indent=2)

@mcp.tool("list_agency", description="Return a JSON array of all active government agencies.")
async def list_agency_tool(ctx: Context = CurrentContext()) -> dict:
    """
    Tool wrapper for list_agency_resource, which returns a JSON string.
    """
    
    agencies = await _fetch_agencies(ctx)

    return {"agencies": agencies, "total": len(agencies)}

async def _fetch_agencies(ctx: Context) -> dict:
    """
    Return a JSON array of all *active* government agencies.

    Each item contains:
    - id
    - name
    - description
    - connection_type  (MCP | API | A2A)
    - data_scope       list of data categories this agency covers
    - endpoint_url     base URL of the agency's API
    - expected_payload example JSON payload for API calls
    """

    request = get_http_request()
    http_host = request.headers.get("X-Forwarded-Host")

    user_is_admin = await ctx.get_state("user_is_admin")
    
    agencies = await Agency.filter(status="active").values(
        "id",
        "name",
        "description",
        "connection_type",
        "data_scope",
        "endpoint_url",
        "expected_payload",
        "api_headers",
    )

    for index, agency in enumerate(agencies):
        if agency["api_headers"] is None:
            agencies[index]["api_headers"] = []
        
        for j, header in enumerate(agency["api_headers"]):
            if header.get("name").lower() == "authorization" and not user_is_admin:
                agencies[index]["api_headers"][j]["value"] = "REDACTED"

        if agency["connection_type"] == "API":
            agency["endpoint_url"] = f"{request.url.scheme}://{http_host}/agent-proxy/{agency['id']}"

    return agencies

from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "mcp-server"})