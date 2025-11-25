"""
FastAPI Backend for YouTube Sentiment Analyzer (Hybrid Architecture)
- Streamlit handles: UI + OAuth (streamlit-oauth)
- FastAPI handles: Video analysis + Database operations
"""
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

# Import your modules
from src.database.db import get_session
from src.database import crud
from src.backend.analyzers.bert_sentiment_analyzer import BertSentimentAnalyzer
from src.backend.api.youtube_comment_fetcher import YoutubeCommentFetcher
from src.utils.logger import get_logger
from src.utils.exceptions import (
    APIQuotaExceededError,
    VideoNotFoundError,
    CommentsDisabledError,
    APIConnectionError
)

# Initialize logger
logger = get_logger()

# Create FastAPI app
app = FastAPI(
    title="YouTube Sentiment Analyzer API",
    description="Hybrid Architecture: Analysis backend for Streamlit frontend",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for Streamlit
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "http://localhost:8501,https://*.streamlit.app").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize BERT analyzer (singleton pattern)
_bert_analyzer = None

def get_bert_analyzer() -> BertSentimentAnalyzer:
    """Get or create BERT sentiment analyzer (singleton)"""
    global _bert_analyzer
    if _bert_analyzer is None:
        logger.info("Initializing BERT sentiment analyzer...")
        _bert_analyzer = BertSentimentAnalyzer()
        logger.info("✅ BERT analyzer ready")
    return _bert_analyzer


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for video analysis"""
    youtube_video_id: str
    user_id: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "youtube_video_id": "dQw4w9WgXcQ",
                "user_id": 1
            }
        }


class AnalyzeResponse(BaseModel):
    """Response model for analysis results"""
    success: bool
    message: str
    analysis_id: Optional[int] = None
    video_id: Optional[int] = None
    total_comments: Optional[int] = None
    positive_count: Optional[int] = None
    negative_count: Optional[int] = None
    neutral_count: Optional[int] = None
    positive_percentage: Optional[float] = None
    negative_percentage: Optional[float] = None
    neutral_percentage: Optional[float] = None


class TopNegativeComment(BaseModel):
    """Model for top negative comment"""
    author: str
    text: str
    confidence: float


class VideoListItem(BaseModel):
    """Model for video list item"""
    video_id: int
    youtube_video_id: str
    title: Optional[str]
    created_at: str
    analysis_count: int


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str
    status_code: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_video_id(youtube_url_or_id: str) -> str:
    """
    Extract video ID from YouTube URL or return ID if already extracted
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - VIDEO_ID (direct)
    """
    if "youtube.com/watch?v=" in youtube_url_or_id:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(youtube_url_or_id)
        return parse_qs(parsed.query)['v'][0]
    elif "youtu.be/" in youtube_url_or_id:
        return youtube_url_or_id.split("youtu.be/")[1].split("?")[0]
    else:
        # Assume it's already a video ID
        return youtube_url_or_id


def get_current_user(user_id: int, db: Session) -> crud.User:
    """
    Validate and get current user
    
    Raises:
        HTTPException: If user not found
    """
    user = crud.get_user_by_id(db, user_id)
    if not user:
        logger.warning(f"Unauthorized access attempt: user_id={user_id}")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. User not found. Please login again."
        )
    return user


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "YouTube Sentiment Analyzer API",
        "version": "2.0.0",
        "architecture": "Hybrid (Streamlit UI + FastAPI Backend)",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint - checks database connectivity"""
    from src.database.db import engine
    
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "bert_model": "loaded" if _bert_analyzer else "not_loaded"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ============================================================================
# VIDEO ANALYSIS ENDPOINT
# ============================================================================

