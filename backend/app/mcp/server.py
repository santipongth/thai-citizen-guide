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
        "Each agency contains: id, name, short_name, logo, description, connection_type "
        "(MCP | API | A2A), status (active | inactive), data_scope (list of data categories), "
        "endpoint_url, total_calls, color, created_at, updated_at.\n\n"
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

    Each item contains:
    - id, name, short_name, logo
    - connection_type  (MCP | API | A2A)
    - status           (active | inactive)
    - data_scope       list of data categories this agency covers
    - endpoint_url     base URL of the agency's API
    - total_calls      lifetime call counter
    - color            UI accent colour (hex or Tailwind class)
    - created_at / updated_at
    """
    return await _fetch_agencies()

@mcp.tool("list_agency", description="Return a JSON array of all active government agencies.")
async def list_agency_tool() -> str:
    """
    Tool wrapper for list_agency_resource, which returns a JSON string.
    """
    return await _fetch_agencies()

async def _fetch_agencies() -> str:
    """
    Return a JSON array of all *active* government agencies.

    Each item contains:
    - id, name, short_name, logo
    - connection_type  (MCP | API | A2A)
    - status           (active | inactive)
    - data_scope       list of data categories this agency covers
    - endpoint_url     base URL of the agency's API
    - total_calls      lifetime call counter
    - color            UI accent colour (hex or Tailwind class)
    - created_at / updated_at
    """
    
    agencies = await Agency.filter(status="active").values(
        "id",
        "name",
        "short_name",
        "logo",
        "description",
        "connection_type",
        "status",
        "data_scope",
        "endpoint_url",
        "total_calls",
        "color",
        "created_at",
        "updated_at",
    )

    return json.dumps(
        {"agencies": agencies, "total": len(agencies)},
        default=_serialize,
        ensure_ascii=False,
        indent=2,
    )