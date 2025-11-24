"""FastAPI authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from src.database.db import get_session
from src.auth import oauth

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# LOGIN ENDPOINT
# ============================================================================

@router.get("/login")
def login():
    """
    Initiate Google OAuth login
    
    Returns:
        RedirectResponse: Redirects user to Google OAuth consent page
        
    Usage from Streamlit:
        # In Streamlit app
        st.markdown(f'<a href="{FASTAPI_URL}/auth/login" target="_blank">Login with Google</a>')
    """
    auth_url, state = oauth.build_google_login_url()
    
    # In a real app, you'd store state in session/cookie to validate callback
    # For this demo, we skip state validation
    
    return RedirectResponse(url=auth_url)


# ============================================================================
# CALLBACK ENDPOINT
# ============================================================================

@router.get("/callback")
def oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter"),
    db: Session = Depends(get_session)
):
    """
    Handle OAuth callback from Google
    
    Args:
        code: Authorization code from Google
        state: State parameter (not validated in this demo)
        db: Database session
        
    Returns:
        dict: User info with user_id and email
        
    This endpoint should redirect back to Streamlit with user info.
    For simplicity, we return JSON that Streamlit can parse.
    
    Usage from Streamlit:
        # After redirect, Streamlit can read query params
        query_params = st.query_params
        if 'code' in query_params:
            response = requests.get(f"{FASTAPI_URL}/auth/callback?code={query_params['code']}&state={query_params['state']}")
            user_info = response.json()
            st.session_state['user_id'] = user_info['user_id']
            st.session_state['email'] = user_info['email']
    """
    try:
        user_info = oauth.handle_oauth_callback(db, code, state)
        return {
            "success": True,
            "user_id": user_info["user_id"],
            "email": user_info["email"],
            "name": user_info.get("name")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# TOKEN ENDPOINTS
# ============================================================================

@router.get("/token/{user_id}")
def get_youtube_token(
    user_id: int,
    db: Session = Depends(get_session)
):
    """
    Get a valid YouTube access token for user (auto-refreshes if needed)
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        dict: access_token
        
    Usage from Streamlit:
        # Get token before making YouTube API calls
        response = requests.get(f"{FASTAPI_URL}/auth/token/{user_id}")
        access_token = response.json()["access_token"]
    """
    try:
        access_token = oauth.get_valid_youtube_token(db, user_id)
        return {"access_token": access_token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/{user_id}")
def force_refresh_token(
    user_id: int,
    db: Session = Depends(get_session)
):
    """
    Force refresh user's access token
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        dict: New access_token
    """
    from src.database import crud
    
    user = crud.get_user_by_id(db, user_id)
    if not user or not user.refresh_token:
        raise HTTPException(status_code=400, detail="Cannot refresh token")
    
    try:
        token_response = oauth.refresh_access_token(user.refresh_token)
        new_token = token_response["access_token"]
        
        from datetime import datetime, timedelta
        expires_in = token_response.get("expires_in", 3600)
        new_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        crud.update_user_tokens(
            db,
            user_id=user_id,
            access_token=new_token,
            token_expires_at=new_expires_at
        )
        
        return {"access_token": new_token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# USER INFO ENDPOINT
# ============================================================================

@router.get("/me/{user_id}")
def get_current_user(
    user_id: int,
    db: Session = Depends(get_session)
):
    """
    Get current user information
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        dict: User info
    """
    from src.database import crud
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "google_id": user.google_id
    }