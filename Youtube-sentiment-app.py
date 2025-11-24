"""
Complete Streamlit Integration with FastAPI Backend
"""
import streamlit as st
import requests
from urllib.parse import parse_qs, urlparse
import time

# Configuration
FASTAPI_URL = "http://localhost:8000"  


# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

def check_authentication():
    """Check if user is authenticated"""
    return "user_id" in st.session_state and "email" in st.session_state


def handle_oauth_callback():
    """Handle OAuth callback from Google"""
    query_params = st.query_params
    
    if "code" in query_params:
        code = query_params["code"]
        state = query_params.get("state", "")
        
        with st.spinner("Logging in..."):
            try:
                response = requests.get(
                    f"{FASTAPI_URL}/auth/callback",
                    params={"code": code, "state": state},
                    timeout=10
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    
                    # Store in session state
                    st.session_state["user_id"] = user_info["user_id"]
                    st.session_state["email"] = user_info["email"]
                    st.session_state["name"] = user_info.get("name", "User")
                    
                    # Clear query params
                    st.query_params.clear()
                    
                    st.success(f"✅ Logged in as {user_info['email']}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error during login: {e}")
                st.info("Make sure FastAPI server is running on http://localhost:8000")


def login_button():
    """Display login button"""
    st.markdown("""
    <style>
    .login-button {
        display: inline-block;
        padding: 12px 24px;
        background-color: #4285f4;
        color: white;
        text-decoration: none;
        border-radius: 4px;
        font-weight: 500;
        text-align: center;
        margin: 10px 0;
    }
    .login-button:hover {
        background-color: #357ae8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(
        f'<a href="{FASTAPI_URL}/auth/login" class="login-button" target="_self">🔐 Login with Google</a>',
        unsafe_allow_html=True
    )


def logout_button():
    """Display logout button"""
    if st.button("🚪 Logout"):
        for key in ["user_id", "email", "name"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# ============================================================================
# API HELPERS
# ============================================================================

def analyze_video(video_url: str) -> dict:
    """
    Call FastAPI to analyze video
    
    Args:
        video_url: YouTube video URL or ID
        
    Returns:
        Analysis results dictionary
    """
    if not check_authentication():
        raise ValueError("User not authenticated")
    
    try:
        response = requests.post(
            f"{FASTAPI_URL}/api/analyze",
            json={
                "youtube_video_id": video_url,
                "user_id": st.session_state["user_id"]
            },
            timeout=120  # 2 minutes for analysis
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
    Get top negative comments for a video
    
    Args:
        youtube_video_id: YouTube video ID
        limit: Number of comments to retrieve
        
    Returns:
        List of top negative comments
    """
    if not check_authentication():
        return []
    
    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/videos/{youtube_video_id}/comments/top-negative",
            params={
                "user_id": st.session_state["user_id"],
                "limit": limit
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.warning("Could not fetch top negative comments")
            return []
            
    except Exception as e:
        st.warning(f"Error fetching comments: {e}")
        return []


def get_user_videos() -> list:
    """
    Get list of videos analyzed by user
    
    Returns:
        List of video dictionaries
    """
    if not check_authentication():
        return []
    
    try:
        response = requests.get(
            f"{FASTAPI_URL}/api/videos",
            params={"user_id": st.session_state["user_id"]},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return []
            
    except Exception as e:
        st.warning(f"Error fetching videos: {e}")
        return []


# ============================================================================
# UI COMPONENTS
# ============================================================================

def display_analysis_results(results: dict):
    """Display analysis results with visualizations"""
    if not results.get("success"):
        st.warning(results.get("message", "Analysis failed"))
        return
    
    st.success("✅ Analysis Complete!")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "😊 Positive",
            results["positive_count"],
            f"{results['positive_percentage']:.1f}%"
        )
    
    with col2:
        st.metric(
            "😐 Neutral",
            results["neutral_count"],
            f"{results['neutral_percentage']:.1f}%"
        )
    
    with col3:
        st.metric(
            "😞 Negative",
            results["negative_count"],
            f"{results['negative_percentage']:.1f}%"
        )
    
    # Bar chart
    st.subheader("📊 Sentiment Distribution")
    st.bar_chart({
        "Positive": results["positive_count"],
        "Neutral": results["neutral_count"],
        "Negative": results["negative_count"]
    })
    
    st.info(f"Total comments analyzed: {results['total_comments']}")


def display_top_negative_comments(youtube_video_id: str):
    """Display top negative comments"""
    st.subheader("💬 Top Negative Comments")
    
    comments = get_top_negative_comments(youtube_video_id, limit=5)
    
    if not comments:
        st.info("No negative comments found or analysis not complete yet.")
        return
    
    for i, comment in enumerate(comments, 1):
        with st.expander(f"#{i} - {comment['author']} (Confidence: {comment['confidence']:.2%})"):
            st.write(comment['text'])


def display_video_history():
    """Display user's video analysis history"""
    st.subheader("📹 Your Analysis History")
    
    videos = get_user_videos()
    
    if not videos:
        st.info("No videos analyzed yet. Start by analyzing your first video!")
        return
    
    for video in videos:
        with st.expander(f"📺 {video['title'] or video['youtube_video_id']}"):
            st.write(f"**Video ID:** {video['youtube_video_id']}")
            st.write(f"**Analyzed:** {video['created_at'][:10]}")
            st.write(f"**Total Analyses:** {video['analysis_count']}")
            
            if st.button(f"View Analysis", key=f"view_{video['video_id']}"):
                st.session_state["selected_video"] = video['youtube_video_id']


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="YouTube Sentiment Analyzer",
        page_icon="🎬",
        layout="wide"
    )
    
    # Handle OAuth callback
    handle_oauth_callback()
    
    # Check authentication
    if not check_authentication():
        # Show login page
        st.title("🎬 YouTube Sentiment Analyzer")
        st.markdown("### Welcome! Please login to continue")
        st.markdown("""
        This application analyzes sentiment of YouTube video comments using AI.
        
        **Features:**
        - 🤖 AI-powered sentiment analysis using BERT
        - 📊 Visual sentiment distribution
        - 💬 Top negative comment detection
        - 📹 Analysis history tracking
        """)
        st.markdown("---")
        login_button()
        
        st.markdown("""
        **Note:** Make sure FastAPI server is running:
        ```bash
        python main.py
        ```
        """)
        st.stop()
    
    # User is authenticated - show main app
    st.title("🎬 YouTube Sentiment Analyzer")
    
    # Sidebar with user info
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state['name']}")
        st.markdown(f"📧 {st.session_state['email']}")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["🔍 Analyze Video", "📹 History"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        logout_button()
        
        # API Status
        st.markdown("---")
        st.markdown("**API Status**")
        try:
            response = requests.get(f"{FASTAPI_URL}/health", timeout=2)
            if response.status_code == 200:
                st.success("✅ Connected")
            else:
                st.error("❌ API Error")
        except:
            st.error("❌ Disconnected")
    
    # Main content
    if page == "🔍 Analyze Video":
        st.markdown("### Analyze YouTube Video Comments")
        
        # Video URL input
        video_url = st.text_input(
            "Enter YouTube Video URL:",
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste a YouTube video URL or video ID"
        )
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            analyze_button = st.button("🔍 Analyze Comments", type="primary")
        
        with col2:
            if st.session_state.get("analyzing"):
                st.info("⏳ Analysis in progress...")
        
        # Analyze video
        if analyze_button:
            if not video_url:
                st.error("Please enter a YouTube URL")
            else:
                st.session_state["analyzing"] = True
                
                with st.spinner("🎬 Fetching comments and analyzing sentiment..."):
                    try:
                        results = analyze_video(video_url)
                        st.session_state["last_results"] = results
                        st.session_state["last_video_id"] = video_url
                        st.session_state["analyzing"] = False
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {e}")
                        st.session_state["analyzing"] = False
        
        # Display results
        if "last_results" in st.session_state:
            st.markdown("---")
            display_analysis_results(st.session_state["last_results"])
            
            if "last_video_id" in st.session_state:
                st.markdown("---")
                display_top_negative_comments(st.session_state["last_video_id"])
    
    else:  # History page
        display_video_history()


if __name__ == "__main__":
    main()