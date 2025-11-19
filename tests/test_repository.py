import pytest
from src.repositories.commentRepository import InMemoryCommentRepo
from src.domain.models import Comment, Sentiment, SentimentLabel
from src.utils.exceptions import CommentNotFoundError


class TestInMemoryCommentRepo:
    """Unit tests for InMemoryCommentRepo"""
    
    @pytest.fixture
    def repo(self):
        """Fixture to provide a fresh repository for each test"""
        return InMemoryCommentRepo()
    
    @pytest.fixture
    def sample_comment(self):
        """Fixture to provide a sample comment"""
        return Comment(
            videoId="dQw4w9WgXcQ",
            id=0,
            author="TestUser",
            text="Great video!"
        )
    
    def test_repo_initialization(self, repo):
        """Test that repository initializes empty"""
        assert len(repo.comments) == 0
        assert repo.next_id == 1
    
    def test_add_comment_assigns_id(self, repo, sample_comment):
        """Test that adding a comment assigns an ID"""
        repo.add(sample_comment)
        
        assert sample_comment.id == 1
        assert repo.next_id == 2
    
    def test_add_multiple_comments(self, repo):
        """Test adding multiple comments increments IDs correctly"""
        comment1 = Comment(videoId="abc", id=0, author="User1", text="Text1")
        comment2 = Comment(videoId="abc", id=0, author="User2", text="Text2")
        comment3 = Comment(videoId="abc", id=0, author="User3", text="Text3")
        
        repo.add(comment1)
        repo.add(comment2)
        repo.add(comment3)
        
        assert comment1.id == 1
        assert comment2.id == 2
        assert comment3.id == 3
        assert repo.next_id == 4
        assert len(repo.comments) == 3
    
    def test_add_comment_with_existing_id(self, repo):
        """Test that adding a comment with existing non-zero ID keeps that ID"""
        comment = Comment(videoId="abc", id=99, author="User", text="Text")
        repo.add(comment)
        
        assert comment.id == 99
        assert repo.next_id == 1  # next_id unchanged