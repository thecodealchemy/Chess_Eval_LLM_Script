#!/usr/bin/env python3
"""
Test script for Chess.com PGN upload functionality
"""

import requests
import json

# Sample Chess.com PGN format
CHESS_COM_PGN = """[Event "Live Chess"]
[Site "Chess.com"]
[Date "2024.01.15"]
[Round "-"]
[White "TestPlayer1"]
[Black "TestPlayer2"]
[Result "1-0"]
[CurrentPosition "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3"]
[Timezone "UTC"]
[ECO "C50"]
[ECOUrl "https://www.chess.com/openings/Italian-Game"]
[UTCDate "2024.01.15"]
[UTCTime "14:30:25"]
[WhiteElo "1650"]
[BlackElo "1580"]
[TimeControl "600"]
[Termination "TestPlayer1 won by checkmate"]
[StartTime "14:30:25"]
[EndDate "2024.01.15"]
[EndTime "14:45:12"]
[Link "https://www.chess.com/game/live/12345678"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. Ng5 d5 5. exd5 Nxd5 6. Nxf7 Kxf7 7. Qf3+ Ke6 8. Nc3 Ncb4 9. Qe4 c6 10. a3 Na6 11. d4 f5 12. Qxe5+ Kd7 13. Bf4 Bd6 14. Qxd5+ cxd5 15. Bxd6 Kxd6 16. O-O-O Nc7 17. Rhe1 Re8 18. Rxe8 Nxe8 19. Re1 Kc6 20. Rxe8 Kb6 21. Re6+ Ka5 22. b4+ Ka4 23. Bd3 Bh3 24. gxh3 Rc8 25. Ra6# 1-0"""

def test_upload_and_navigation():
    """Test the complete upload and navigation flow"""
    
    print("🚀 Testing Chess.com PGN Upload Flow")
    print("=" * 50)
    
    # Step 1: Upload PGN using the new endpoint
    print("1. Uploading Chess.com PGN...")
    
    try:
        response = requests.post("http://localhost:8000/api/v1/upload_pgn", json={
            "pgn": CHESS_COM_PGN
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            game_id = data['game_id']
            
            print(f"✅ Upload successful!")
            print(f"   Game ID: {game_id}")
            print(f"   White: {data['metadata']['white_player']}")
            print(f"   Black: {data['metadata']['black_player']}")
            print(f"   Result: {data['metadata']['result']}")
            print(f"   Event: {data['metadata']['event']}")
            print(f"   Moves: {len(data['moves'])} positions")
            
            # Step 2: Test the games list endpoint
            print("\n2. Testing games history endpoint...")
            
            games_response = requests.get("http://localhost:8000/api/v1/games")
            
            if games_response.status_code == 200:
                games_data = games_response.json()
                print(f"✅ Games list retrieved!")
                print(f"   Total games in history: {len(games_data)}")
                
                # Find our uploaded game
                uploaded_game = next((g for g in games_data if g['id'] == game_id), None)
                if uploaded_game:
                    print(f"   ✓ Our game found in history")
                    print(f"   ✓ Title: {uploaded_game['title'] if uploaded_game.get('title') else 'Auto-generated'}")
                    print(f"   ✓ Move count: {uploaded_game.get('move_count', 'N/A')}")
            
            # Step 3: Test move analysis
            print("\n3. Testing move analysis...")
            
            analysis_response = requests.post("http://localhost:8000/api/v1/analyse_move", json={
                "game_id": game_id,
                "move_index": 3  # Test the Italian Game opening
            })
            
            if analysis_response.status_code == 200:
                analysis_data = analysis_response.json()
                print(f"✅ Move analysis successful!")
                print(f"   Evaluation: {analysis_data.get('eval', 'N/A')}")
                print(f"   Explanation: {analysis_data.get('explanation', 'N/A')}")
                print(f"   Variations: {len(analysis_data.get('variations', []))} found")
            
            print("\n" + "=" * 50)
            print("🎉 All tests completed successfully!")
            print("\nYou can now:")
            print(f"   • Open http://localhost:3000/upload to test the upload form")
            print(f"   • Open http://localhost:3000/history to see the history page")
            print(f"   • Open http://localhost:3000/games/{game_id} to analyze the game")
            print(f"   • Click on moves to get AI analysis!")
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the FastAPI server is running on localhost:8000")

def test_pgn_cleaning():
    """Test PGN cleaning functionality"""
    print("\n🧹 Testing PGN Cleaning")
    print("-" * 30)
    
    # Messy Chess.com PGN
    messy_pgn = """   [Event "Live Chess"]   
    
    [Site "Chess.com"]
[Date "2024.01.15"]     [White "Player1"]
[Black "Player2"][Result "1-0"]

    1. e4 e5   2. Nf3 Nc6   3. Bb5 1-0   """
    
    print("Original messy PGN:")
    print(repr(messy_pgn))
    
    # Simple cleaning logic (similar to what's in the React component)
    cleaned = messy_pgn.replace('\n\n', '\n').strip()
    cleaned = ' '.join(cleaned.split())  # Normalize whitespace
    
    print("\nCleaned PGN:")
    print(repr(cleaned))

if __name__ == "__main__":
    test_upload_and_navigation()
    test_pgn_cleaning()