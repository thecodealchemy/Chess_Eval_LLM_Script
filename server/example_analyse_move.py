#!/usr/bin/env python3
"""
Example script showing how to use the /analyse_move endpoint
"""

import requests
import json
import time

# Sample PGN for testing
SAMPLE_PGN = """[Event "World Championship"]
[Site "London"]
[Date "2024.01.01"]
[Round "1"]
[White "Magnus Carlsen"]
[Black "Ding Liren"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 1-0"""

def upload_test_game():
    """Upload a test game and return the game ID"""
    url = "http://localhost:8000/api/v1/upload_pgn"
    
    payload = {
        "pgn": SAMPLE_PGN
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Game uploaded successfully!")
            print(f"Game ID: {data['game_id']}")
            print(f"Moves available: {len(data['moves'])}")
            return data['game_id']
        else:
            print(f"❌ Error uploading game: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return None

def analyze_move(game_id, move_index):
    """Analyze a specific move"""
    url = "http://localhost:8000/api/v1/analyse_move"
    
    payload = {
        "game_id": game_id,
        "move_index": move_index
    }
    
    try:
        print(f"\n🔍 Analyzing move {move_index}...")
        start_time = time.time()
        
        response = requests.post(url, json=payload, timeout=30)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis completed in {duration:.2f}s")
            print(f"📊 Evaluation: {data.get('eval', 'N/A')}")
            
            if data.get('explanation'):
                print(f"💡 Explanation: {data['explanation']}")
            
            if data.get('variations'):
                print(f"🎯 Best variations: {', '.join(data['variations'][:3])}")  # Show first 3
            
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return None

def test_caching(game_id, move_index):
    """Test caching by analyzing the same move twice"""
    print(f"\n🔄 Testing caching for move {move_index}...")
    
    # First request
    start_time = time.time()
    result1 = analyze_move(game_id, move_index)
    time1 = time.time() - start_time
    
    if not result1:
        return
    
    # Second request (should be cached)
    start_time = time.time()
    result2 = analyze_move(game_id, move_index)
    time2 = time.time() - start_time
    
    if result2:
        print(f"\n⚡ Cache performance:")
        print(f"First request: {time1:.2f}s")
        print(f"Second request: {time2:.2f}s")
        print(f"Speedup: {time1/time2:.1f}x faster")
        
        # Verify results are identical
        if result1 == result2:
            print("✅ Results identical - caching working correctly!")
        else:
            print("⚠️  Results differ - caching might have issues")

def main():
    print("🚀 Testing /analyse_move endpoint...")
    print("=" * 60)
    
    # Step 1: Upload a test game
    game_id = upload_test_game()
    if not game_id:
        print("Failed to upload game. Make sure the server is running.")
        return
    
    # Step 2: Analyze different moves
    moves_to_test = [0, 1, 2, 5, 10]  # Starting position and various moves
    
    for move_index in moves_to_test:
        result = analyze_move(game_id, move_index)
        if not result:
            break
        time.sleep(1)  # Small delay to not overwhelm APIs
    
    # Step 3: Test caching
    test_caching(game_id, 2)
    
    print("\n" + "=" * 60)
    print("🎉 Testing completed!")
    print("\nTips:")
    print("• Make sure GROQ_API_KEY is set in your .env file for AI explanations")
    print("• The first request may be slower due to API calls")
    print("• Cached requests should be much faster")
    print("• Check the MongoDB 'move_analysis_cache' collection for stored results")

if __name__ == "__main__":
    main()