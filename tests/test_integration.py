import pytest
from unittest.mock import Mock, patch
from src.repositories.commentRepository import InMemoryCommentRepo
from src.backend.analyzers.bert_sentiment_analyzer import BertSentimentAnalyzer
from src.services.comment_service import CommentService
from src.domain.models import SentimentLabel


def test_fetch_and_store_workflow():
    """Test fetching comments and storing them in repository"""
    repo = InMemoryCommentRepo()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    # Mock fetcher returns 2 comments
    mock_fetcher.get_comments.return_value = [
        {"author": "User1", "text": "Great!", "video_id": "abc123"},
        {"author": "User2", "text": "Nice video", "video_id": "abc123"}
    ]
    
    service = CommentService(repo, mock_analyzer, mock_fetcher)
    comments = service.fetch_and_store_comments()
    
    assert len(comments) == 2
    assert len(repo.get_all()) == 2
    assert comments[0].author == "User1"
    assert comments[1].author == "User2"


def test_analyze_and_retrieve_workflow():
    """Test analyzing comments and retrieving sentiment distribution"""
    repo = InMemoryCommentRepo()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    # Mock fetcher
    mock_fetcher.get_comments.return_value = [
        {"author": "User1", "text": "Great!", "video_id": "abc123"}
    ]
    
    # Mock analyzer returns positive sentiment
    mock_analyzer.analyze_comments_batch.return_value = [
        {"label": "POSITIVE", "score": 0.95}
    ]
    
    service = CommentService(repo, mock_analyzer, mock_fetcher)
    
    # Fetch and store
    service.fetch_and_store_comments()
    
    # Analyze
    service.analyze_all_comments()
    
    # Check distribution
    distribution = service.get_sentiment_distrib()
    assert distribution[SentimentLabel.POSITIVE] == 1
    assert distribution[SentimentLabel.NEGATIVE] == 0
    assert distribution[SentimentLabel.NEUTRAL] == 0


def test_service_handles_empty_comments():
    """Test that service handles empty comment list gracefully"""
    repo = InMemoryCommentRepo()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    # Mock fetcher returns empty list
    mock_fetcher.get_comments.return_value = []
    
    service = CommentService(repo, mock_analyzer, mock_fetcher)
    
    comments = service.fetch_and_store_comments()
    assert len(comments) == 0
    
    results = service.analyze_all_comments()
    assert len(results) == 0
    
    distribution = service.get_sentiment_distrib()
    assert all(count == 0 for count in distribution.values())


def test_multiple_sentiments_distribution():
    """Test sentiment distribution with mixed sentiments"""
    repo = InMemoryCommentRepo()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    # Mock fetcher returns 4 comments
    mock_fetcher.get_comments.return_value = [
        {"author": "User1", "text": "Great!", "video_id": "abc"},
        {"author": "User2", "text": "Terrible", "video_id": "abc"},
        {"author": "User3", "text": "Okay", "video_id": "abc"},
        {"author": "User4", "text": "Amazing!", "video_id": "abc"}
    ]
    
    # Mock analyzer returns mixed sentiments
    mock_analyzer.analyze_comments_batch.return_value = [
        {"label": "POSITIVE", "score": 0.92},
        {"label": "NEGATIVE", "score": 0.88},
        {"label": "NEUTRAL", "score": 0.70},
        {"label": "POSITIVE", "score": 0.95}
    ]
    
    service = CommentService(repo, mock_analyzer, mock_fetcher)
    
    service.fetch_and_store_comments()
    service.analyze_all_comments()
    
    distribution = service.get_sentiment_distrib()
    assert distribution[SentimentLabel.POSITIVE] == 2
    assert distribution[SentimentLabel.NEGATIVE] == 1
    assert distribution[SentimentLabel.NEUTRAL] == 1