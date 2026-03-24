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

from app.models.agency import Agency

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

def _serialize(value):
    """JSON-serialise datetime and UUID objects."""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)

@mcp.resource("agencies://list")
async def list_agency_resource() -> str:
    """
    Return a JSON array of all *active* government agencies.
    """
    return json.dumps(await _fetch_agencies(), default=_serialize, ensure_ascii=False, indent=2)

@mcp.tool("list_agency", description="Return a JSON array of all active government agencies.")
async def list_agency_tool() -> dict:
    """
    Tool wrapper for list_agency_resource, which returns a JSON string.
    """
    
    agencies = await _fetch_agencies()

    return {"agencies": agencies, "total": len(agencies)}

async def _fetch_agencies() -> dict:
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
    
    agencies = await Agency.filter(status="active").values(
        "id",
        "name",
        "description",
        "connection_type",
        "data_scope",
        "endpoint_url",
        "expected_payload",
    )

    # for agency in agencies:
    #     agency["expected_payload"] = {
    #         "session_id": { "type": "string", "description": "Unique identifier for the chat session" },
    #         "query": { "type": "string", "description": "User's natural language query" },
    #     }

    return agencies

from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "mcp-server"})