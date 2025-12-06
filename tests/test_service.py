import pytest
from unittest.mock import Mock
from src.services.comment_service import CommentService
from src.domain.models import Comment
    

def test_service_initializes_with_dependencies():
    """Test that service stores its dependencies"""
    
    mock_repo = Mock()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    service = CommentService(
        comment_repository=mock_repo,
        sentiment_analyzer=mock_analyzer,
        comment_fetcher=mock_fetcher
    )
    
    assert service.comment_repo == mock_repo
    assert service.analyzer == mock_analyzer
    assert service.comment_fetcher == mock_fetcher


def test_service_fetch_returns_comment_objects():
    """Test that fetch_and_store_comments returns list of Comment objects"""

    mock_repo = Mock()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    # Mock fetcher returns raw comments
    mock_fetcher.get_comments.return_value = [
        {"author": "User1", "text": "Great!", "video_id": "abc123"}
    ]
    
    service = CommentService(mock_repo, mock_analyzer, mock_fetcher)
    result = service.fetch_and_store_comments()
    
    assert len(result) == 1
    assert isinstance(result[0], Comment)
    assert result[0].author == "User1"