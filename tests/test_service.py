import pytest
from unittest.mock import Mock, MagicMock, patch
from src.services.comment_service import CommentService
from src.domain.models import Comment, Sentiment, SentimentLabel
from src.utils.exceptions import CommentNotFoundError, AnalysisFailedError

class TestCommentService:
    #Unit tests for CommentService with mocked dependencies

    @pytest.fixture
    def mock_repo(self):
        return Mock()
    
    @pytest.fixture
    def mock_analyzer(self):
        return Mock()
    
    @pytest.fixture
    def mock_fetcher(self):
        return Mock()
    
    @pytest.fixture
    def service(self, mock_repo, mock_analyzer, mock_fetcher):
        return CommentService(
            comment_repository = mock_repo,
            sentiment_analyzer = mock_analyzer,
            comment_fetcher = mock_fetcher
        )

    @pytest.fixture
    def sample_raw_comments(self):
        return [
            {"author": "User1", "text": "Great video!", "video_id": "abc123"},
            {"author": "User2", "text": "I love this song!", "video_id": "abc123"},
            {"author": "User3", "text": "This was okay...", "video_id": "abc123"},
            {"author": "User4", "text": "Didn't like the thumbnail, not a fan.", "video_id": "abc123"}
        ]

    @pytest.fixture
    def test_service_initialization(self, mock_repo, mock_analyzer, mock_fetcher):
        #test that CommentService initalizes
        service = CommentService(
            comment_repository = mock_repo,
            sentiment_analyzer = mock_analyzer,
            comment_fetcher = mock_fetcher
    )

    assert service.comment_repo == mock_repo 
    assert service.analyzer == mock_analyzer 
    assert service.comment_fetcher == mock_fetcher


    def test_fetch_store_comments_success(self, service, mock_fetcher, mock_repo, sample_raw_comments):
        mock_fetcher.get_comments.return_value = sample_raw_comments
        result = service.fetch_and_store_comments()

        mock_fetcher.get_comments.assert_called_once()
        assert mock_repo.add.call_count == 3
        assert len(result) == 3
        assert all(isinstance(comment, Comment) for comment in result)

    def test_fetch_and_store_comments_empty_list(self, service, mock_fetcher, mock_repo):
        mock_fetcher.get_comments.return_value = []

        result = service.fetch_and_store_comments()

        assert result == []
        mock_repo.add.assert_not_called()

    def test_fetch_and_store_comments_api_error(self, service, mock_fetcher):
        mock_fetcher.get_comments.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            service.fetch_and_store_comments()

        assert "API Error" in str(exc_info.value)

    def test_fetch_and_store_comments_aprtial_failure(self, service, mock_fetcher, mock_repo):
        raw_comments = [
            {"author": "User1", "text": "Good", "video_id": "abc"},
            {"author": "User2", "text": "Bad", "video_id": "abc"}
        ]
        mock_fetcher.get_comments.return_value = raw_comments
        mock_repo.add.side_effect = [None, Exception("Storage error")]

        result = service.fetch_and_store_comments()

        assert len(result) == 1
        assert mock_repo.add.call_count == 2

    def test_analyze_comment_sentiment_success(self, service, mock_repo, mock_analyzer):
        comment = Comment(videoId = "abc", id = 1, author = "User", text = "Great!")
        mock_repo.get_by_id.return_value = comment
        mock_analyzer.analyze.return_value = {"label": "POSITIVE", "score": 0.95}

        result = service.analyze_comment_sentiment(1)

        mock_repo.get_by_id.assert_called_once_with(1)
        mock_analyzer.analyze.assert_called_once_with("Great!")
        mock_repo.update.assert_called_once()
        assert result.label == SentimentLabel.POSITIVE
        assert result.Confidence == 0.95
    
    def test_analyze_comment_sentiment_negative(self, service, mock_repo, mock_analyzer):
        """Test analyzing a negative sentiment comment"""
        comment = Comment(videoId="abc", id=1, author="User", text="Terrible!")
        mock_repo.get_by_id.return_value = comment
        mock_analyzer.analyze.return_value = {"label": "NEGATIVE", "score": 0.92}
        
        result = service.analyze_comment_sentiment(1)
        
        assert result.label == SentimentLabel.NEGATIVE
        assert result.Confidence == 0.92
    
    def test_analyze_comment_sentiment_neutral(self, service, mock_repo, mock_analyzer):
        """Test analyzing a neutral sentiment comment"""
        comment = Comment(videoId="abc", id=1, author="User", text="It's okay")
        mock_repo.get_by_id.return_value = comment
        mock_analyzer.analyze.return_value = {"label": "NEUTRAL", "score": 0.65}
        
        result = service.analyze_comment_sentiment(1)
        
        assert result.label == SentimentLabel.NEUTRAL
        assert result.Confidence == 0.65
    
    def test_analyze_comment_sentiment_comment_not_found(self, service, mock_repo):
        """Test analyzing non-existent comment raises error"""
        mock_repo.get_by_id.return_value = None
        
        with pytest.raises(CommentNotFoundError):
            service.analyze_comment_sentiment(999)
    
    def test_analyze_comment_sentiment_analyzer_error(self, service, mock_repo, mock_analyzer):
        """Test handling analyzer errors"""
        comment = Comment(videoId="abc", id=1, author="User", text="Test")
        mock_repo.get_by_id.return_value = comment
        mock_analyzer.analyze.side_effect = Exception("Model error")
        
        with pytest.raises(AnalysisFailedError):
            service.analyze_comment_sentiment(1)
    
    def test_analyze_comment_sentiment_unknown_label(self, service, mock_repo, mock_analyzer):
        """Test handling unknown sentiment labels defaults to NEUTRAL"""
        comment = Comment(videoId="abc", id=1, author="User", text="Test")
        mock_repo.get_by_id.return_value = comment
        mock_analyzer.analyze.return_value = {"label": "UNKNOWN", "score": 0.5}
        
        result = service.analyze_comment_sentiment(1)
        
        assert result.label == SentimentLabel.NEUTRAL
    
    def test_analyze_all_comments_success(self, service, mock_repo, mock_analyzer):
        """Test analyzing all comments successfully"""
        comments = [
            Comment(videoId="abc", id=1, author="U1", text="Good"),
            Comment(videoId="abc", id=2, author="U2", text="Bad"),
            Comment(videoId="abc", id=3, author="U3", text="Okay")
        ]
        mock_repo.get_all.return_value = comments
        mock_repo.get_by_id.side_effect = comments
        mock_analyzer.analyze.side_effect = [
            {"label": "POSITIVE", "score": 0.9},
            {"label": "NEGATIVE", "score": 0.85},
            {"label": "NEUTRAL", "score": 0.6}
        ]
        
        results = service.analyze_all_comments()
        
        assert len(results) == 3
        assert results[1].label == SentimentLabel.POSITIVE
        assert results[2].label == SentimentLabel.NEGATIVE
        assert results[3].label == SentimentLabel.NEUTRAL
    
    def test_analyze_all_comments_empty_repo(self, service, mock_repo):
        """Test analyzing when no comments exist"""
        mock_repo.get_all.return_value = []
        
        results = service.analyze_all_comments()
        
        assert results == {}
    
    def test_analyze_all_comments_with_failures(self, service, mock_repo, mock_analyzer):
        """Test that analyze_all continues on individual failures"""
        comments = [
            Comment(videoId="abc", id=1, author="U1", text="Good"),
            Comment(videoId="abc", id=2, author="U2", text="Bad")
        ]
        mock_repo.get_all.return_value = comments
        mock_repo.get_by_id.side_effect = [comments[0], comments[1]]
        mock_analyzer.analyze.side_effect = [
            {"label": "POSITIVE", "score": 0.9},
            Exception("Analysis failed")
        ]
        
        results = service.analyze_all_comments()
        
        assert len(results) == 1
        assert 1 in results
        assert 2 not in results
    
    def test_get_sentiment_distrib_all_sentiments(self, service, mock_repo):
        """Test sentiment distribution with all sentiment types"""
        comments = [
            Comment(videoId="abc", id=1, author="U1", text="Good",
                   sentiment=Sentiment(SentimentLabel.POSITIVE, 0.9)),
            Comment(videoId="abc", id=2, author="U2", text="Good2",
                   sentiment=Sentiment(SentimentLabel.POSITIVE, 0.85)),
            Comment(videoId="abc", id=3, author="U3", text="Bad",
                   sentiment=Sentiment(SentimentLabel.NEGATIVE, 0.8)),
            Comment(videoId="abc", id=4, author="U4", text="Okay",
                   sentiment=Sentiment(SentimentLabel.NEUTRAL, 0.6))
        ]
        mock_repo.get_all.return_value = comments
        
        distribution = service.get_sentiment_distrib()
        
        assert distribution[SentimentLabel.POSITIVE] == 2
        assert distribution[SentimentLabel.NEGATIVE] == 1
        assert distribution[SentimentLabel.NEUTRAL] == 1
    
    def test_get_sentiment_distrib_no_sentiment(self, service, mock_repo):
        """Test distribution with comments without sentiment"""
        comments = [
            Comment(videoId="abc", id=1, author="U1", text="Good"),
            Comment(videoId="abc", id=2, author="U2", text="Bad")
        ]
        mock_repo.get_all.return_value = comments
        
        distribution = service.get_sentiment_distrib()
        
        assert distribution[SentimentLabel.POSITIVE] == 0
        assert distribution[SentimentLabel.NEGATIVE] == 0
        assert distribution[SentimentLabel.NEUTRAL] == 0
    
    def test_get_sentiment_distrib_empty_repo(self, service, mock_repo):
        """Test distribution with no comments"""
        mock_repo.get_all.return_value = []
        
        distribution = service.get_sentiment_distrib()
        
        assert all(count == 0 for count in distribution.values())
    
    def test_get_comment_success(self, service, mock_repo):
        """Test retrieving a comment by ID"""
        comment = Comment(videoId="abc", id=1, author="User", text="Test")
        mock_repo.get_by_id.return_value = comment
        
        result = service.get_comment(1)
        
        mock_repo.get_by_id.assert_called_once_with(1)
        assert result == comment
    
    def test_get_comment_not_found(self, service, mock_repo):
        """Test retrieving non-existent comment raises error"""
        mock_repo.get_by_id.return_value = None
        
        with pytest.raises(CommentNotFoundError):
            service.get_comment(999)
    
    def test_get_all_comments_success(self, service, mock_repo):
        """Test retrieving all comments"""
        comments = [
            Comment(videoId="abc", id=1, author="U1", text="T1"),
            Comment(videoId="abc", id=2, author="U2", text="T2")
        ]
        mock_repo.get_all.return_value = comments
        
        result = service.get_all_comments()
        
        mock_repo.get_all.assert_called_once()
        assert result == comments
        assert len(result) == 2
    
    def test_get_all_comments_empty(self, service, mock_repo):
        """Test retrieving from empty repository"""
        mock_repo.get_all.return_value = []
        
        result = service.get_all_comments()
        
        assert result == []
