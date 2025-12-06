import pytest
from unittest.mock import Mock, patch
from src.repositories.commentRepository import InMemoryCommentRepo
from src.backend.analyzers.bert_sentiment_analyzer import BertSentimentAnalyzer
from src.backend.api.youtube_comment_fetcher import YoutubeCommentFetcher
from src.services.comment_service import CommentService
from src.domain.models import SentimentLabel


class TestServiceRepositoryIntegration:
    """Integration tests for Service and Repository layers"""
    
    @pytest.fixture
    def repo(self):
        return InMemoryCommentRepo()
    
    @pytest.fixture
    def mock_analyzer(self):
        mock = Mock()
        mock.analyze.return_value = {"label": "POSITIVE", "score": 0.95}
        return mock
    
    @pytest.fixture
    def mock_fetcher(self):
        mock = Mock()
        mock.get_comments.return_value = [
            {"author": "User1", "text": "Great video!", "video_id": "abc123"},
            {"author": "User2", "text": "Not bad", "video_id": "abc123"}
        ]
        return mock
    
    def test_fetch_store_analyze_workflow(self, repo, mock_analyzer, mock_fetcher):
        """Test complete workflow: fetch -> store -> analyze"""
        service = CommentService(repo, mock_analyzer, mock_fetcher)
        
        comments = service.fetch_and_store_comments()
        assert len(comments) == 2
        assert len(repo.get_all()) == 2
        
        service.analyze_all_comments()
        
        distribution = service.get_sentiment_distrib()
        assert distribution[SentimentLabel.POSITIVE] == 2
    
    def test_service_retrieves_stored_comments(self, repo, mock_analyzer, mock_fetcher):
        """Test that service can retrieve comments from repository"""
        service = CommentService(repo, mock_analyzer, mock_fetcher)
        
        service.fetch_and_store_comments()
        
        all_comments = service.get_all_comments()
        assert len(all_comments) == 2
        
        comment = service.get_comment(1)
        assert comment.id == 1
        assert comment.author == "User1"


class TestServiceAnalyzerIntegration:
    """Integration tests for Service and Analyzer layers"""
    
    @pytest.fixture
    def repo(self):
        return InMemoryCommentRepo()
    
    @pytest.fixture
    def mock_fetcher(self):
        mock = Mock()
        mock.get_comments.return_value = [
            {"author": "User1", "text": "Amazing!", "video_id": "abc"},
            {"author": "User2", "text": "Terrible", "video_id": "abc"},
            {"author": "User3", "text": "Okay", "video_id": "abc"}
        ]
        return mock
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_real_analyzer_with_service(self, mock_logger, mock_pipeline, repo, mock_fetcher):
        """Test service with mocked BERT analyzer"""
        mock_pipe = Mock()
        mock_pipe.side_effect = [
            [{"label": "POSITIVE", "score": 0.95}],
            [{"label": "NEGATIVE", "score": 0.88}],
            [{"label": "NEUTRAL", "score": 0.65}]
        ]
        mock_pipeline.return_value = mock_pipe
        
        analyzer = BertSentimentAnalyzer()
        service = CommentService(repo, analyzer, mock_fetcher)
        
        service.fetch_and_store_comments()
        service.analyze_all_comments()
        
        distribution = service.get_sentiment_distrib()
        assert distribution[SentimentLabel.POSITIVE] == 1
        assert distribution[SentimentLabel.NEGATIVE] == 1
        assert distribution[SentimentLabel.NEUTRAL] == 1


class TestEndToEndFlow:
    """Light end-to-end integration tests"""
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    @patch('src.backend.api.youtube_comment_fetcher.build')
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_complete_sentiment_analysis_flow(self, api_logger, mock_build, analyzer_logger, mock_pipeline):
        """Test complete flow from API fetch to sentiment distribution"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "User1",
                                "textDisplay": "Love this!"
                            }
                        }
                    }
                },
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "User2",
                                "textDisplay": "Hate it"
                            }
                        }
                    }
                }
            ]
        }
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_build.return_value = mock_youtube
        
        mock_pipe = Mock()
        mock_pipe.side_effect = [
            [{"label": "POSITIVE", "score": 0.92}],
            [{"label": "NEGATIVE", "score": 0.85}]
        ]
        mock_pipeline.return_value = mock_pipe
        
        repo = InMemoryCommentRepo()
        analyzer = BertSentimentAnalyzer()
        fetcher = YoutubeCommentFetcher("test_key", "test_video")
        service = CommentService(repo, analyzer, fetcher)
        
        comments = service.fetch_and_store_comments()
        assert len(comments) == 2
        
        service.analyze_all_comments()
        
        distribution = service.get_sentiment_distrib()
        assert distribution[SentimentLabel.POSITIVE] == 1
        assert distribution[SentimentLabel.NEGATIVE] == 1
        assert distribution[SentimentLabel.NEUTRAL] == 0
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_empty_comments_flow(self, analyzer_logger, mock_pipeline):
        """Test flow when no comments are fetched"""
        mock_pipeline.return_value = Mock()
        
        repo = InMemoryCommentRepo()
        analyzer = BertSentimentAnalyzer()
        mock_fetcher = Mock()
        mock_fetcher.get_comments.return_value = []
        
        service = CommentService(repo, analyzer, mock_fetcher)
        
        comments = service.fetch_and_store_comments()
        assert len(comments) == 0
        
        results = service.analyze_all_comments()
        assert len(results) == 0
        
        distribution = service.get_sentiment_distrib()
        assert all(count == 0 for count in distribution.values())