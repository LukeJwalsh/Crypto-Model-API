import pytest
from httpx import AsyncClient
from fastapi import status
from main import app 

# Health Endpoint Tests
@pytest.mark.asyncio
async def test_health_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/v1/health/")
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {"status": "Health root endpoint"}


@pytest.mark.asyncio
async def test_health_live():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/v1/health/live")
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {"status": "alive"}
    assert res.headers["Cache-Control"] == "no-cache"


@pytest.mark.asyncio
async def test_server_ready():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/v1/health/ready")
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == {"status": "ready"}
    assert res.headers["Cache-Control"] == "no-cache"