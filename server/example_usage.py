#!/usr/bin/env python3
"""
Example script showing how to use the /upload_pgn endpoint
"""

import requests
import json

# Sample PGN for testing
SAMPLE_PGN = """[Event "Test Game"]
[Site "Test Site"]
[Date "2024.01.01"]
[Round "1"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 1-0"""

def test_upload_pgn_endpoint():
    """Test the /upload_pgn endpoint"""
    url = "http://localhost:8000/api/v1/upload_pgn"
    
    payload = {
        "pgn": SAMPLE_PGN
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PGN Upload Successful!")
            print(f"Game ID: {data['game_id']}")
            print("\n📋 Metadata:")
            metadata = data['metadata']
            for key, value in metadata.items():
                if value:
                    print(f"  {key}: {value}")
            
            print(f"\n🎯 Moves ({len(data['moves'])} total):")
            for i, move in enumerate(data['moves'][:5]):  # Show first 5 moves
                print(f"  {move['move_number']}: {move['san']}")
            
            if len(data['moves']) > 5:
                print(f"  ... and {len(data['moves']) - 5} more moves")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("Make sure the FastAPI server is running on localhost:8000")

if __name__ == "__main__":
    print("Testing /upload_pgn endpoint...")
    print("=" * 50)
    test_upload_pgn_endpoint()