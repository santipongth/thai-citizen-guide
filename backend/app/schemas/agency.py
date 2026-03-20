from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------

class ApiEndpoint(BaseModel):
    method: str = Field(..., examples=["GET", "POST"])
    path: str = Field(..., examples=["/search"])
    description: str = Field(default="")


class ResponseField(BaseModel):
    field: str
    type: str = Field(..., examples=["string", "number", "boolean"])
    description: str = Field(default="")
    example: Any = None


# ---------------------------------------------------------------------------
# Agency schemas
# ---------------------------------------------------------------------------

class AgencyBase(BaseModel):
    name: str
    short_name: str | None = None
    logo: str | None = None
    description: str | None = None
    connection_type: str = "API"
    status: str = "active"
    data_scope: list[str] = []
    color: str | None = None

    # Connection
    endpoint_url: str | None = None
    auth_method: str | None = None
    auth_header: str | None = None
    base_path: str | None = None
    api_key_name: str | None = None
    rate_limit_rpm: int | None = None
    request_format: str | None = None

    # Schema / spec
    api_endpoints: list[ApiEndpoint] = []
    response_schema: list[ResponseField] = []
    api_spec_raw: str | None = None


class AgencyCreate(AgencyBase):
    """Request body for creating a new agency."""
    pass


class AgencyUpdate(BaseModel):
    """Request body for partial update of an agency (all fields optional)."""
    name: str | None = None
    short_name: str | None = None
    logo: str | None = None
    description: str | None = None
    connection_type: str | None = None
    status: str | None = None
    data_scope: list[str] | None = None
    color: str | None = None
    endpoint_url: str | None = None
    auth_method: str | None = None
    auth_header: str | None = None
    base_path: str | None = None
    api_key_name: str | None = None
    rate_limit_rpm: int | None = None
    request_format: str | None = None
    api_endpoints: list[ApiEndpoint] | None = None
    response_schema: list[ResponseField] | None = None
    api_spec_raw: str | None = None


class AgencyResponse(AgencyBase):
    """Response schema — includes server-generated fields."""
    id: uuid.UUID
    total_calls: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgencyListResponse(BaseModel):
    """Paginated list of agencies."""
    data: list[AgencyResponse]
    total: int


# ---------------------------------------------------------------------------
# Summary schema used by MCP resource (lightweight)
# ---------------------------------------------------------------------------

class AgencySummary(BaseModel):
    id: uuid.UUID
    name: str
    short_name: str | None
    logo: str | None
    connection_type: str
    status: str
    data_scope: list[str]
    total_calls: int
    color: str | None

    model_config = ConfigDict(from_attributes=True)
