"""
YouTube Sentiment Analyzer - Streamlit UI
Hybrid Architecture: Streamlit handles OAuth, FastAPI handles analysis
"""
import streamlit as st
from streamlit_oauth import OAuth2Component
import os
import sys
from pathlib import Path
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database modules for direct user storage
from src.database.db import get_db_session
from src.database import crud
from src.config.constants import (
    DEFAULT_TOP_NEGATIVE_LIMIT,
    DEFAULT_USER_VIDEOS_LIMIT,
    DEFAULT_TOKEN_EXPIRY_SECONDS,
    API_TIMEOUT_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    GOOGLE_OAUTH_SCOPES,
    GOOGLE_OAUTH_AUTHORIZE_URL,
    GOOGLE_OAUTH_TOKEN_URL,
    GOOGLE_OAUTH_USERINFO_URL,
    GOOGLE_OAUTH_TOKENINFO_URL
)

# Configuration
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# OAuth scopes
SCOPES = ["openid"] + GOOGLE_OAUTH_SCOPES



# SESSION STATE INITIALIZATION

def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "token_expires_at" not in st.session_state:
        st.session_state.token_expires_at = None
    if "last_results" not in st.session_state:
        st.session_state.last_results = None
    if "analyzing" not in st.session_state:
        st.session_state.analyzing = False
        
        
def extract_video_id(url_or_id: str) -> str:
    """
    Extract YouTube video ID from URL or return as-is if already an ID
    
    Args:
        url_or_id: YouTube URL or video ID
        
    Returns:
        str: YouTube video ID
    """
    from urllib.parse import urlparse, parse_qs
    
    # If it's already an ID (11 chars), return it
    if len(url_or_id) == 11 and url_or_id.replace('-', '').replace('_', '').isalnum():
        return url_or_id
    
    # Handle youtu.be URLs
    if 'youtu.be' in url_or_id:
        parsed = urlparse(url_or_id)
        return parsed.path.strip('/')
    
    # Handle youtube.com URLs
    if 'youtube.com' in url_or_id:
        parsed = urlparse(url_or_id)
        query = parse_qs(parsed.query)
        return query.get('v', [''])[0]
    
    # Return as-is if can't parse
    return url_or_id

def get_video_title(video_id: str, access_token: str) -> str:
    """
    Fetch video title from YouTube API
    
    Args:
        video_id: YouTube video ID
        access_token: User's access token
        
    Returns:
        Video title or video ID if fetch fails
    """
    try:
        response = requests.get(
            f"https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet",
                "id": video_id,
                "fields": "items(snippet(title))"
            },
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                return data["items"][0]["snippet"]["title"]
    except Exception as e:
        st.warning(f"Could not fetch video title: {e}")
    
    return video_id  # Fallback to ID if fetch fails


# OAUTH AUTHENTICATION

