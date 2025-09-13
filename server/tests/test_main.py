import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Chess Analysis API"

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

# Add more tests for your API endpoints as needed
@pytest.mark.asyncio
async def test_upload_game_invalid_data(client: AsyncClient):
    # Test with missing required fields
    response = await client.post("/api/v1/games/upload", json={})
    assert response.status_code == 422  # Validation error