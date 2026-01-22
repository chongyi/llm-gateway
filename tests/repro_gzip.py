
import asyncio
import gzip
import httpx
from fastapi import FastAPI, Request, Response
from uvicorn import Config, Server

# Create a dummy server that returns gzipped content
app = FastAPI()

@app.post("/echo")
async def echo(request: Request):
    body = await request.body()
    # Return gzipped response
    content = b"Hello, World! " * 10
    compressed = gzip.compress(content)
    return Response(
        content=compressed,
        headers={
            "Content-Encoding": "gzip",
            "Content-Type": "text/plain"
        }
    )

async def run_server():
    config = Config(app=app, port=8888, log_level="error")
    server = Server(config)
    await server.serve()

async def run_client():
    # Wait for server to start
    await asyncio.sleep(1)
    
    url = "http://127.0.0.1:8888/echo"
    
    # Case 1: No Accept-Encoding header (httpx default)
    print("--- Case 1: Default httpx headers ---")
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=b"test")
        print(f"Content-Encoding: {resp.headers.get('content-encoding')}")
        print(f"Raw Content (first 20 bytes): {resp.content[:20]}")
        try:
            print(f"Decoded Text: {resp.text[:20]}")
        except Exception as e:
            print(f"Decoded Text Error: {e}")

    # Case 2: Explicit Accept-Encoding: gzip
    print("\n--- Case 2: Explicit Accept-Encoding: gzip ---")
    headers = {"Accept-Encoding": "gzip"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=b"test", headers=headers)
        print(f"Content-Encoding: {resp.headers.get('content-encoding')}")
        print(f"Raw Content (first 20 bytes): {resp.content[:20]}")
        try:
            print(f"Decoded Text: {resp.text[:20]}")
        except Exception as e:
            print(f"Decoded Text Error: {e}")

    # Case 3: Streaming with Explicit Accept-Encoding: gzip
    print("\n--- Case 3: Streaming with Explicit Accept-Encoding: gzip ---")
    headers = {"Accept-Encoding": "gzip"}
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, content=b"test", headers=headers) as resp:
            print(f"Content-Encoding: {resp.headers.get('content-encoding')}")
            chunks = []
            async for chunk in resp.aiter_bytes():
                chunks.append(chunk)
            full_content = b"".join(chunks)
            print(f"Raw Content (first 20 bytes): {full_content[:20]}")
            try:
                print(f"Decoded Text: {full_content.decode('utf-8')[:20]}")
            except Exception as e:
                print(f"Decoded Text Error: {e}")

async def main():
    server_task = asyncio.create_task(run_server())
    try:
        await run_client()
    finally:
        server_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
