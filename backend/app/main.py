"""
AI Chatbot Portal — FastAPI Backend
=====================================
Stack:  FastAPI · Tortoise ORM · FastMCP
DB:     PostgreSQL

Entry-point:
    uvicorn app.main:app --reload

MCP server is mounted at /mcp  (SSE transport)
REST API is served under /api/v1
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.mcp.server import mcp
from app.routers import agencies, conversations, messages, chat, dashboard, feedback, auth, seed
from app.routers.seed import _run_seed_admin, _run_seed_agencies

mcp_app = mcp.http_app(path="/")

# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _run_seed_admin()
    await _run_seed_agencies()

    async with mcp_app.lifespan(app):
        yield

    await close_db()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Central AI Chatbot Portal API.\n\n"
        "**MCP server** (for LLM clients) is available at `/mcp/`.\n\n"
        "**REST API** endpoints are under `/api/v1`."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# REST routers
# ---------------------------------------------------------------------------

app.include_router(auth.router, prefix="/api/v1")
# app.include_router(seed.router, prefix="/api/v1")
app.include_router(agencies.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# MCP server — mount as sub-application
# ---------------------------------------------------------------------------

app.mount("/mcp", mcp_app)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
