"""SQLAlchemy ORM Models (Synchronous) for Neon PostgreSQL - Simple Version"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from typing import Optional

Base = declarative_base()


# ============================================================================
# SQLAlchemy ORM Models (Synchronous)
# ============================================================================

class User(Base):
    """User model - stores Google OAuth users"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"


class Video(Base):
    """Video model - stores YouTube video metadata"""
    __tablename__ = 'videos'
    
    video_id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_video_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    title = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Video(video_id={self.video_id}, youtube_video_id={self.youtube_video_id})>"


class Analysis(Base):
    """Analysis model - stores sentiment analysis results"""
    __tablename__ = 'analyses'
    
    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), index=True)
    total_comments = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    positive_percentage = Column(Numeric(5, 2))
    negative_percentage = Column(Numeric(5, 2))
    neutral_percentage = Column(Numeric(5, 2))
    top_negative_comments = Column(Text)  # JSON string
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="analyses")
    user = relationship("User", back_populates="analyses")

    def __repr__(self):
        return f"<Analysis(analysis_id={self.analysis_id}, total_comments={self.total_comments})>"


class Comment(Base):
    """Comment model - stores raw YouTube comments"""
    __tablename__ = 'comments'
    
    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, index=True)
    author = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    sentiment = Column(String(20))  # POSITIVE, NEGATIVE, NEUTRAL
    confidence = Column(Numeric(5, 4))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="comments")

    def __repr__(self):
        return f"<Comment(comment_id={self.comment_id}, author={self.author})>"


# ============================================================================
# Pydantic Schemas for FastAPI Responses
# ============================================================================

class UserSchema(BaseModel):
    """Pydantic schema for User responses"""
    user_id: int
    google_id: str
    email: EmailStr
    name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2
        # For Pydantic v1, use: orm_mode = True


class VideoSchema(BaseModel):
    """Pydantic schema for Video responses"""
    video_id: int
    youtube_video_id: str
    user_id: Optional[int]
    title: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisSchema(BaseModel):
    """Pydantic schema for Analysis responses"""
    analysis_id: int
    video_id: int
    user_id: Optional[int]
    total_comments: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: Optional[float]
    negative_percentage: Optional[float]
    neutral_percentage: Optional[float]
    top_negative_comments: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentSchema(BaseModel):
    """Pydantic schema for Comment responses"""
    comment_id: int
    video_id: int
    author: str
    text: str
    sentiment: Optional[str]
    confidence: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True