import streamlit as st
import os
from urllib.parse import urlparse, parse_qs
import matplotlib.pyplot as plt
from wordcloud import WordCloud

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
from src.utils.logger import get_logger


# Configure the Streamlit page
st.set_page_config(
    page_title="YouTube Sentiment Analyzer",
    page_icon="🎬",
    layout="wide"
)

# init logger
logger = get_logger()

@st.cache_resource

def load_analyzer():
    #load analyzer for caching
    logger.info("Loading sentiment analyzer for Streamlit")
    return BertSentimentAnalyzer()

def extract_video_id(url: str) -> str:
    # Handle different YouTube URL formats
    logger.debug(f"Extracting video ID from URL")

    try:
        if "youtube.com/watch?v=" in url:
            parsed = urlparse(url)
            video_id = parse_qs(parsed.query)['v'][0]
            logger.debug(f"Extracted video ID: {video_id}")
            return video_id
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
            logger.debug(f"Extracted video ID from short URL: {video_id}")
            return video_id
        else:
            logger.warning(f"Invalid URL format: {url}")
            raise InvalidURLError(url)
    except InvalidURLError:
        raise
    except Exception as e:
        logger.error(f"Failed to extract video ID from URL: {url}")
        raise InvalidURLError(url)

def create_pie_chart(distribution):
    logger.debug("Creating pie chart for sentiment distribution")

    # prepare data
    labels = []
    sizes = []
    colors = []

    if distribution[SentimentLabel.POSITIVE] > 0:
        labels.append('Positive 😊')
        sizes.append(distribution[SentimentLabel.POSITIVE])
        colors.append('#4CAF50')

    if distribution[SentimentLabel.NEUTRAL] > 0:
        labels.append('Neutral 😐')
        sizes.append(distribution[SentimentLabel.NEUTRAL])
        colors.append('#FFC107')  # Amber

    if distribution[SentimentLabel.NEGATIVE] > 0:
        labels.append('Negative 😞')
        sizes.append(distribution[SentimentLabel.NEGATIVE])
        colors.append('#F44336')  # Red

    # Create pie chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
           startangle=90, textprops={'fontsize': 14, 'weight': 'bold'})
    ax.axis('equal')
    plt.title('Sentiment Distribution', fontsize=16, weight='bold', pad=20)
    
    logger.debug("Pie chart created successfully")
    return fig

def create_word_cloud(service: CommentService):
    logger.debug("Creating word cloud from comments")

    comments = service.get_all_comments()

    if not comments:
        logger.warning("No comments available")
        return None
    
    all_text = ' '.join([comment.text for comment in comments])

    #create cloud
    wordcloud = WordCloud(
        width = 800,
        height = 400,
        background_color = 'white',
        colormap = 'inferno',
        max_words = 100,
        relative_scaling = 0.5,
        min_font_size = 10
    ).generate(all_text)

    fig, ax = plt.subplots(figsize = (12, 6))
    ax.imshow(wordcloud, interpolation = 'bilinear')
    ax.axis('off')
    plt.title('Comment Word Cloud', fontsize = 16, weight = 'bold', pad = 20)
    plt.tight_layout(pad = 0)

    logger.debug("Word cloud created successfully")
    return fig
    
def display_results(service: CommentService):
    logger.debug("Displaying sentiment analysis results")

    # Get distribution
    distribution = service.get_sentiment_distrib()
    total = sum(distribution.values())

    logger.info(f"Displaying results for {total} comments")

    # Display sentiment visuals
    st.subheader("📊 Sentiment Distribution")
    col1, col2, col3 = st.columns(3)
    with col1:
        positive_count = distribution[SentimentLabel.POSITIVE]
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

    #Bar chart
    st.bar_chart({
      "Positive": positive_count,
       "Neutral": neutral_count,
       "Negative": negative_count
    })

    # Create two columns for visualizations
    col_left, col_right = st.columns(2)

    # Display pie chart
    with col_left:
        st.subheader("🥧 Sentiment Breakdown")
        pie_chart = create_pie_chart(distribution)
        st.pyplot(pie_chart)
    
    # Display word cloud
    with col_right:
        st.subheader("☁️ Most Common Words")
        word_cloud = create_word_cloud(service)
        if word_cloud:
            st.pyplot(word_cloud)
        else:
            st.info("Not enough comment data to generate word cloud")

    logger.debug("Results displayed successfully")

def main():
    logger.info("Starting Streamlit YouTube Sentiment App")

    st.title("🎬 YouTube Sentiment Analyzer")
    st.markdown("Analyze the sentiment of YouTube video comments using AI")

    # load the cached model
    analyzer = load_analyzer()
    logger.info("Loaded cached model")

    # URL input field
    video_url = st.text_input(
        "Enter YouTube Video URL:",
        placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )

    # Analyze button
    if st.button("🔍 Analyze Comments", type="primary"):
        logger.info(f"User started analysis for URL: {video_url}")

        if not video_url:
            logger.warning("Analysis attempted with empty URL")
            st.error("Please enter a YouTube URL")
            return
        
        try:
            video_id = extract_video_id(video_url)
            logger.info(f"Processing video ID: {video_id}")

            API_KEY = st.secrets["YOUTUBE_API_KEY"]
            logger.debug("API ket retreved from secrets")

            # initialization
            repo = InMemoryCommentRepo()
            fetcher = YoutubeCommentFetcher(API_KEY, video_id)
            service = CommentService(repo, analyzer, fetcher)
            logger.info("Services initalized successfully")
            
            # Fetch comments
            with st.spinner(" Fetching comments from YouTube..."):
                logger.info("Fetching comments")
                comments = service.fetch_and_store_comments()
            
            if not comments:
                logger.warning(f"No comments found for video: {video_id}")
                st.warning("No comments found for this video")
                return
            
            st.success(f" Fetched {len(comments)} comments")
            logger.info(f"Successfully fetched {len(comments)} comments")
            
            # Analyze sentiment
            with st.spinner(f" Analyzing sentiment of {len(comments)} comments..."):
                logger.info("Starting sentiment analysis")
                service.analyze_all_comments()
            
            st.success(" Analysis complete!")
            logger.info("Sentiment analysis completed successfully")
            
            # Display results
            display_results(service)

        except InvalidURLError:
            logger.error(f"Invalid URL provided: {video_url}")
            st.error(" Invalid URL format")
            st.info("Please use: https://www.youtube.com/watch?v=VIDEO_ID")
            
        except APIQuotaExceededError:
            logger.critical("Youtube API quota exceeded")
            st.error("YouTube API quota exceeded for today")
            st.info("Please try again tomorrow or use a different API key.")
        
        except VideoNotFoundError:
            logger.warning(f"Comments disabled for video: {video_url}")
            st.error(" Video not found")
            st.info("The video might be private, deleted, or the ID is incorrect.")
        
        except CommentsDisabledError:
            logger.error("API connection error occurred")
            st.error(" Comments are disabled for this video")
            st.info("Please try a different video.")
        
        except APIConnectionError:
            logger.error("API connection error occurred")
            st.error(" Failed to connect to YouTube API")
            st.info("Please check your internet connection.")
        
        except Exception as e:
            logger.exception(f"Unexpected error in Streamlit app: {str(e)}")
            st.error(f"An unexpected error occurred: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()