@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_video(
    request: AnalyzeRequest,
    db: Session = Depends(get_session)
):
    """
    Analyze YouTube video comments with BERT sentiment analysis
    
    Flow:
    1. Validate user exists in database
    2. Get user's YouTube access token from database
    3. Fetch comments from YouTube API
    4. Run BERT sentiment analysis on each comment
    5. Store comments and sentiments in database
    6. Return analysis summary
    
    Args:
        request: AnalyzeRequest with youtube_video_id and user_id
        db: Database session (injected)
        
    Returns:
        AnalyzeResponse with analysis results
        
    Raises:
        HTTPException: 401 (unauthorized), 422 (invalid input), 500 (internal error)
    """
    try:
        logger.info(f"🎬 Starting analysis: video={request.youtube_video_id}, user={request.user_id}")
        
        # 1. Validate user
        user = get_current_user(request.user_id, db)
        logger.debug(f"✅ User validated: {user.email}")
        
        # 2. Extract clean video ID
        try:
            video_id = extract_video_id(request.youtube_video_id)
            logger.debug(f"📹 Extracted video ID: {video_id}")
        except Exception as e:
            logger.error(f"❌ Invalid video ID/URL: {request.youtube_video_id}")
            raise HTTPException(
                status_code=422,
                detail=f"Invalid YouTube video ID or URL. Please check the format."
            )
        
        # 3. Check if user has valid access token
        if not user.access_token:
            logger.error(f"❌ User {user.user_id} has no access token")
            raise HTTPException(
                status_code=401,
                detail="No YouTube access token found. Please login again."
            )
        
        # 4. Create or get video in database (with title)
        # First, try to get the video title from YouTube
        video_title = None
        try:
            import requests as req
            title_response = req.get(
                f"https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "snippet",
                    "id": video_id,
                    "fields": "items(snippet(title))"
                },
                headers={"Authorization": f"Bearer {user.access_token}"},
                timeout=5
            )
            if title_response.status_code == 200:
                title_data = title_response.json()
                if title_data.get("items"):
                    video_title = title_data["items"][0]["snippet"]["title"]
                    logger.info(f"📺 Video title: {video_title}")
        except Exception as e:
            logger.warning(f"Could not fetch video title: {e}")
        
        video = crud.create_or_get_video(
            db,
            youtube_video_id=video_id,
            user_id=user.user_id,
            title=video_title
        )
        logger.info(f"📊 Video DB ID: {video.video_id}")
        
        # 4.5. Check for recent cached analysis (within 24 hours)
        logger.info("🔍 Checking for cached analysis...")
        cached_analysis = crud.get_recent_analysis(db, video_id, hours=24)
        
        if cached_analysis:
            logger.info(f"✅ Found cached analysis from {cached_analysis.created_at}")
            
            # Parse top negative comments from cache
            top_negative = crud.parse_top_negative_comments(cached_analysis)
            
            return AnalyzeResponse(
                success=True,
                message="Retrieved cached analysis!",
                analysis_id=cached_analysis.analysis_id,
                video_id=video.video_id,
                total_comments=cached_analysis.total_comments,
                positive_count=cached_analysis.positive_count,
                negative_count=cached_analysis.negative_count,
                neutral_count=cached_analysis.neutral_count,
                positive_percentage=float(cached_analysis.positive_percentage),
                negative_percentage=float(cached_analysis.negative_percentage),
                neutral_percentage=float(cached_analysis.neutral_percentage)
            )
        
        logger.info("📥 No cached analysis found, proceeding with fresh analysis...")
        
        # 5. Fetch comments from YouTube
        try:
            logger.info("📥 Fetching comments from YouTube...")
            fetcher = YoutubeCommentFetcher(user.access_token, video_id)
            raw_comments = fetcher.get_comments()
            logger.info(f"✅ Fetched {len(raw_comments)} comments")
            
            if not raw_comments:
                logger.warning("⚠️ No comments found for video")
                return AnalyzeResponse(
                    success=False,
                    message="No comments found for this video. The video may have comments disabled or no comments yet."
                )
                
        except APIQuotaExceededError:
            logger.error("❌ YouTube API quota exceeded")
            raise HTTPException(
                status_code=429,
                detail="YouTube API quota exceeded. Please try again tomorrow or use a different API key."
            )
        except CommentsDisabledError:
            logger.warning(f"⚠️ Comments disabled for video: {video_id}")
            raise HTTPException(
                status_code=422,
                detail="Comments are disabled for this video. Please try a different video."
            )
        except VideoNotFoundError:
            logger.warning(f"⚠️ Video not found: {video_id}")
            raise HTTPException(
                status_code=404,
                detail="Video not found. Please check the video ID and try again."
            )
        except APIConnectionError as e:
            logger.error(f"❌ YouTube API connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to YouTube API. Please try again later."
            )
        except Exception as e:
            logger.exception("❌ Unexpected error fetching comments")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch comments: {str(e)}"
            )
        
        # 6. Run sentiment analysis with BERT
        try:
            logger.info("🤖 Running BERT sentiment analysis...")
            analyzer = get_bert_analyzer()
            
            sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
            comments_data = []
            negative_comments = []

            # --- BATCH ANALYSIS ---
            logger.info("Running batch analysis...")
            comment_texts = [comment["text"] for comment in raw_comments]
            batch_results = analyzer.analyze_comments_batch(comment_texts, batch_size=32)

            # Reset counters and lists
            sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
            comments_data = []
            negative_comments = []

            # Process batch results
            for i, (raw_comment, result) in enumerate(zip(raw_comments, batch_results)):
                label = result["label"]
                confidence = result["score"]

                sentiment_counts[label] += 1

                # Prepare comment data for DB
                comment_data = {
                    "author": raw_comment["author"],
                    "text": raw_comment["text"],
                    "sentiment": label,
                    "confidence": confidence
                }
                comments_data.append(comment_data)

                # Track negative comments
                if label == "NEGATIVE":
                    negative_comments.append({
                        "author": raw_comment["author"],
                        "text": raw_comment["text"],
                        "confidence": confidence
                    })

                # Log progress every 50 comments
                if (i + 1) % 50 == 0:
                    logger.info(f"📊 Analyzed {i + 1}/{len(raw_comments)} comments", flush = True)

            logger.info(f"✅ Analysis complete: {sentiment_counts}")
            
        except Exception as e:
            logger.exception("❌ Sentiment analysis failed")
            raise HTTPException(
                status_code=500,
                detail=f"Sentiment analysis failed: {str(e)}"
            )
        
        # 7. Store comments in database
        try:
            logger.info("💾 Storing comments in database...")
            stored_comments = crud.store_comments_bulk(
                db,
                video_id=video.video_id,
                comments_data=comments_data
            )
            logger.info(f"✅ Stored {len(stored_comments)} comments")
        except Exception as e:
            logger.error(f"⚠️ Failed to store comments: {e}")
            # Continue anyway - we have the analysis results
            logger.warning("⚠️ Continuing without storing comments")
        
        # 8. Get top 5 negative comments (sorted by confidence)
        negative_comments.sort(key=lambda x: x["confidence"], reverse=True)
        top_negative = negative_comments[:5]
        
        # 9. Store analysis summary in database
        try:
            logger.info("💾 Storing analysis summary...")
            total = len(raw_comments)
            analysis = crud.store_analysis(
                db,
                video_id=video.video_id,
                user_id=user.user_id,
                total_comments=total,
                positive_count=sentiment_counts["POSITIVE"],
                negative_count=sentiment_counts["NEGATIVE"],
                neutral_count=sentiment_counts["NEUTRAL"],
                top_negative_comments=top_negative
            )
            logger.info(f"✅ Analysis stored with ID: {analysis.analysis_id}")
            
            # 10. Return success response
            return AnalyzeResponse(
                success=True,
                message="Analysis completed successfully! 🎉",
                analysis_id=analysis.analysis_id,
                video_id=video.video_id,
                total_comments=analysis.total_comments,
                positive_count=analysis.positive_count,
                negative_count=analysis.negative_count,
                neutral_count=analysis.neutral_count,
                positive_percentage=float(analysis.positive_percentage),
                negative_percentage=float(analysis.negative_percentage),
                neutral_percentage=float(analysis.neutral_percentage)
            )
            
        except Exception as e:
            logger.exception("❌ Failed to store analysis")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store analysis results: {str(e)}"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions (already handled)
        raise
    except Exception as e:
        logger.exception("❌ Unexpected error during analysis")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


