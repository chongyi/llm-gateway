
import asyncio
import pytest
from sqlalchemy import text
from app.db.session import init_db, engine

async def verify_columns():
    # Run the initialization which triggers migrations
    await init_db()
    
    async with engine.connect() as conn:
        # Check if columns exist by selecting them (limit 0 to avoid fetching data)
        try:
            await conn.execute(text("SELECT request_protocol, supplier_protocol, converted_request_body, upstream_response_body FROM request_logs LIMIT 0"))
            print("SUCCESS: Columns exist.")
        except Exception as e:
            print(f"FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(verify_columns())
