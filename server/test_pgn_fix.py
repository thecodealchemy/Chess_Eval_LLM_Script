#!/usr/bin/env python3
"""
Test script to verify PGN parsing fix
"""

import chess.pgn
from io import StringIO

# Test the malformed PGN from the error
malformed = '[Event "Live Chess"] [Site "Chess.com"] [Date "2025.09.12"] [Round "?"] [White "00JoyBoy00"] [Black "RumoVonZamonien"] [Result "1-0"]'
print("Original malformed:", repr(malformed))

# Apply the cleaning fix
cleaned = malformed.replace('] [', ']\n[')
print("After cleaning:", repr(cleaned))

# Test with full PGN
full_pgn = cleaned + '\n\n1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Qxd4 1-0'
print("Full PGN:", repr(full_pgn))

# Test parsing
game = chess.pgn.read_game(StringIO(full_pgn))
if game:
    print("✅ Parsing successful!")
    print("Headers:", dict(game.headers))
    print("White:", game.headers.get("White"))
    print("Black:", game.headers.get("Black"))
else:
    print("❌ Parsing failed")

# Test what the analyzer would extract
from app.chess_analyzer import ChessAnalyzer
analyzer = ChessAnalyzer()
game_info = analyzer.extract_game_info(full_pgn)
print("Extracted game info:", game_info)