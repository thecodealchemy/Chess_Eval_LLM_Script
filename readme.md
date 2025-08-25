# CloudReviews

Terminal tool to review a PGN chess game using Lichess Cloud Eval for variations and (optionally) a Groq/OpenAI-compatible LLM for short move explanations.

Features

- Query Lichess cloud-eval for position evaluations and top variations.
- Convert engine PVs to SAN and display compact sequence previews.
- Optional short explanation per move via Groq (OpenAI-compatible) chat completions.
- Simple in-memory cache to reduce repeated API calls while the script runs.
- Interactive stepping through moves and variation inspection.

Requirements

- Python 3.9+
- pip packages: python-chess, requests, python-dotenv
  - Install: pip install python-chess requests python-dotenv

Files

- CloudReviews.py — main script (interactive).
- myGame.pgn — sample PGN filename referenced by default (place your PGN or change PGN_FILE).

Configuration

- Edit constants at top of CloudReviews.py or via environment:
  - PGN_FILE — path to PGN file (default: myGame.pgn)
  - SKIP_BOOK_MOVES — number of opening plies to skip evaluations for
  - SEARCH_DEPTH — desired Lichess search depth (best-effort)
  - WAIT_FOR_ENTER — interactive pause behaviour
  - SHOW_ASCII_BOARD — print ASCII board vs FEN
- LLM integration (optional):
  - Set GROQ_API_KEY in your environment or a .env file to enable LLM explanations.
  - The script uses Groq's OpenAI-compatible endpoint and model configured in the script.

Example .env

```text
# Do NOT commit this file to git
GROQ_API_KEY=sk-your-secret-key
```
