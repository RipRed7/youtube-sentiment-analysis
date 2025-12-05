"""
Application constants and configuration values.

This module centralizes all magic numbers, URLs, and configuration defaults
to eliminate hardcoded values across the codebase.
"""

# ============================================================================
# DATA LAYER DEFAULTS
# ============================================================================

# Cache analysis within this many hours to avoid re-analyzing recent videos
DEFAULT_CACHE_HOURS = 24

# Number of top negative comments to return
DEFAULT_TOP_NEGATIVE_LIMIT = 5

# Default limit for retrieving videos by user
DEFAULT_VIDEO_LIMIT = 10

# Default limit for user's video history
DEFAULT_USER_VIDEOS_LIMIT = 20

# ============================================================================
# API CONFIGURATION
# ============================================================================

# Total timeout for analysis requests (large videos can take time)
API_TIMEOUT_SECONDS = 300  # 5 minutes

# Timeout for general HTTP requests
REQUEST_TIMEOUT_SECONDS = 10

# YouTube API maximum results per request
YOUTUBE_API_MAX_RESULTS = 100

# ============================================================================
# OAUTH & AUTHENTICATION
# ============================================================================

# Default token expiry in seconds (1 hour)
DEFAULT_TOKEN_EXPIRY_SECONDS = 3600

# Google OAuth scopes required for the application
GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/youtube.readonly"
]

# ============================================================================
# GOOGLE API ENDPOINTS
# ============================================================================

# Base URL for Google APIs
GOOGLE_API_BASE_URL = "https://www.googleapis.com"

# YouTube API video details endpoint
YOUTUBE_API_VIDEO_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"

# Google OAuth endpoints
GOOGLE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_OAUTH_TOKENINFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"

# ============================================================================
# FRONTEND CONFIGURATION
# ============================================================================

# Default frontend origins for CORS (can be overridden with FRONTEND_ORIGINS env var)
DEFAULT_FRONTEND_ORIGINS = "http://localhost:8501,https://*.streamlit.app"