@st.cache_resource
def get_oauth_component():
    """Get OAuth component (cached)"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        st.error("⚠️ OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
        st.stop()
    
    return OAuth2Component(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorize_endpoint=GOOGLE_OAUTH_AUTHORIZE_URL,
        token_endpoint=GOOGLE_OAUTH_TOKEN_URL,
        refresh_token_endpoint=GOOGLE_OAUTH_TOKEN_URL
    )


def get_google_user_info(access_token: str) -> Optional[dict]:
    """Get user information from Google"""
    try:
        response = requests.get(
            GOOGLE_OAUTH_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Failed to get user info: {e}")
    return None


def save_user_to_database(user_info: dict, token: dict) -> Optional[int]:
    """
    Save user and token to database
    Returns user_id if successful
    """
    db = get_db_session()
    try:
        # Calculate token expiry
        expires_in = token.get("expires_in", 3600)
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        # Create or update user
        user = crud.create_or_update_user(
            db,
            google_id=user_info["id"],
            email=user_info["email"],
            name=user_info.get("name"),
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            token_expires_at=token_expires_at
        )
        
        db.commit()
        return user.user_id
        
    except Exception as e:
        db.rollback()
        st.error(f"Failed to save user to database: {e}")
        return None
    finally:
        db.close()


def handle_authentication():
    """
    Handle OAuth authentication flow
    Returns True if authenticated, False otherwise
    """
    # Check if already authenticated
    if st.session_state.authenticated and st.session_state.user_id:
        return True
    
    oauth = get_oauth_component()
    
    # Show login section
    st.markdown("### 🔐 Login Required")
    st.markdown("Please login with your Google account to analyze YouTube videos.")
    st.markdown("---")
    
    # Get redirect URI from environment 
    redirect_uri = os.getenv(
        "STREAMLIT_REDIRECT_URI", 
        "http://localhost:8501"  
    )
    
    # OAuth login button
    result = oauth.authorize_button(
        name="Login with Google",
        icon="https://www.google.com/favicon.ico",
        redirect_uri=redirect_uri,  # Use dynamic redirect URI
        scope=" ".join(SCOPES),  # Convert list to space-separated string
        key="google_oauth",
        extras_params={
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true"
        }
    )
    
    if result and "token" in result:
        # Successfully authenticated
        token = result["token"]
        
        with st.spinner("Logging in..."):
            # Get user info from Google
            user_info = get_google_user_info(token["access_token"])
            
            if user_info:
                # Save to database
                user_id = save_user_to_database(user_info, token)
                
                if user_id:
                    # Store in session state
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.session_state.user_id = user_id
                    st.session_state.access_token = token["access_token"]
                    st.session_state.refresh_token = token.get("refresh_token")
                    
                    expires_in = token.get("expires_in", DEFAULT_TOKEN_EXPIRY_SECONDS)
                    st.session_state.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    
                    st.success(f"✅ Logged in as {user_info['email']}")
                    st.rerun()
                    return True
    
    return False


def logout():
    """Logout user and clear session"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# API CALLS TO FASTAPI

