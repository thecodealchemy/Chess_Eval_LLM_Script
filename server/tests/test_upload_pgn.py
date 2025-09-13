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
async def test_upload_pgn_valid(client: AsyncClient):
    """Test uploading a valid PGN string"""
    response = await client.post("/api/v1/upload_pgn", json={
        "pgn": SAMPLE_PGN
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that we get a game_id
    assert "game_id" in data
    assert len(data["game_id"]) == 24  # MongoDB ObjectId length
    
    # Check metadata
    assert "metadata" in data
    metadata = data["metadata"]
    assert metadata["white_player"] == "Alice"
    assert metadata["black_player"] == "Bob"
    assert metadata["event"] == "Test Game"
    assert metadata["result"] == "1-0"
    assert metadata["date"] == "2024.01.01"
    
    # Check moves
    assert "moves" in data
    moves = data["moves"]
    assert len(moves) > 0
    
    # Check starting position
    first_move = moves[0]
    assert first_move["move_number"] == 0
    assert first_move["san"] == "Starting position"
    assert first_move["fen"] == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    # Check first move
    second_move = moves[1]
    assert second_move["move_number"] == 1
    assert second_move["san"] == "e4"
    assert "fen" in second_move

@pytest.mark.asyncio
async def test_upload_pgn_invalid(client: AsyncClient):
    """Test uploading an invalid PGN string"""
    response = await client.post("/api/v1/upload_pgn", json={
        "pgn": "This is not a valid PGN"
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Error processing PGN" in data["detail"]

@pytest.mark.asyncio
async def test_upload_pgn_empty(client: AsyncClient):
    """Test uploading an empty PGN string"""
    response = await client.post("/api/v1/upload_pgn", json={
        "pgn": ""
    })
    
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_upload_pgn_missing_field(client: AsyncClient):
    """Test uploading without required pgn field"""
    response = await client.post("/api/v1/upload_pgn", json={})
    
    assert response.status_code == 422  # Validation error