from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST, before any local imports
env_file = Path(__file__).parent.parent / ".env"
env_production_file = Path(__file__).parent.parent / ".env.production"

# Load appropriate environment file based on NODE_ENV
node_env = os.getenv("NODE_ENV", "development")
if node_env == "production" and env_production_file.exists():
    load_dotenv(env_production_file)
    print(f"✓ Loaded production environment from {env_production_file}")
elif env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded environment from {env_file}")
else:
    print(f"⚠️  No .env file found at {env_file}")
    print("   Please create a .env file based on .env.example")

# Validate critical environment variables
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key or groq_key == "your_groq_api_key_here":
    print("⚠️  Warning: GROQ_API_KEY not set or using placeholder value. AI explanations will use fallback mode.")
else:
    print("✓ GROQ_API_KEY loaded successfully")

# Now import local modules that depend on environment variables
from .database import connect_to_mongo, close_mongo_connection
from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="Chess Analysis API",
    description="A FastAPI backend for chess game analysis with PGN upload and move analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Chess Analysis API", 
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}