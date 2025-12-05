"""CRUD operations for database (Synchronous)"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

from src.database.models import User, Video, Analysis, Comment


# USER OPERATIONS

def create_or_update_user(
    db: Session,
    google_id: str,
    email: str,
    name: Optional[str] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    token_expires_at: Optional[datetime] = None
) -> User:
    """
    Create or update user (by google_id)
    
    Args:
        db: Database session
        google_id: Google user ID
        email: User email
        name: User name
        access_token: OAuth access token
        refresh_token: OAuth refresh token
        token_expires_at: Token expiration time
        
    Returns:
        User: Created or updated user
    """
    user = db.query(User).filter_by(google_id=google_id).first() # find user based on google_id
    
    if user:
        # Update existing user
        user.email = email
        user.name = name
        if access_token:
            user.access_token = access_token
        if refresh_token:
            user.refresh_token = refresh_token
        if token_expires_at:
            user.token_expires_at = token_expires_at
    else:
        # Create new user
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    #Get user by ID"""
    return db.query(User).filter_by(user_id=user_id).first()

# VIDEO OPERATIONS

def create_or_get_video(
    db: Session,
    youtube_video_id: str,
    user_id: Optional[int] = None,
    title: Optional[str] = None
) -> Video:
    """
    Create or get existing video
    
    Args:
        db: Database session
        youtube_video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ')
        user_id: User who analyzed the video
        title: Video title
        
    Returns:
        Video: Created or existing video
    """
    video = db.query(Video).filter_by(youtube_video_id=youtube_video_id).first()
    
    if video:
        # Update title if provided
        if title and not video.title:
            video.title = title
            db.commit()
            db.refresh(video)
        return video
    
    # Create new video
    video = Video(
        youtube_video_id=youtube_video_id,
        user_id=user_id,
        title=title
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def get_video_by_youtube_id(db: Session, youtube_video_id: str) -> Optional[Video]:
    #Get video by YouTube video ID
    return db.query(Video).filter_by(youtube_video_id=youtube_video_id).first()


def get_videos_by_user(db: Session, user_id: int, limit: int = 10) -> List[Video]:
    #Get videos analyzed by user (most recent first)
    return db.query(Video).filter_by(user_id=user_id).order_by(desc(Video.created_at)).limit(limit).all()


# COMMENT CRUD

def store_comment(
    db: Session,
    video_id: int,
    author: str,
    text: str,
    sentiment: Optional[str] = None,
    confidence: Optional[float] = None
) -> Comment:
    """
    Store a single comment
    
    Args:
        db: Database session
        video_id: Video ID (from videos table)
        author: Comment author
        text: Comment text
        sentiment: POSITIVE, NEGATIVE, or NEUTRAL
        confidence: Confidence score (0-1)
        
    Returns:
        Comment: Created comment
    """
    comment = Comment(
        video_id=video_id,
        author=author,
        text=text,
        sentiment=sentiment,
        confidence=confidence
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def store_comments_bulk(
    db: Session,
    video_id: int,
    comments_data: List[dict]
) -> List[Comment]:
    """
    Store multiple comments at once
    
    Args:
        db: Database session
        video_id: Video ID
        comments_data: List of dicts with keys: author, text, sentiment, confidence
        
    Returns:
        List[Comment]: Created comments
    """
    comments = []
    for data in comments_data:
        comment = Comment(
            video_id=video_id,
            author=data.get("author"),
            text=data.get("text"),
            sentiment=data.get("sentiment"),
            confidence=data.get("confidence")
        )
        comments.append(comment)
    
    db.add_all(comments)
    db.commit()
    
    # Refresh all comments
    for comment in comments:
        db.refresh(comment)
    
    return comments


def get_negative_comments(db: Session, video_id: int, limit: int = 10) -> List[Comment]:
    #Get top negative comments sorted by confidence (top 10)
    return (
        db.query(Comment)
        .filter_by(video_id=video_id, sentiment="NEGATIVE")
        .order_by(desc(Comment.confidence))
        .limit(limit)
        .all()
    )


# ANALYSIS OPERATIONS

def store_analysis(
    db: Session,
    video_id: int,
    user_id: Optional[int],
    total_comments: int,
    positive_count: int,
    negative_count: int,
    neutral_count: int,
    top_negative_comments: Optional[List[dict]] = None
) -> Analysis:
    """
    Store sentiment analysis results
    
    Args:
        db: Database session
        video_id: Video ID
        user_id: User who ran the analysis
        total_comments: Total number of comments
        positive_count: Number of positive comments
        negative_count: Number of negative comments
        neutral_count: Number of neutral comments
        top_negative_comments: List of top negative comments (dicts with author, text, confidence)
        
    Returns:
        Analysis: Created analysis
    """
    # Calculate percentages
    positive_pct = (positive_count / total_comments * 100) if total_comments > 0 else 0
    negative_pct = (negative_count / total_comments * 100) if total_comments > 0 else 0
    neutral_pct = (neutral_count / total_comments * 100) if total_comments > 0 else 0
    
    # Convert top negative comments to JSON string, database friendly
    top_negative_json = json.dumps(top_negative_comments) if top_negative_comments else None
    
    analysis = Analysis(
        video_id=video_id,
        user_id=user_id,
        total_comments=total_comments,
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count,
        positive_percentage=round(positive_pct, 2),
        negative_percentage=round(negative_pct, 2),
        neutral_percentage=round(neutral_pct, 2),
        top_negative_comments=top_negative_json
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analyses_by_video(db: Session, video_id: int) -> List[Analysis]:
    #Get all analyses for a video (most recent first)
    return db.query(Analysis).filter_by(video_id=video_id).order_by(desc(Analysis.created_at)).all()


def get_latest_analysis_for_video(db: Session, video_id: int) -> Optional[Analysis]:
    #Get the most recent analysis for a video
    return db.query(Analysis).filter_by(video_id=video_id).order_by(desc(Analysis.created_at)).first()

def parse_top_negative_comments(analysis: Analysis) -> Optional[List[dict]]:
    #Parse JSON string of top negative comments back to list
    if not analysis.top_negative_comments:
        return None
    try:
        return json.loads(analysis.top_negative_comments)
    except json.JSONDecodeError:
        return None
    

def get_recent_analysis(db: Session, youtube_video_id: str, hours: int = 24) -> Optional[Analysis]:
    """
    Get recent analysis for a video (within specified hours)
    
    Args:
        db: Database session
        youtube_video_id: YouTube video ID
        hours: How recent the analysis should be (default: 24 hours)
        
    Returns:
        Analysis if found within time window, None otherwise
    """
    
    video = get_video_by_youtube_id(db, youtube_video_id)
    if not video:
        return None
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    analysis = (
        db.query(Analysis)
        .filter_by(video_id=video.video_id)
        .filter(Analysis.created_at >= cutoff_time)
        .order_by(desc(Analysis.created_at))
        .first()
    )
    
    return analysis