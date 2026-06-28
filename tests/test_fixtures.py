import os
import asyncio
import asyncpg
import uuid
import pytest

TENANT_ID = os.getenv("TENANT_ID")
if not TENANT_ID:
    raise RuntimeError("Set TENANT_ID env var before running tests")

DB_URL = "postgresql://postgres:postgres@localhost:5433/nexamind"

async def _conn():
    return await asyncpg.connect(DB_URL)

@pytest.mark.asyncio
async def test_tenant_rows():
    conn = await _conn()
    try:
        
        for table in ("financial_transactions", "employees", "knowledge_articles"):
            count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {table} WHERE tenant_id = $1", TENANT_ID
            )
            assert count > 0, f"{table} has no rows for tenant {TENANT_ID}"
    finally:
        await conn.close()
