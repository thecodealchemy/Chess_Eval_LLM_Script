import os
from typing import Optional
from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

db = Database()

async def get_database() -> AsyncIOMotorDatabase:
    if db.database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    
    # Parse the database name from the URL
    parsed_url = urlparse(mongo_url)
    db_name = parsed_url.path.lstrip('/') if parsed_url.path else "ChessAnalyserDB"
    
    # If no database name in URL, fall back to environment variable or default
    if not db_name:
        db_name = os.getenv("DATABASE_NAME", "ChessAnalyserDB")
    
    db.client = AsyncIOMotorClient(mongo_url, server_api=ServerApi('1'))
    db.database = db.client[db_name]
    
    # Test the connection
    try:
        await db.client.admin.command('ping')
        print(f"Successfully connected to MongoDB database: {db_name}!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")