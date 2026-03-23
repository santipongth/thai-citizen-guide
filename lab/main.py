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

async def main():
    client = MultiServerMCPClient({
        "agency": {
            "transport": "http",
            "url": "http://185.84.161.24/mcp/",
        }
    })

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
    
    for message in result["messages"]:
        print(f"{message.__class__.__name__}: ", end="")
        # content = re.sub(r"<think>.*?</think>", "", message.content, flags=re.DOTALL).strip()
        print(message.content)

if __name__ == "__main__":
    asyncio.run(main())