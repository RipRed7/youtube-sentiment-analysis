"""
Minimal test suite for CI/CD - tests critical functionality only
"""
import pytest
from unittest.mock import Mock, patch
from src.domain.models import Comment, Sentiment, SentimentLabel


# ============================================================================
# DOMAIN TESTS - Critical data models
# ============================================================================

def test_sentiment_labels_exist():
    """Test that all required sentiment labels are defined"""
    assert SentimentLabel.POSITIVE.value == "POSITIVE"
    assert SentimentLabel.NEGATIVE.value == "NEGATIVE"
    assert SentimentLabel.NEUTRAL.value == "NEUTRAL"


def test_comment_creation():
    """Test basic comment creation"""
    comment = Comment(
        videoId="test123",
        id=1,
        author="TestUser",
        text="Test comment"
    )
    assert comment.id == 1
    assert comment.author == "TestUser"
    assert comment.sentiment is None


def test_sentiment_creation():
    """Test sentiment creation with confidence"""
    sentiment = Sentiment(label=SentimentLabel.POSITIVE, Confidence=0.95)
    assert sentiment.label == SentimentLabel.POSITIVE
    assert sentiment.Confidence == 0.95


# ============================================================================
# REPOSITORY TESTS - Data access layer
# ============================================================================

def test_repository_add_and_retrieve():
    """Test basic repository operations"""
    from src.repositories.commentRepository import InMemoryCommentRepo
    
    repo = InMemoryCommentRepo()
    comment = Comment(videoId="test", id=0, author="User", text="Text")
    
    repo.add(comment)
    assert comment.id == 1
    
    retrieved = repo.get_by_id(1)
    assert retrieved.author == "User"


# ============================================================================
# ANALYZER TESTS - Sentiment analysis
# ============================================================================

@patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
@patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
def test_analyzer_positive_sentiment(mock_logger, mock_pipeline):
    """Test analyzer detects positive sentiment"""
    from src.backend.analyzers.bert_sentiment_analyzer import BertSentimentAnalyzer
    
    # Reset singleton
    BertSentimentAnalyzer._pipeline = None
    BertSentimentAnalyzer._logger = None
    
    # Mock pipeline
    mock_pipe = Mock()
    mock_pipe.return_value = [{"label": "LABEL_2", "score": 0.95}]
    mock_pipeline.return_value = mock_pipe
    
    analyzer = BertSentimentAnalyzer()
    result = analyzer.analyze("This is great!")
    
    assert result["label"] == "POSITIVE"
    assert result["score"] == 0.95


@patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
@patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
def test_analyzer_handles_empty_text(mock_logger, mock_pipeline):
    """Test analyzer handles empty input gracefully"""
    from src.backend.analyzers.bert_sentiment_analyzer import BertSentimentAnalyzer
    
    BertSentimentAnalyzer._pipeline = None
    BertSentimentAnalyzer._logger = None
    
    mock_pipeline.return_value = Mock()
    
    analyzer = BertSentimentAnalyzer()
    result = analyzer.analyze("")
    
    assert result["label"] == "NEUTRAL"
    assert result["score"] == 0.0


# ============================================================================
# SERVICE TESTS - Business logic
# ============================================================================

def test_service_initialization():
    """Test service layer initializes correctly"""
    from src.services.comment_service import CommentService
    
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


def test_service_analyze_comment():
    """Test service can analyze a comment"""
    from src.services.comment_service import CommentService
    
    mock_repo = Mock()
    mock_analyzer = Mock()
    mock_fetcher = Mock()
    
    comment = Comment(videoId="test", id=1, author="User", text="Good!")
    mock_repo.get_by_id.return_value = comment
    mock_analyzer.analyze.return_value = {"label": "POSITIVE", "score": 0.9}
    
    service = CommentService(mock_repo, mock_analyzer, mock_fetcher)
    result = service.analyze_comment_sentiment(1)
    
    assert result.label == SentimentLabel.POSITIVE
    assert result.Confidence == 0.9


# ============================================================================
# EXCEPTION TESTS - Error handling
# ============================================================================

def test_custom_exceptions_exist():
    """Test that custom exception classes are defined"""
    from src.utils.exceptions import (
        CommentNotFoundError,
        AnalysisFailedError,
        APIQuotaExceededError
    )
    
    # Test exceptions can be instantiated
    exc1 = CommentNotFoundError(1)
    exc2 = AnalysisFailedError(1, Exception("test"))
    exc3 = APIQuotaExceededError()
    
    assert "not found" in str(exc1).lower()
    assert "failed" in str(exc2).lower()
    assert "quota" in str(exc3).lower()