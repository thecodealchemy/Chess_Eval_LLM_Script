import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Sample PGN for testing
SAMPLE_PGN = """[Event "Test Game"]
[Site "Test Site"]
[Date "2024.01.01"]
[Round "1"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 1-0"""

@pytest.mark.asyncio
async def test_analyze_move_valid(client: AsyncClient):
    """Test analyzing a valid move"""
    # First upload a game to get a game_id
    upload_response = await client.post("/api/v1/upload_pgn", json={
        "pgn": SAMPLE_PGN
    })
    
    assert upload_response.status_code == 200
    game_id = upload_response.json()["game_id"]
    
    # Now analyze a move
    response = await client.post("/api/v1/analyse_move", json={
        "game_id": game_id,
        "move_index": 1  # First move (e4)
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "eval" in data
    assert "explanation" in data
    assert "variations" in data
    assert isinstance(data["variations"], list)

@pytest.mark.asyncio
async def test_analyze_move_invalid_game_id(client: AsyncClient):
    """Test analyzing move with invalid game ID"""
    response = await client.post("/api/v1/analyse_move", json={
        "game_id": "invalid_id",
        "move_index": 1
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid game ID" in data["detail"]

@pytest.mark.asyncio
async def test_analyze_move_nonexistent_game(client: AsyncClient):
    """Test analyzing move for non-existent game"""
    fake_game_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format but non-existent
    
    response = await client.post("/api/v1/analyse_move", json={
        "game_id": fake_game_id,
        "move_index": 1
    })
    
    assert response.status_code == 404
    data = response.json()
    assert "Game not found" in data["detail"]

@pytest.mark.asyncio
async def test_analyze_move_invalid_move_index(client: AsyncClient):
    """Test analyzing move with invalid move index"""
    # First upload a game
    upload_response = await client.post("/api/v1/upload_pgn", json={
        "pgn": SAMPLE_PGN
    })
    
    game_id = upload_response.json()["game_id"]
    
    # Test with negative move index
    response = await client.post("/api/v1/analyse_move", json={
        "game_id": game_id,
        "move_index": -1
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid move index" in data["detail"]
    
    # Test with move index too high
    response = await client.post("/api/v1/analyse_move", json={
        "game_id": game_id,
        "move_index": 1000
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid move index" in data["detail"]

@pytest.mark.asyncio
async def test_analyze_move_caching(client: AsyncClient):
    """Test that move analysis is cached"""
    # First upload a game
    upload_response = await client.post("/api/v1/upload_pgn", json={
        "pgn": SAMPLE_PGN
    })
    
    game_id = upload_response.json()["game_id"]
    
    # Analyze the same move twice
    response1 = await client.post("/api/v1/analyse_move", json={
        "game_id": game_id,
        "move_index": 1
    })
    
    response2 = await client.post("/api/v1/analyse_move", json={
        "game_id": game_id,
        "move_index": 1
    })
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # The responses should be identical (served from cache)
    assert response1.json() == response2.json()

@pytest.mark.asyncio
async def test_analyze_move_starting_position(client: AsyncClient):
    """Test analyzing the starting position (move index 0)"""
    # First upload a game
    upload_response = await client.post("/api/v1/upload_pgn", json={
        "pgn": SAMPLE_PGN
    })
    
    game_id = upload_response.json()["game_id"]
    
    # Analyze starting position
    response = await client.post("/api/v1/analyse_move", json={
        "game_id": game_id,
        "move_index": 0
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Starting position should have evaluation close to 0
    if data["eval"] is not None:
        assert abs(data["eval"]) < 0.5  # Should be roughly equal