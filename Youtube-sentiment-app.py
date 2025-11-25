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
from datetime import datetime, timedelta
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

# Configuration
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# OAuth scopes
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/youtube.readonly"
]


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

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
    
    # If it's already just an ID (11 chars), return it
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


# ============================================================================
# OAUTH AUTHENTICATION
# ============================================================================

@st.cache_resource
def get_oauth_component():
    """Get OAuth component (cached)"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        st.error("⚠️ OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
        st.stop()
    
    return OAuth2Component(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        refresh_token_endpoint="https://oauth2.googleapis.com/token",
        revoke_token_endpoint="https://oauth2.googleapis.com/revoke"
    )


def get_google_user_info(access_token: str) -> Optional[dict]:
    """Get user information from Google"""
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
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
        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
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
    
    # OAuth login button
    # NEW (explicitly force scope)
    result = oauth.authorize_button(
    name="Login with Google",
    icon="https://www.google.com/favicon.ico",
    redirect_uri=os.getenv("STREAMLIT_REDIRECT_URI", "http://localhost:8501"),
    scope="openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube.force-ssl",
    key="google_oauth",
    extras_params={
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true"
    })
    
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
                    
                    expires_in = token.get("expires_in", 3600)
                    st.session_state.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    st.success(f"✅ Logged in as {user_info['email']}")
                    st.rerun()
                    return True
    
    return False


def logout():
    """Logout user and clear session"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ============================================================================
# API CALLS TO FASTAPI
# ============================================================================

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
            timeout=300  # 5 minutes for large videos
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
            timeout=10
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
        comments = get_top_negative_comments(video_id, limit=5)  # Pass ID, not URL
    
    if not comments:
        st.info("No negative comments found or analysis not complete yet.")
        return
    
    for i, comment in enumerate(comments, 1):
        with st.expander(f"#{i} - {comment['author']} (Confidence: {comment['confidence']:.1%})"):
            st.write(comment['text'])
            
            # Sentiment indicator
            confidence_pct = comment['confidence'] * 100
            if confidence_pct >= 90:
                st.caption("🔴 Very Negative (High Confidence)")
            elif confidence_pct >= 75:
                st.caption("🟠 Negative (Medium Confidence)")
            else:
                st.caption("🟡 Negative (Lower Confidence)")

def get_user_videos(limit: int = 10) -> list:
    """Get user's video history from FastAPI"""
    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/videos",
            params={"user_id": st.session_state.user_id, "limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


# ============================================================================
# UI COMPONENTS
# ============================================================================

# In Youtube-sentiment-app.py
# REPLACE the display_analysis_results function (around line 360-420) with this:

def display_analysis_results(results: dict):
    """Display analysis results with visualizations"""
    # Handle None or empty results
    if not results:
        st.warning("⚠️ No analysis results available")
        return
    
    if not results.get("success"):
        st.warning(results.get("message", "Analysis failed"))
        return
    
    st.success("✅ " + results.get("message", "Analysis complete!"))
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Total Comments",
            results["total_comments"]
        )
    
    with col2:
        st.metric(
            "😊 Positive",
            results["positive_count"],
            f"{results['positive_percentage']:.1f}%"
        )
    
    with col3:
        st.metric(
            "😐 Neutral",
            results["neutral_count"],
            f"{results['neutral_percentage']:.1f}%"
        )
    
    with col4:
        st.metric(
            "😞 Negative",
            results["negative_count"],
            f"{results['negative_percentage']:.1f}%"
        )
    
    # Bar chart
    st.markdown("---")
    st.subheader("📊 Sentiment Distribution")
    
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
        with st.expander(f"#{i} - {comment['author']} (Confidence: {comment['confidence']:.2%})"):
            st.write(comment['text'])


def display_video_history():
    """Display user's video analysis history"""
    st.subheader("📹 Your Analysis History")
    
    with st.spinner("Loading your videos..."):
        videos = get_user_videos(limit=20)
    
    if not videos:
        st.info("No videos analyzed yet. Start by analyzing your first video! 🎬")
        return
    
    st.markdown(f"*You have analyzed {len(videos)} video(s)*")
    st.markdown("---")
    
    for video in videos:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            title = video.get('title') or video['youtube_video_id']
            st.markdown(f"**📺 {title}**")
            st.caption(f"Video ID: `{video['youtube_video_id']}` • Analyzed: {video['created_at'][:10]} • Analyses: {video['analysis_count']}")
        
        with col2:
            if st.button("View", key=f"view_{video['video_id']}"):
                # Store FULL YouTube URL instead of just video ID
                full_url = f"https://www.youtube.com/watch?v={video['youtube_video_id']}"
                st.session_state.selected_video = full_url
                st.session_state.switch_to_analyze = True
                st.rerun()
        
        st.markdown("---")

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
    st.title("🎬 YouTube Sentiment Analyzer")
    st.markdown("*Analyze YouTube video comments with AI-powered sentiment analysis*")
    
    # Check authentication
    if not handle_authentication():
        st.info("👆 Click the button above to get started!")
        
        # Show features while logged out
        st.markdown("---")
        st.markdown("### ✨ Features")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("🤖 **AI-Powered**")
            st.caption("Uses BERT transformer model for accurate sentiment analysis")
        with col2:
            st.markdown("📊 **Visual Analytics**")
            st.caption("Interactive charts and sentiment breakdowns")
        with col3:
            st.markdown("💬 **Top Comments**")
            st.caption("Identifies most negative comments automatically")
        
        st.markdown("---")
        st.markdown("### 🚀 How It Works")
        st.markdown("1. Login with your Google account")
        st.markdown("2. Paste a YouTube video URL")
        st.markdown("3. Get instant sentiment analysis results")
        st.markdown("4. View detailed breakdowns and top negative comments")
        
        st.stop()
    
    # User is authenticated - show main app
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        st.markdown(f"**{st.session_state.user_info['name']}**")
        st.markdown(f"📧 {st.session_state.user_info['email']}")
        
        if st.session_state.user_info.get('picture'):
            st.image(st.session_state.user_info['picture'], width=100)
        
        st.markdown("---")
        
        # Navigation - handle switch from history page
        if st.session_state.get("switch_to_analyze"):
            default_index = 0  # Analyze Video page
            st.session_state.switch_to_analyze = False
        else:
            default_index = 0
        
        page = st.radio(
            "Navigation",
            ["🔍 Analyze Video", "📹 History"],
            index=default_index,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    # Main content area
    if page == "🔍 Analyze Video":
        st.markdown("### Analyze YouTube Video Comments")
        st.markdown("Enter a YouTube video URL to analyze the sentiment of its comments.")
        
        # Video URL input
        default_url = st.session_state.get("selected_video", "")
        
        video_url = st.text_input(
            "YouTube Video URL",
            value=default_url,
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste the full URL or just the video ID",
            label_visibility="collapsed"
        )
        
        # Clear the selected video after it's been used
        if "selected_video" in st.session_state and default_url:
            del st.session_state["selected_video"]

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
            if not video_url:
                st.error("⚠️ Please enter a YouTube URL")
            else:
                # Clear previous analyzing state
                st.session_state.analyzing = False
                
                with st.spinner("🎬 Fetching comments and analyzing sentiment... This may take 30-60 seconds."):
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