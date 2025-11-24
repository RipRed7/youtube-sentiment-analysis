"""Google OAuth module for FastAPI (Synchronous)"""
import os
import secrets
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from urllib.parse import urlencode

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.database import crud

# Environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")

if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, OAUTH_REDIRECT_URI]):
    raise ValueError("Missing OAuth environment variables: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, OAUTH_REDIRECT_URI")

# Google OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# OAuth scopes
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/youtube.readonly"
]


# ============================================================================
# OAUTH LOGIN
# ============================================================================

def build_google_login_url() -> tuple[str, str]:
    """
    Build Google OAuth login URL
    
    Returns:
        tuple: (auth_url, state) - OAuth URL and state parameter
    """
    state = secrets.token_urlsafe(32)
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "access_type": "offline",  # Get refresh token
        "prompt": "consent"  # Force consent to get refresh token
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return auth_url, state


# ============================================================================
# OAUTH CALLBACK
# ============================================================================

def exchange_code_for_tokens(code: str) -> Dict:
    """
    Exchange authorization code for access and refresh tokens
    
    Args:
        code: Authorization code from Google
        
    Returns:
        dict: Token response containing access_token, refresh_token, expires_in
        
    Raises:
        HTTPException: If token exchange fails
    """
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code for tokens: {response.text}"
        )
    
    return response.json()


def get_user_info(access_token: str) -> Dict:
    """
    Get user information from Google
    
    Args:
        access_token: OAuth access token
        
    Returns:
        dict: User info containing id, email, name, picture
        
    Raises:
        HTTPException: If request fails
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get user info: {response.text}"
        )
    
    return response.json()


def handle_oauth_callback(db: Session, code: str, state: str) -> Dict:
    """
    Handle OAuth callback - exchange code, get user info, store in DB
    
    Args:
        db: Database session
        code: Authorization code from Google
        state: State parameter (not validated in this simple version)
        
    Returns:
        dict: User info with user_id and email
        
    Raises:
        HTTPException: If any step fails
    """
    # Exchange code for tokens
    token_response = exchange_code_for_tokens(code)
    access_token = token_response["access_token"]
    refresh_token = token_response.get("refresh_token")
    expires_in = token_response.get("expires_in", 3600)
    
    # Calculate token expiration
    token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    # Get user info
    user_info = get_user_info(access_token)
    google_id = user_info["id"]
    email = user_info["email"]
    name = user_info.get("name")
    
    # Store or update user in database
    user = crud.create_or_update_user(
        db,
        google_id=google_id,
        email=email,
        name=name,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=token_expires_at
    )
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name
    }


# ============================================================================
# TOKEN REFRESH
# ============================================================================

def refresh_access_token(refresh_token: str) -> Dict:
    """
    Refresh access token using refresh token
    
    Args:
        refresh_token: OAuth refresh token
        
    Returns:
        dict: New token response with access_token and expires_in
        
    Raises:
        HTTPException: If refresh fails
    """
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to refresh token: {response.text}"
        )
    
    return response.json()


def get_valid_youtube_token(db: Session, user_id: int) -> str:
    """
    Get a valid YouTube access token for user (refresh if expired)
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        str: Valid access token
        
    Raises:
        HTTPException: If user not found or refresh fails
    """
    user = crud.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.refresh_token:
        raise HTTPException(
            status_code=400,
            detail="User has no refresh token. Please re-authenticate."
        )
    
    # Check if token is expired or about to expire (5 minute buffer)
    now = datetime.utcnow()
    expires_soon = user.token_expires_at - timedelta(minutes=5)
    
    if now >= expires_soon:
        # Token expired or expiring soon - refresh it
        token_response = refresh_access_token(user.refresh_token)
        new_access_token = token_response["access_token"]
        expires_in = token_response.get("expires_in", 3600)
        new_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Update user tokens in database
        crud.update_user_tokens(
            db,
            user_id=user_id,
            access_token=new_access_token,
            token_expires_at=new_expires_at
        )
        
        return new_access_token
    
    # Token still valid
    return user.access_token


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_youtube_token(access_token: str) -> bool:
    """
    Validate that an access token is valid for YouTube API
    
    Args:
        access_token: OAuth access token
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Try to access YouTube API
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
            headers=headers
        )
        return response.status_code == 200
    except Exception:
        return False