import pytest


def test_repository_adds_comment():
    """Test that repository can add a comment"""
    from src.repositories.commentRepository import InMemoryCommentRepo
    from src.domain.models import Comment
    
    repo = InMemoryCommentRepo()
    comment = Comment(videoId="test", id=0, author="User", text="Text")
    
    repo.add(comment)
    
    assert len(repo.comments) == 1
    assert comment.id == 1  # Should auto-assign ID


def test_repository_retrieves_comment_by_id():
    """Test that repository can find comment by ID"""
    from src.repositories.commentRepository import InMemoryCommentRepo
    from src.domain.models import Comment
    
    repo = InMemoryCommentRepo()
    comment = Comment(videoId="test", id=0, author="User", text="Text")
    repo.add(comment)
    
    retrieved = repo.get_by_id(1)
    
    assert retrieved is not None
    assert retrieved.author == "User"


def test_repository_returns_none_for_missing_id():
    """Test that repository returns None when comment doesn't exist"""
    from src.repositories.commentRepository import InMemoryCommentRepo
    
    repo = InMemoryCommentRepo()
    
    result = repo.get_by_id(999)
    
    assert result is None
