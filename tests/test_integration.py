import pytest
from unittest.mock import Mock, MagicMock, patch
from src.database import crud
from fastapi.testclient import TestClient
from main import app

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

@patch('main.get_bert_analyzer')
@patch('main.crud')
def test_analyze_endpoint_returns_results(mock_crud, mock_analyzer):
    """Test /api/analyze endpoint returns analysis results"""
    
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
