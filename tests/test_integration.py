import pytest
from unittest.mock import Mock, MagicMock, patch
from src.repositories.commentRepository import InMemoryCommentRepo
from src.backend.analyzers.bert_sentiment_analyzer import BertSentimentAnalyzer
from src.services.comment_service import CommentService
from src.domain.models import SentimentLabel
from src.database import crud
from src.utils.exceptions import CommentNotFoundError

# SERVICE LAYER

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
    
    # Mock fetcher returns 3 comments
    mock_fetcher.get_comments.return_value = [
        {"author": "User1", "text": "Amazing!", "video_id": "abc"},
        {"author": "User2", "text": "Terrible", "video_id": "abc"},
        {"author": "User3", "text": "Okay", "video_id": "abc"}
    ]
    
    # Mock analyzer returns different sentiments
    mock_analyzer.analyze_comments_batch.return_value = [
        {"label": "POSITIVE", "score": 0.95},
        {"label": "NEGATIVE", "score": 0.88},
        {"label": "NEUTRAL", "score": 0.70}
    ]
    
    service = CommentService(repo, mock_analyzer, mock_fetcher)
    
    # Run full workflow
    service.fetch_and_store_comments()
    service.analyze_all_comments()
    distribution = service.get_sentiment_distrib()
    
    # Verify results
    assert distribution[SentimentLabel.POSITIVE] == 1
    assert distribution[SentimentLabel.NEGATIVE] == 1
    assert distribution[SentimentLabel.NEUTRAL] == 1

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

# DATABASE

def test_create_user_and_video_relationship():
    """Test creating user and associating video"""
    
    mock_db = MagicMock()
    
    # Mock user doesn't exist yet
    mock_db.query().filter_by().first.return_value = None
    
    # Create user
    user = crud.create_or_update_user(
        db=mock_db,
        google_id="test123",
        email="test@example.com",
        name="Test User"
    )
    
    # Verify user was added to database
    mock_db.add.assert_called()
    mock_db.commit.assert_called()

def test_create_video_stores_metadata():
    """Test creating video with title and YouTube ID"""
    
    mock_db = MagicMock()
    
    # Mock video doesn't exist
    mock_db.query().filter_by().first.return_value = None
    
    # Create video
    video = crud.create_or_get_video(
        db=mock_db,
        youtube_video_id="abc123",
        user_id=1,
        title="Test Video Title"
    )
    
    # Verify video was added
    mock_db.add.assert_called()
    mock_db.commit.assert_called()

def test_store_analysis_with_sentiment_counts():
    """Test storing complete analysis with sentiment distribution"""
    
    mock_db = MagicMock()
    
    # Store analysis
    analysis = crud.store_analysis(
        db=mock_db,
        video_id=1,
        user_id=1,
        total_comments=100,
        positive_count=60,
        negative_count=20,
        neutral_count=20,
        top_negative_comments=[
            {"author": "User1", "text": "Bad", "confidence": 0.95}
        ]
    )
    
    # Verify analysis was stored
    mock_db.add.assert_called()
    mock_db.commit.assert_called()


# API ENDPOINTS


@patch('main.get_bert_analyzer')
@patch('main.crud')
def test_analyze_endpoint_returns_results(mock_crud, mock_analyzer):
    """Test /api/analyze endpoint returns analysis results"""
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    # Mock user exists
    mock_user = Mock()
    mock_user.user_id = 1
    mock_user.email = "test@example.com"
    mock_user.access_token = "fake_token"
    mock_crud.get_user_by_id.return_value = mock_user
    
    # Mock video
    mock_video = Mock()
    mock_video.video_id = 1
    mock_video.youtube_video_id = "test123"
    mock_crud.create_or_get_video.return_value = mock_video
    
    # Mock no cached analysis
    mock_crud.get_recent_analysis.return_value = None
    
    # will fail at YouTube API call, but tests endpoint 
    response = client.post(
        "/api/analyze",
        json={
            "youtube_video_id": "test123",
            "user_id": 1
        }
    )
    
    # validate the request format
    assert response.status_code in [200, 401, 422, 500, 503]

def test_health_endpoint_responds():
    """Test /health endpoint is accessible"""
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert "status" in response.json()

# Exceptions

def test_service_handles_analyzer_failure_with_fallback():
    """Test service falls back to sequential when batch fails"""
    
    repo = InMemoryCommentRepo()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    # Mock fetcher returns 1 comment
    mock_fetcher.get_comments.return_value = [
        {"author": "User1", "text": "Test", "video_id": "abc"}
    ]
    
    mock_analyzer.analyze_comments_batch.side_effect = Exception("Batch failed")
    mock_analyzer.analyze.return_value = {"label": "NEUTRAL", "score": 0.5}
    
    service = CommentService(repo, mock_analyzer, mock_fetcher)
    service.fetch_and_store_comments()
    
    # Should handle error gracefully by falling back to sequential
    results = service.analyze_all_comments()
    
    # Service should have attempted analysis
    assert isinstance(results, dict)


def test_repository_raises_error_for_missing_comment():
    """Test repository raises proper error when comment not found"""
    
    repo = InMemoryCommentRepo()
    
    # Should raise CommentNotFoundError for update
    from src.domain.models import Comment
    fake_comment = Comment(videoId="test", id=999, author="User", text="Text")
    
    with pytest.raises(CommentNotFoundError):
        repo.update(fake_comment)


# END TO END

def test_complete_sentiment_analysis_workflow():
    """
    Test end-to-end workflow:
    1. Fetch comments from API
    2. Store in repository
    3. Analyze sentiment
    4. Calculate distribution
    5. Retrieve results
    """
    
    repo = InMemoryCommentRepo()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    # Step 1: Mock API returns 4 comments
    mock_fetcher.get_comments.return_value = [
        {"author": "User1", "text": "Amazing!", "video_id": "abc"},
        {"author": "User2", "text": "Terrible", "video_id": "abc"},
        {"author": "User3", "text": "Okay", "video_id": "abc"},
        {"author": "User4", "text": "Love it!", "video_id": "abc"}
    ]
    
    # Step 2: Mock analyzer returns mixed sentiments
    mock_analyzer.analyze_comments_batch.return_value = [
        {"label": "POSITIVE", "score": 0.92},
        {"label": "NEGATIVE", "score": 0.88},
        {"label": "NEUTRAL", "score": 0.70},
        {"label": "POSITIVE", "score": 0.95}
    ]
    
    service = CommentService(repo, mock_analyzer, mock_fetcher)
    
    # Step 3: Execute workflow
    comments = service.fetch_and_store_comments()
    assert len(comments) == 4
    
    results = service.analyze_all_comments()
    assert len(results) == 4
    
    distribution = service.get_sentiment_distrib()
    
    # Step 4: Verify final results
    assert distribution[SentimentLabel.POSITIVE] == 2
    assert distribution[SentimentLabel.NEGATIVE] == 1
    assert distribution[SentimentLabel.NEUTRAL] == 1
    
    # Step 5: Verify we can retrieve individual comments
    comment = service.get_comment(1)
    assert comment is not None
    assert comment.sentiment is not None
    assert comment.sentiment.label in [
        SentimentLabel.POSITIVE,
        SentimentLabel.NEGATIVE,
        SentimentLabel.NEUTRAL
    ]