def check_api_health() -> bool:
    """Check if FastAPI backend is running"""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def analyze_video(video_url: str) -> dict:
    """
    Call FastAPI to analyze video
    
    Args:
        video_url: YouTube video URL or ID
        
    Returns:
        Analysis results dictionary
    """
    
    # Extract video ID from URL
    video_id = extract_video_id(video_url)
    
    try:
        response = requests.post(
            f"{FASTAPI_URL}/api/analyze",
            json={
                "youtube_video_id": video_id,  # Use extracted ID
                "user_id": st.session_state["user_id"]
            },
            timeout=API_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", response.text)
            raise Exception(f"Analysis failed: {error_detail}")
            
    except requests.exceptions.Timeout:
        raise Exception("Analysis timed out. The video may have too many comments.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to API: {e}")
    
def get_top_negative_comments(youtube_video_id: str, limit: int = 5) -> list:
    """
    Get top negative comments from FastAPI
    
    Args:
        youtube_video_id: YouTube video ID (just the ID, not full URL)
        limit: Number of comments to retrieve
        
    Returns:
        List of comment dictionaries with author, text, confidence
    """
    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/videos/{youtube_video_id}/comments/top-negative",
            params={
                "user_id": st.session_state.user_id,
                "limit": limit
            },
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Could not fetch top negative comments: {response.status_code}")
            return []
            
    except requests.exceptions.Timeout:
        st.warning("⏰ Request timed out while fetching comments")
        return []
    except requests.exceptions.ConnectionError:
        st.warning("🔌 Cannot connect to FastAPI backend")
        return []
    except Exception as e:
        st.warning(f"Error fetching comments: {e}")
        return []

def display_top_negative_comments(youtube_video_url: str):
    """Display top negative comments"""
    st.markdown("---")
    st.subheader("💬 Top Negative Comments")
    
    # Extract video ID from URL
    video_id = extract_video_id(youtube_video_url)
    
    with st.spinner("Loading top negative comments..."):
        comments = get_top_negative_comments(video_id, limit=DEFAULT_TOP_NEGATIVE_LIMIT)
    
    if not comments:
        st.info("No negative comments found or analysis not complete yet.")
        return
    
    for i, comment in enumerate(comments, 1):
        with st.expander(f" (Confidence: {comment['confidence']:.1%})"):
            st.write(comment['text'])


def get_user_videos(limit: int = DEFAULT_USER_VIDEOS_LIMIT) -> list:
    """Get user's video history from FastAPI"""
    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/videos",
            params={"user_id": st.session_state.user_id, "limit": limit},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


# UI COMPONENTS

def display_analysis_results(results: dict):
    """Display analysis results with visualizations"""
    # Handle None or empty results
    if not results:
        st.warning("⚠️ No analysis results available")
        return
    
    if not results.get("success"):
        st.warning(results.get("message", "Analysis failed"))
        return
    
    message = results.get("message", "Analysis complete!")
    
    st.success( results.get("message", "Analysis complete!"))
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Comments",
            results["total_comments"]
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="font-size: 14px; font-weight: 600; ">
                Positive
            </div>
            <div style="font-size: 35px; font-weight: 700; color:#28a745;">
                {results["positive_count"]}
            </div>
            <div style="font-size: 18px;">
                {results['positive_percentage']:.1f}%
            </div>
            """,
            unsafe_allow_html=True
        )

    
    with col3:
        st.markdown(
            f"""
            <div style="font-size: 14px; font-weight: 600; ">
                Neutral
            </div>
            <div style="font-size: 35px; font-weight: 700; color:#999999;">
                {results["neutral_count"]}
            </div>
            <div style="font-size: 18px;">
                {results['neutral_percentage']:.1f}%
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            f"""
            <div style="font-size: 14px; font-weight: 600; ">
                Negative
            </div>
            <div style="font-size: 35px; font-weight: 700; color:#DC143C;">
                {results["negative_count"]}
            </div>
            <div style="font-size: 18px;">
                {results['negative_percentage']:.1f}%
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Bar chart
    st.markdown("---")
    st.subheader("Sentiment Distribution")
    
    import plotly.graph_objects as go
    
    fig = go.Figure(data=[
        go.Bar(
            x=["Positive", "Neutral", "Negative"],
            y=[results["positive_count"], results["neutral_count"], results["negative_count"]],
            marker_color=["#28a745", "#6c757d", "#dc3545"],
            text=[
                f"{results['positive_percentage']:.1f}%",
                f"{results['neutral_percentage']:.1f}%",
                f"{results['negative_percentage']:.1f}%"
            ],
            textposition="auto"
        )
    ])
    
    fig.update_layout(
        title="Comment Sentiment Breakdown",
        xaxis_title="Sentiment",
        yaxis_title="Number of Comments",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_top_negative_comments(youtube_video_url: str):
    """Display top negative comments"""
    st.subheader("💬 Top Negative Comments")
    
    # Extract just the video ID from the URL
    video_id = extract_video_id(youtube_video_url)
    
    comments = get_top_negative_comments(video_id, limit=5)
    
    if not comments:
        st.info("No negative comments found or analysis not complete yet.")
        return
    
    for i, comment in enumerate(comments, 1):
        with st.expander(f"(Confidence: {comment['confidence']:.2%})"):
            st.write(comment['text'])


def display_video_history():
    """Display user's video analysis history"""
    st.subheader("Analysis History")
    
    with st.spinner("Loading your videos..."):
        videos = get_user_videos(limit=DEFAULT_USER_VIDEOS_LIMIT)
    
    if not videos:
        st.info("No videos analyzed yet. Start by analyzing your first video!")
        return
    
    st.markdown(f"**{len(videos)} video(s) analyzed**")
    st.markdown("---")
    
    for video in videos:
        # Use title if available, fallback to ID
        display_title = video.get('title') or f"Video {video['youtube_video_id']}"
        
        # Create card layout
        st.markdown(f"""
        <div class="video-card">
            <div class="video-title">{display_title}</div>
            <div class="video-meta">
                Analyzed: {video['created_at'][:10]} | 
                Analyses: {video['analysis_count']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([5, 1])
        
        with col2:
            if st.button("View Analysis", key=f"view_{video['video_id']}", use_container_width=True):
                full_url = f"https://www.youtube.com/watch?v={video['youtube_video_id']}"
                st.session_state.selected_video = full_url
                st.session_state.switch_to_analyze = True
                st.session_state.video_url_input = full_url
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="YouTube Sentiment Analyzer",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Custom CSS
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("YouTube Sentiment Analyzer")
    st.markdown("#### Analyze YouTube video comments with AI-powered sentiment analysis")
    st.markdown("---")
    
    # Check authentication
    if not handle_authentication():
        st.info("👆 Click the button above to get started!")
        
        # Show features while logged out
        st.markdown("---")
        st.markdown("###  Features")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(" **AI-Powered**")
            st.caption("Uses BERT transformer model for sentiment analysis")
        with col2:
            st.markdown(" **Visual Analytics**")
            st.caption("Interactive charts and sentiment breakdowns")
        with col3:
            st.markdown(" **Top Comments**")
            st.caption("Identifies top comments automatically")
        
        st.markdown("---")
        st.markdown("### How It Works")
        st.markdown("1. Login with your Google account")
        st.markdown("2. Paste a YouTube video URL")
        st.markdown("3. Get sentiment analysis results")
        st.markdown("4. View detailed charts and top comments")
        
        st.stop()
    
    # User is authenticated - show main app
    
    # Sidebar
    with st.sidebar:
        # User profile section 
        st.markdown(f"""
        <div class="profile-section">
            <h3>{st.session_state.user_info['name']}</h3>
            <p>{st.session_state.user_info['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.user_info.get('picture'):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(st.session_state.user_info['picture'], width=80)
        
        # Navigation - handle switch from history page
        if st.session_state.get("switch_to_analyze"):
            default_index = 0  # Analyze Video page
        else:
            default_index = 0
        
        page = st.radio(
            "Navigation",
            ["🔍 Analyze Video", "📹 History"],
            index=default_index,
            label_visibility="collapsed",
            key="page_navigation"
        )
        
        # Clear the switch flag after page is set
        if st.session_state.get("switch_to_analyze"):
            st.session_state.switch_to_analyze = False
        
        st.markdown("---")
        
        # Logout button
        if st.button(" Logout", use_container_width=True):
            logout()

    # Main content 
    if page == "🔍 Analyze Video":
        st.markdown("### Analyze YouTube Video Comments")
        st.markdown("Enter a YouTube video URL to analyze the sentiment of its comments.")
        
        # Initialize or update video URL from history page
        if "video_url_input" not in st.session_state:
            st.session_state.video_url_input = ""
        
        if st.session_state.get("selected_video"):
            st.session_state.video_url_input = st.session_state.selected_video
            del st.session_state.selected_video
        
        # Video URL input
        video_url = st.text_input(
            "YouTube Video URL",
            value=st.session_state.video_url_input,
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste the full URL or just the video ID",
            label_visibility="collapsed"
        )
        
        # Always update session state
        if video_url != st.session_state.video_url_input:
            st.session_state.video_url_input = video_url

        # Analyze button
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            analyze_button = st.button(
                "🔍 Analyze Comments",
                type="primary",
                disabled=st.session_state.analyzing,
                use_container_width=True
            )
        
        with col2:
            if st.session_state.last_results:
                if st.button("🔄 Clear Results", use_container_width=True):
                    st.session_state.last_results = None
                    st.rerun()
        
        # Handle analysis
        if analyze_button:
            if not video_url or not video_url.strip():
                st.error("⚠️ Please enter a YouTube URL")
            else:
                # Debug: show what URL is being analyzed
                st.info(f"Analyzing: {video_url}")
                
                with st.spinner("🎬 Fetching comments and analyzing sentiment... "):
                    results = analyze_video(video_url)
                    
                    # Only store results if they exist and are successful
                    if results and results.get("success"):
                        st.session_state.last_results = results
                        st.session_state.last_video_id = video_url
                        st.rerun()
                    elif results:
                        # Show error message but don't store None
                        st.error(results.get("message", "Analysis failed"))
                    else:
                        # analyze_video already showed error message
                        pass
        
        # Display results
        if st.session_state.get("last_results"):
            st.markdown("---")
            display_analysis_results(st.session_state["last_results"])
            
            if st.session_state.get("last_video_id"):
                display_top_negative_comments(st.session_state["last_video_id"])
    
    else:  # History page
        display_video_history()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #777; font-size: 0.8rem;'>"
        "YouTube Sentiment Analyzer | Powered by BERT & FastAPI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()