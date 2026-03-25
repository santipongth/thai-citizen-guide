import re
import asyncio
import os

import dotenv
dotenv.load_dotenv()

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

model = ChatOpenAI(
    model="/model",
    temperature=0.0,

    openai_api_key="sk-placeholder",
    openai_api_base="http://thaillm.or.th/api/pathumma/v1",
    default_headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "apikey": os.getenv("LLM_EXTRA_APIKEY", ""),
    },
)

llm = create_agent(model)

mcp_client = MultiServerMCPClient({
    "agency": {
        "transport": "http",
        "url": "http://185.84.161.24/mcp",
    }
})

# ------------------------------------------------------------
# Router node system prompt and helper functions
# ------------------------------------------------------------

ROUTER_SYSTEM_PROMPT = """Analyze this query and determine which government agencies to consult.
For each relevant agency, generate a targeted sub-question optimized for that agency's data scope.

Available sources:
{available_sources}

Return ONLY the agencies that are relevant to the query.
Respond in JSON format:
{{
  "routes": [
    {{
      "agency_id": "<uuid>",
      "agency_name": "<name>",
      "connection_type": "<A2A|API|MCP>",
      "sub_question": "<targeted question optimized for this agency's domain>"
    }}
  ]
}}"""

def format_available_sources(agencies: list[dict]) -> str:
    """แปลง list_agency response เป็น available sources block สำหรับ prompt"""
    lines = []
    for ag in agencies:
        scope = ", ".join(ag["data_scope"])
        lines.append(
            f'- {ag["name"]} (id: {ag["id"]}, type: {ag["connection_type"]}): '
            f'{ag["description"]} — ขอบเขตข้อมูล: {scope}'
        )
    return "\n".join(lines)

async def router_node(state: AgentState) -> dict:
    # 1) ดึง agency list จาก MCP tool
    agencies_response = await mcp_client.call_tool("list_agency")
    agencies = agencies_response["agencies"]

    # 2) สร้าง prompt
    sources_block = format_available_sources(agencies)
    system_prompt = ROUTER_SYSTEM_PROMPT.format(available_sources=sources_block)

    # 3) ให้ LLM route
    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["query"]),
    ])

    routes = parse_json(response.content)["routes"]

    # 4) สร้าง lookup map สำหรับ downstream nodes
    agency_map = {ag["id"]: ag for ag in agencies}
    for route in routes:
        route["endpoint_url"] = agency_map[route["agency_id"]]["endpoint_url"]
        route["expected_payload"] = agency_map[route["agency_id"]].get("expected_payload")

    return {"routes": routes, "agency_map": agency_map}

# ------------------------------------------------------------
# Main function to test the router node
# ------------------------------------------------------------

async def main():

    tools = await client.get_tools()
    # print(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")

    agent = create_agent(model, tools=tools)

    result = await agent.ainvoke({
        "messages": [
            SystemMessage(content=(
                "You are an AI assistant for the Thai Government Agency Portal.\n\n"
                "You have access to the following tool:\n"
                "- list_agency: Returns all active Thai government agencies as JSON.\n\n"
                "Each agency has: id, name, short_name, connection_type (MCP | API | A2A), "
                "status, data_scope, endpoint_url, total_calls, color, created_at, updated_at.\n\n"
                "Rules:\n"
                "1. Call list_agency before answering any question about agencies.\n"
                "2. Never fabricate agency data — only use what list_agency returns.\n"
                "3. Respond in the same language the user uses (Thai or English).\n"
                "4. If asked about a specific agency, filter from the returned list."
            )),
            SystemMessage(content="if you receive 'ping', return 'pong'."),
            HumanMessage(content="get agencies data"),
        ]
    })
    
    message = result["messages"][-1].content or ""
    message = re.sub(r'<think>.*?</think>', '', message, flags=re.DOTALL)
    print(message)

if __name__ == "__main__":
    asyncio.run(main())