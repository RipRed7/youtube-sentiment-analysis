import pytest 
from unittest.mock import Mock, patch
from src.database.models import Comment

def test_comment_stores_basic_info():
    """Test that Comment stores author, text, and video ID"""
    
    comment = Comment(
        videoId="abc123",
        id=1,
        author="TestUser",
        text="Great video!"
    )
    
    assert comment.videoId == "abc123"
    assert comment.author == "TestUser"
    assert comment.text == "Great video!"
