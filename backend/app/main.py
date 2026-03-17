from fastapi import FastAPI
from fastmcp import FastMCP

mcp = FastMCP("thai-citizen-guide-mcp")

mcp_app = mcp.http_app(path="/")

app = FastAPI(lifespan=mcp_app.lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.mount("/mcp", mcp_app)