# ============================================================================
# VIDEO LIST ENDPOINT
# ============================================================================

@app.get("/api/videos", response_model=List[VideoListItem])
def list_videos(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_session)
):
    """
    Get list of videos analyzed by user
    
    Args:
        user_id: User ID
        limit: Maximum number of videos to return (default: 10)
        db: Database session
        
    Returns:
        List of videos with analysis counts
    """
    try:
        # Validate user
        user = get_current_user(user_id, db)
        
        # Get videos
        videos = crud.get_videos_by_user(db, user.user_id, limit=limit)
        
        # Build response with analysis counts
        result = []
        for video in videos:
            analyses = crud.get_analyses_by_video(db, video.video_id)
            
            result.append(VideoListItem(
                video_id=video.video_id,
                youtube_video_id=video.youtube_video_id,
                title=video.title,
                created_at=video.created_at.isoformat(),
                analysis_count=len(analyses)
            ))
        
        logger.info(f"📹 Retrieved {len(result)} videos for user {user_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("❌ Error retrieving videos")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve videos: {str(e)}"
        )


# ============================================================================
# TOP NEGATIVE COMMENTS ENDPOINT
# ============================================================================

@app.get("/api/videos/{youtube_video_id}/comments/top-negative", response_model=List[TopNegativeComment])
def get_top_negative_comments(
    youtube_video_id: str,
    user_id: int,
    limit: int = 5,
    db: Session = Depends(get_session)
):
    """
    Get top negative comments for a video
    
    Args:
        youtube_video_id: YouTube video ID
        user_id: User ID (for authorization)
        limit: Number of top comments to return (default: 5)
        db: Database session
        
    Returns:
        List of top negative comments with confidence scores
    """
    try:
        # Validate user
        user = get_current_user(user_id, db)
        
        # Get video
        video = crud.get_video_by_youtube_id(db, youtube_video_id)
        if not video:
            raise HTTPException(
                status_code=404,
                detail="Video not found. Please analyze it first."
            )
        
        # Get latest analysis (contains top negative comments)
        analysis = crud.get_latest_analysis_for_video(db, video.video_id)
        
        if analysis and analysis.top_negative_comments:
            # Parse from analysis (faster)
            top_negative = crud.parse_top_negative_comments(analysis)
            if top_negative:
                return [TopNegativeComment(**comment) for comment in top_negative[:limit]]
        
        # Fallback: Query from comments table
        negative_comments = crud.get_negative_comments(db, video.video_id, limit=limit)
        
        return [
            TopNegativeComment(
                author=comment.author,
                text=comment.text,
                confidence=float(comment.confidence)
            )
            for comment in negative_comments
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("❌ Error retrieving top negative comments")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve comments: {str(e)}"
        )

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return {
        "error": "Not Found",
        "detail": "The requested resource was not found",
        "status_code": 404
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.exception("Internal server error")
    return {
        "error": "Internal Server Error",
        "detail": "An unexpected error occurred. Please try again later.",
        "status_code": 500
    }


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 FastAPI application starting...")
    logger.info(f"📚 API docs available at /docs")
    logger.info(f"🌐 Allowed CORS origins: {', '.join(FRONTEND_ORIGINS)}")
    
    # Pre-load BERT model
    try:
        get_bert_analyzer()
        logger.info("✅ BERT model pre-loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to pre-load BERT model: {e}")
        logger.warning("⚠️ Model will load on first analysis request")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("🛑 FastAPI application shutting down...")


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("=" * 60)
    print("🚀 YouTube Sentiment Analyzer - FastAPI Backend")
    print("=" * 60)
    print(f"📍 Server: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    print(f"🌐 CORS Origins: {', '.join(FRONTEND_ORIGINS)}")
    print("=" * 60)
    print()
    print("Architecture: Hybrid")
    print("  - Streamlit: UI + OAuth (streamlit-oauth)")
    print("  - FastAPI: Analysis + Database")
    print()
    print("Press CTRL+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )