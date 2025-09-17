#!/usr/bin/env python3
"""
Simple script to run the FastAPI server for development
"""

import uvicorn
import os
from pathlib import Path

def main():
    print("🚀 Starting Chess Analysis FastAPI Server...")
    print("=" * 50)
    print("Endpoints available:")
    print("  • POST /api/v1/upload_pgn - Upload PGN string")
    print("  • GET  /api/v1/games - List games")
    print("  • GET  /docs - API documentation")
    print("  • GET  /health - Health check")
    print("=" * 50)
    
    # Ensure we're in the server directory
    server_dir = Path(__file__).parent.absolute()
    os.chdir(server_dir)
    print(f"Working directory: {server_dir}")
    
    # Check for .env file and provide guidance
    env_file = server_dir / ".env"
    env_example = server_dir / ".env.example"
    
    if not env_file.exists():
        print(f"\n⚠️  .env file not found at {env_file}")
        if env_example.exists():
            print(f"📝 Please copy {env_example} to {env_file} and update the values")
        print("   Especially set your GROQ_API_KEY for AI explanations")
        print()
    else:
        print(f"✓ Found .env file at {env_file}")
    
    # Set default environment variables if .env doesn't exist
    if not env_file.exists():
        os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()