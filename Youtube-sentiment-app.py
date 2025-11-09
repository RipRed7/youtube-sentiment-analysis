import streamlit as st
import os
from urllib.parse import urlparse, parse_qs
# Suppress tensorflow warnings (same as main.py)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from src.repositories import InMemoryCommentRepo
from src.backend.analyzers import BertSentimentAnalyzer
from src.backend.api import YoutubeCommentFetcher
from src.services import CommentService
from src.domain.models import SentimentLabel
from src.utils.exceptions import (
    APIQuotaExceededError,
    VideoNotFoundError,
    CommentsDisabledError,
    APIConnectionError,
    InvalidURLError
)


# Configure the Streamlit page
st.set_page_config(
    page_title="YouTube Sentiment Analyzer",
    page_icon="🎬",
    layout="wide"
)

@st.cache_resource

def load_analyzer():
    #load analyzer for caching
    return BertSentimentAnalyzer()

def extract_video_id(url: str) -> str:
    # Handle different YouTube URL formats
    if "youtube.com/watch?v=" in url:
        parsed = urlparse(url)
        return parse_qs(parsed.query)['v'][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise InvalidURLError(url)
    
def display_results(service: CommentService):
    # Get distribution
    distribution = service.get_sentiment_distrib()
    total = sum(distribution.values())

    # Display sentiment bar chart
    st.subheader("📊 Sentiment Distribution")
    col1, col2, col3 = st.columns(3)
    with col1:
        positive_count = distribution[SentimentLabel.POSTIVE]
        positive_pct = (positive_count / total * 100) if total > 0 else 0
        st.metric("😊 Positive", f"{positive_count}", f"{positive_pct:.1f}%")
    with col2:
        neutral_count = distribution[SentimentLabel.NEUTRAL]
        neutral_pct = (neutral_count / total * 100) if total > 0 else 0
        st.metric("😐 Neutral", f"{neutral_count}", f"{neutral_pct:.1f}%")
    with col3:
        negative_count = distribution[SentimentLabel.NEGATIVE]
        negative_pct = (negative_count / total * 100) if total > 0 else 0
        st.metric("😞 Negative", f"{negative_count}", f"{negative_pct:.1f}%")
    # Bar chart
    st.bar_chart({
        "Positive": positive_count,
        "Neutral": neutral_count,
        "Negative": negative_count
    })

def main():
    st.title("🎬 YouTube Sentiment Analyzer")

    st.markdown("Analyze the sentiment of YouTube video comments using AI")

    # load the chached model
    analyzer = load_analyzer()

    # URL input field
    video_url = st.text_input(
        "Enter YouTube Video URL:",
        placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )

    # Analyze button
    if st.button("🔍 Analyze Comments", type="primary"):
        if not video_url:
            st.error("Please enter a YouTube URL")
            return
        try:
            video_id = extract_video_id(video_url)
            
            API_KEY = st.secrets["YOUTUBE_API_KEY"]
            
            # initialization
            repo = InMemoryCommentRepo()
            fetcher = YoutubeCommentFetcher(API_KEY, video_id)
            service = CommentService(repo, analyzer, fetcher)
            
            # Fetch comments
            with st.spinner(" Fetching comments from YouTube..."):
                comments = service.fetch_and_store_comments()
            
            if not comments:
                st.warning("No comments found for this video")
                return
            
            st.success(f" Fetched {len(comments)} comments")
            
            # Analyze sentiment
            with st.spinner(f" Analyzing sentiment of {len(comments)} comments..."):
                service.analyze_all_comments()
            
            st.success(" Analysis complete!")
            
            # Display results
            display_results(service)

        except InvalidURLError:
            st.error(" Invalid URL format")
            st.info("Please use: https://www.youtube.com/watch?v=VIDEO_ID")
            
        except APIQuotaExceededError:
            st.error(" YouTube API quota exceeded for today")
            st.info("Please try again tomorrow or use a different API key.")
        
        except VideoNotFoundError:
            st.error(" Video not found")
            st.info("The video might be private, deleted, or the ID is incorrect.")
        
        except CommentsDisabledError:
            st.error(" Comments are disabled for this video")
            st.info("Please try a different video.")
        
        except APIConnectionError:
            st.error(" Failed to connect to YouTube API")
            st.info("Please check your internet connection.")
        
        except Exception as e:
            st.error(f" An unexpected error occurred: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()