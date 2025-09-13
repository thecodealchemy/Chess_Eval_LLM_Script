import os
from jose import jwt
from jose.exceptions import JWTError
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests
from google.oauth2 import id_token
from .database import get_database
from .models import UserModel, UserResponse
from bson import ObjectId

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

security = HTTPBearer()

class AuthenticationError(Exception):
    pass

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise AuthenticationError("Invalid token")

async def verify_google_token(token: str) -> dict:
    """Verify Google OAuth token and return user info"""
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID)
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return {
            'google_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo['name'],
            'picture': idinfo.get('picture')
        }
    except ValueError as e:
        raise AuthenticationError(f"Invalid Google token: {str(e)}")

async def get_or_create_user(user_data: dict, db) -> UserModel:
    """Get existing user or create new one"""
    # Check if user exists
    existing_user = await db.users.find_one({"google_id": user_data["google_id"]})
    
    if existing_user:
        # Update last login
        await db.users.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return UserModel(**existing_user)
    else:
        # Create new user
        user_doc = {
            "google_id": user_data["google_id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return UserModel(**user_doc)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_database)
) -> UserModel:
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        # Get user from database
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise AuthenticationError("User not found")
        
        return UserModel(**user)
    
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db = Depends(get_database)
) -> Optional[UserModel]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None