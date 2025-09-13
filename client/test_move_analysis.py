#!/usr/bin/env python3
"""
Test script for the React move analysis functionality
"""

import requests
import json

SAMPLE_PGN = """[Event "World Championship"]
[Site "London"]
[Date "2024.01.01"]
[Round "1"]
[White "Magnus Carlsen"]
[Black "Ding Liren"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 exd4 11. cxd4 Nbd7 12. Nc3 Bb7 13. Bg5 h6 14. Bh4 c5 1-0"""

def upload_and_test_analysis():
    """Upload a game and test the analysis endpoints"""
    
    # Step 1: Upload a PGN
    print("🚀 Uploading test game...")
    upload_response = requests.post("http://localhost:8000/api/v1/upload_pgn", json={
        "pgn": SAMPLE_PGN
    })
    
    if upload_response.status_code != 200:
        print("❌ Failed to upload game")
        return
    
    game_data = upload_response.json()
    game_id = game_data['game_id']
    print(f"✅ Game uploaded with ID: {game_id}")
    print(f"📊 Game has {len(game_data['moves'])} moves")
    
    # Step 2: Test move analysis for different positions
    test_moves = [1, 3, 5, 10]  # Test various moves
    
    for move_index in test_moves:
        print(f"\n🔍 Analyzing move {move_index}...")
        
        response = requests.post("http://localhost:8000/api/v1/analyse_move", json={
            "game_id": game_id,
            "move_index": move_index
        })
        
        if response.status_code == 200:
            analysis = response.json()
            print(f"✅ Move {move_index} analysis:")
            print(f"   📈 Evaluation: {analysis.get('eval', 'N/A')}")
            print(f"   💡 Explanation: {analysis.get('explanation', 'N/A')}")
            print(f"   🎯 Variations: {len(analysis.get('variations', []))} found")
        else:
            print(f"❌ Failed to analyze move {move_index}: {response.text}")
    
    print(f"\n🎉 Test completed! You can now:")
    print(f"   1. Open http://localhost:3000/games/{game_id}")
    print(f"   2. Click on any move in the move list")
    print(f"   3. See the AI analysis with engine evaluation and explanations")

if __name__ == "__main__":
    upload_and_test_analysis()