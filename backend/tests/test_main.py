"""
Basic tests for the FastAPI application.
"""
import pytest
import httpx

from backend.app.main import app


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test the root endpoint returns expected message."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI 數學語音助教系統 API"}


@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
