import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        payload = {"query":"hello","inputs":{},"user":"asd"}
        response = await client.post("http://localhost:8080/agent-proxy/019dc8b6-74fe-7c36-b2c6-50d239407fe0", json=payload)
        print(response.status_code)
        print(response.text)

if __name__ == "__main__":
    asyncio.run(main())