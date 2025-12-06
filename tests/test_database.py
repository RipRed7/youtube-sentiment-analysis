from main import extract_video_id
from src.database import crud
from src.database.models import User
from unittest.mock import MagicMock

def test_create_or_update_user_creates_new_user():
    """Test that create_or_update_user creates a new user"""
    
    mock_db = MagicMock()
    mock_db.query().filter_by().first.return_value = None  # User doesn't exist
    
    user = crud.create_or_update_user(
        db=mock_db,
        google_id="12345",
        email="test@example.com",
        name="Test User"
    )
    
    # Verify user object was created
    mock_db.add.assert_called_once()


def test_extract_video_id_from_url_handles_query_params():
    """Test video ID extraction ignores query parameters"""
    from main import extract_video_id
    
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share"
    
    video_id = extract_video_id(url)
    
    assert video_id == "dQw4w9WgXcQ"
    assert "feature" not in video_id