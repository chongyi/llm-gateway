
import asyncio
import httpx

async def main():
    url = "https://httpbin.org/headers"
    
    print("--- Case 1: No headers ---")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        print(resp.json()['headers'].get('Accept-Encoding'))

    print("\n--- Case 2: Explicit headers without Accept-Encoding ---")
    headers = {"User-Agent": "test-agent"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        print(resp.json()['headers'].get('Accept-Encoding'))

    print("\n--- Case 3: Explicit Accept-Encoding: gzip ---")
    headers = {"Accept-Encoding": "gzip"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        print(resp.json()['headers'].get('Accept-Encoding'))

if __name__ == "__main__":
    asyncio.run(main())
