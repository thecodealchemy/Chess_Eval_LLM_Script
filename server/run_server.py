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
    
    # Set environment variables if .env doesn't exist
    if not Path(".env").exists():
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