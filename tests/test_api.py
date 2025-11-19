import pytest
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError
from src.backend.api.youtube_comment_fetcher import YoutubeCommentFetcher
from src.utils.exceptions import (
    APIQuotaExceededError,
    APIConnectionError,
    VideoNotFoundError,
    CommentsDisabledError
)


class TestYoutubeCommentFetcher:
    """Unit tests for YoutubeCommentFetcher with mocked YouTube API"""
    
    @pytest.fixture
    def mock_youtube_build(self):
        """Fixture providing mocked YouTube API client"""
        with patch('src.backend.api.youtube_comment_fetcher.build') as mock_build:
            yield mock_build
    
    @pytest.fixture
    def sample_api_response(self):
        """Fixture providing sample YouTube API response"""
        return {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "User1",
                                "textDisplay": "Great video!"
                            }
                        }
                    }
                },
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "User2",
                                "textDisplay": "Not bad"
                            }
                        }
                    }
                },
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "User3",
                                "textDisplay": "Terrible content"
                            }
                        }
                    }
                }
            ]
        }
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_fetcher_initialization(self, mock_logger, mock_youtube_build):
        """Test that fetcher initializes correctly"""
        mock_youtube = Mock()
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("test_api_key", "test_video_id")
        
        assert fetcher.VIDEO_ID == "test_video_id"
        assert fetcher.youtube == mock_youtube
        mock_youtube_build.assert_called_once_with("youtube", "v3", developerKey="test_api_key")
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_success(self, mock_logger, mock_youtube_build, sample_api_response):
        """Test successful comment fetching"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = sample_api_response
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        comments = fetcher.get_comments()
        
        assert len(comments) == 3
        assert comments[0]["author"] == "User1"
        assert comments[0]["text"] == "Great video!"
        assert comments[0]["video_id"] == "video_id"
        assert comments[1]["author"] == "User2"
        assert comments[2]["author"] == "User3"
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_empty_response(self, mock_logger, mock_youtube_build):
        """Test fetching when video has no comments"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"items": []}
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        comments = fetcher.get_comments()
        
        assert comments == []
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_api_call_parameters(self, mock_logger, mock_youtube_build):
        """Test that API is called with correct parameters"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {"items": []}
        mock_comment_threads = Mock()
        mock_comment_threads.list.return_value = mock_request
        mock_youtube.commentThreads.return_value = mock_comment_threads
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "test_video_123")
        fetcher.get_comments()
        
        mock_comment_threads.list.assert_called_once_with(
            part="snippet",
            videoId="test_video_123",
            maxResults=1000,
            textFormat="plainText"
        )
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_quota_exceeded_error(self, mock_logger, mock_youtube_build):
        """Test handling of quota exceeded error (403)"""
        mock_youtube = Mock()
        mock_request = Mock()
        
        # Create HttpError with quota exceeded
        http_error = HttpError(
            resp=Mock(status=403),
            content=b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}'
        )
        http_error.error_details = [{"reason": "quotaExceeded"}]
        mock_request.execute.side_effect = http_error
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        
        with pytest.raises(APIQuotaExceededError):
            fetcher.get_comments()
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_disabled_error(self, mock_logger, mock_youtube_build):
        """Test handling of comments disabled error (403)"""
        mock_youtube = Mock()
        mock_request = Mock()
        
        # Create HttpError with comments disabled
        http_error = HttpError(
            resp=Mock(status=403),
            content=b'{"error": {"errors": [{"reason": "commentsDisabled"}]}}'
        )
        http_error.error_details = [{"reason": "commentsDisabled"}]
        mock_request.execute.side_effect = http_error
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        
        with pytest.raises(CommentsDisabledError) as exc_info:
            fetcher.get_comments()
        
        assert exc_info.value.details["video_id"] == "video_id"
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_video_not_found_error(self, mock_logger, mock_youtube_build):
        """Test handling of video not found error (404)"""
        mock_youtube = Mock()
        mock_request = Mock()
        
        # Create HttpError with 404 status
        http_error = HttpError(
            resp=Mock(status=404),
            content=b'{"error": {"message": "Video not found"}}'
        )
        mock_request.execute.side_effect = http_error
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        
        with pytest.raises(VideoNotFoundError) as exc_info:
            fetcher.get_comments()
        
        assert exc_info.value.details["video_id"] == "video_id"
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_generic_http_error(self, mock_logger, mock_youtube_build):
        """Test handling of generic HTTP errors"""
        mock_youtube = Mock()
        mock_request = Mock()
        
        # Create generic HttpError (500)
        http_error = HttpError(
            resp=Mock(status=500),
            content=b'{"error": {"message": "Internal server error"}}'
        )
        mock_request.execute.side_effect = http_error
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        
        with pytest.raises(APIConnectionError):
            fetcher.get_comments()
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_network_error(self, mock_logger, mock_youtube_build):
        """Test handling of network/connection errors"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.side_effect = Exception("Network error")
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        
        with pytest.raises(APIQuotaExceededError):
            fetcher.get_comments()
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_single_comment(self, mock_logger, mock_youtube_build):
        """Test fetching a single comment"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "SingleUser",
                                "textDisplay": "Only comment"
                            }
                        }
                    }
                }
            ]
        }
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        comments = fetcher.get_comments()
        
        assert len(comments) == 1
        assert comments[0]["author"] == "SingleUser"
        assert comments[0]["text"] == "Only comment"
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_special_characters(self, mock_logger, mock_youtube_build):
        """Test handling comments with special characters"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "User™",
                                "textDisplay": "Great! 😊 @mention #hashtag"
                            }
                        }
                    }
                }
            ]
        }
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        comments = fetcher.get_comments()
        
        assert comments[0]["author"] == "User™"
        assert comments[0]["text"] == "Great! 😊 @mention #hashtag"
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_long_text(self, mock_logger, mock_youtube_build):
        """Test handling very long comments"""
        long_text = "This is a very long comment. " * 100
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "VerboseUser",
                                "textDisplay": long_text
                            }
                        }
                    }
                }
            ]
        }
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        comments = fetcher.get_comments()
        
        assert len(comments) == 1
        assert comments[0]["text"] == long_text
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_preserves_video_id(self, mock_logger, mock_youtube_build, sample_api_response):
        """Test that video_id is correctly added to all comments"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = sample_api_response
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        test_video_id = "abc123xyz"
        fetcher = YoutubeCommentFetcher("api_key", test_video_id)
        comments = fetcher.get_comments()
        
        assert all(comment["video_id"] == test_video_id for comment in comments)
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_returns_list(self, mock_logger, mock_youtube_build, sample_api_response):
        """Test that get_comments always returns a list"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = sample_api_response
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        comments = fetcher.get_comments()
        
        assert isinstance(comments, list)
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_get_comments_dict_structure(self, mock_logger, mock_youtube_build, sample_api_response):
        """Test that each comment has correct dict structure"""
        mock_youtube = Mock()
        mock_request = Mock()
        mock_request.execute.return_value = sample_api_response
        mock_youtube.commentThreads().list.return_value = mock_request
        mock_youtube_build.return_value = mock_youtube
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        comments = fetcher.get_comments()
        
        for comment in comments:
            assert isinstance(comment, dict)
            assert "author" in comment
            assert "text" in comment
            assert "video_id" in comment
            assert isinstance(comment["author"], str)
            assert isinstance(comment["text"], str)
            assert isinstance(comment["video_id"], str)
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_multiple_fetchers_independent(self, mock_logger, mock_youtube_build):
        """Test that multiple fetcher instances are independent"""
        mock_youtube1 = Mock()
        mock_youtube2 = Mock()
        mock_youtube_build.side_effect = [mock_youtube1, mock_youtube2]
        
        fetcher1 = YoutubeCommentFetcher("api_key_1", "video_id_1")
        fetcher2 = YoutubeCommentFetcher("api_key_2", "video_id_2")
        
        assert fetcher1.VIDEO_ID == "video_id_1"
        assert fetcher2.VIDEO_ID == "video_id_2"
        assert fetcher1.youtube is not fetcher2.youtube
    
    @patch('src.backend.api.youtube_comment_fetcher.get_logger')
    def test_logger_initialized(self, mock_logger, mock_youtube_build):
        """Test that logger is properly initialized"""
        mock_youtube_build.return_value = Mock()
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance
        
        fetcher = YoutubeCommentFetcher("api_key", "video_id")
        
        assert fetcher.logger is not None
        mock_logger.assert_called()