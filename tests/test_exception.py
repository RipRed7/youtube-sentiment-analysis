from src.utils.exceptions import APIQuotaExceededError
from src.utils.exceptions import CommentNotFoundError

def test_comment_not_found_error_includes_id():
    """Test that CommentNotFoundError includes comment ID in details"""
    
    error = CommentNotFoundError(comment_id=123)
    
    assert "123" in str(error) or 123 in error.details.values()


def test_api_quota_exceeded_error_has_message():
    """Test that APIQuotaExceededError has descriptive message"""
    
    error = APIQuotaExceededError()
    
    assert "quota" in str(error).lower()