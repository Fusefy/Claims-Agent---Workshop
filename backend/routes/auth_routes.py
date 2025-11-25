"""
Authentication routes for Google OAuth and JWT token management
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel
import httpx
import jwt
from datetime import datetime, timedelta
from typing import Optional

from utils.config import (
    GOOGLE_CLIENT_ID, 
    GOOGLE_CLIENT_SECRET, 
    JWT_SECRET, 
    JWT_ALGORITHM,
    JWT_EXPIRATION_DAYS,
    ALLOWED_ORIGINS,
    FRONTEND_URL,
    BACKEND_URL
)
from database.user_repository import user_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Google OAuth redirect URI - must point to BACKEND
REDIRECT_URI = f"{BACKEND_URL}/auth/google/callback"


class TokenVerifyRequest(BaseModel):
    """Request model for token verification"""
    token: str


@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth flow.
    Returns the Google OAuth authorization URL.
    """
    try:
        scope = "openid email profile"
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        logger.info("Generated Google OAuth URL")
        return {"auth_url": auth_url}
        
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow")


@router.get("/google/callback")
async def google_callback(code: str = Query(..., description="Authorization code from Google")):
    """
    Handle Google OAuth callback.
    Exchange authorization code for tokens, verify user, and issue JWT.
    """
    try:
        # Exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=token_data)
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
            
            tokens = response.json()
        
        # Verify and decode the ID token
        try:
            idinfo = id_token.verify_oauth2_token(
                tokens['id_token'],
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )
            
            # Extract user information
            user_email = idinfo.get('email')
            user_name = idinfo.get('name', '')
            google_id = idinfo.get('sub')
            
            if not user_email:
                raise HTTPException(status_code=400, detail="Email not provided by Google")
            
            logger.info(f"User authenticated via Google: {user_email}")
            
            # Create or get user from database
            user = user_repository.get_or_create_user(
                email=user_email,
                username=user_name or user_email.split('@')[0],
                google_id=google_id
            )
            
            # Generate JWT token
            jwt_token = create_access_token({
                "sub": str(user.user_id),
                "email": user.email,
                "username": user.username,
                "role": user.role
            })
            
            # Redirect to frontend with token
            frontend_callback_url = f"{FRONTEND_URL}/auth/callback?token={jwt_token}"
            logger.info(f"Redirecting to frontend: {frontend_callback_url}")
            
            return RedirectResponse(url=frontend_callback_url)
            
        except ValueError as e:
            logger.error(f"Invalid ID token: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail="Invalid ID token from Google")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/verify")
async def verify_token(request: TokenVerifyRequest):
    """
    Verify JWT token and return user information.
    """
    try:
        payload = jwt.decode(request.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check if token is expired
        exp = payload.get('exp')
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(status_code=401, detail="Token expired")
        
        # Get user from database
        user_id = int(payload.get('sub'))
        user = user_repository.get_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token verification failed")


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client should clear token).
    """
    return {"message": "Logged out successfully"}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt
