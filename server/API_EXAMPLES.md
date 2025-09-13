# Chess Analysis API - cURL Examples

## Upload PGN String

Upload a PGN string and get parsed game data with metadata and moves:

```bash
curl -X POST "http://localhost:8000/api/v1/upload_pgn" \
  -H "Content-Type: application/json" \
  -d '{
    "pgn": "[Event \"Test Game\"]\n[Site \"Test Site\"]\n[Date \"2024.01.01\"]\n[Round \"1\"]\n[White \"Alice\"]\n[Black \"Bob\"]\n[Result \"1-0\"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 1-0"
  }'
```

## Other API Endpoints

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

### API Documentation

```bash
# Open in browser
http://localhost:8000/docs
```

### List Games

```bash
curl -X GET "http://localhost:8000/api/v1/games"
```

### Get Specific Game

```bash
curl -X GET "http://localhost:8000/api/v1/games/{game_id}"
```

### Analyze Specific Move

```bash
curl -X POST "http://localhost:8000/api/v1/analyse_move" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "{game_id}",
    "move_index": 1
  }'
```

### Analyze Game

```bash
curl -X POST "http://localhost:8000/api/v1/games/{game_id}/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "{game_id}",
    "use_llm": false
  }'
```

### Get Game Analysis

```bash
curl -X GET "http://localhost:8000/api/v1/games/{game_id}/analysis"
```

### Delete Game

```bash
curl -X DELETE "http://localhost:8000/api/v1/games/{game_id}"
```

## Response Examples

### Upload PGN Response

```json
{
  "game_id": "507f1f77bcf86cd799439011",
  "metadata": {
    "white_player": "Alice",
    "black_player": "Bob",
    "event": "Test Game",
    "result": "1-0",
    "date": "2024.01.01",
    "site": "Test Site",
    "round": "1",
    "eco": null
  },
  "moves": [
    {
      "move_number": 0,
      "san": "Starting position",
      "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    },
    {
      "move_number": 1,
      "san": "e4",
      "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    },
    {
      "move_number": 2,
      "san": "e5",
      "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
    }
  ]
}
```

### Error Response

```json
{
  "detail": "Error processing PGN: Invalid PGN format"
}
```

### Move Analysis Response

```json
{
  "eval": 0.25,
  "explanation": "White is slightly better. The e4 move controls the center and opens lines for piece development.",
  "variations": ["e4 e5 Nf3 Nc6 Bb5"]
}
```
