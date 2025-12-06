import pytest
from unittest.mock import Mock, patch
from src.backend.api.youtube_comment_fetcher import YoutubeCommentFetcher


@patch('src.backend.api.youtube_comment_fetcher.build')
@patch('src.backend.api.youtube_comment_fetcher.get_logger')
def test_fetcher_returns_list_of_dicts(mock_logger, mock_build):
    """Test that fetcher returns list of comment dictionaries"""
    
    # Mock YouTube API response
    mock_youtube = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = {
        "items": [
            {
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "authorDisplayName": "User1",
                            "textDisplay": "Great!"
                        }
                    }
                }
            }
        ]
    }
    mock_youtube.commentThreads().list.return_value = mock_request
    mock_build.return_value = mock_youtube
    
    fetcher = YoutubeCommentFetcher("fake_token", "video123")
    comments = fetcher.get_comments()
    
    assert isinstance(comments, list)
    assert len(comments) == 1
    assert "author" in comments[0]
    assert "text" in comments[0]


@patch('src.backend.api.youtube_comment_fetcher.build')
@patch('src.backend.api.youtube_comment_fetcher.get_logger')
def test_fetcher_includes_video_id_in_comments(mock_logger, mock_build):
    """Test that fetcher adds video_id to each comment"""
    
    mock_youtube = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = {
        "items": [
            {
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "authorDisplayName": "User1",
                            "textDisplay": "Great!"
                        }
                    }
                }
            }
        ]
    }
    mock_youtube.commentThreads().list.return_value = mock_request
    mock_build.return_value = mock_youtube
    
    fetcher = YoutubeCommentFetcher("fake_token", "test_video_123")
    comments = fetcher.get_comments()
    
    assert comments[0]["video_id"] == "test_video_123"
