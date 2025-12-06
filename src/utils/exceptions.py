#root exception / base exception for all errors
class SentimentAnalyzerError(Exception):
    def __init__(self, message: str, details: dict = None): 
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message
    
#base class for API errors
class APIError(SentimentAnalyzerError):
    pass

class APIQuotaExceededError(APIError):
    def __init__(self, quota_limit: int = 10000):
        super().__init__( 
            message = "Youtube API quota exceeded for today",
            details = {
                "quota_limit": quota_limit,
                "suggestion": "Try again tomorrow or use a different API key..."
            }
        )

class APIConnectionError(APIError):
    def __init__(self, original_error: Exception = None):
        super().__init__(
            message = "Failed to connect to Youtube API",
            details = {"original_error": str(original_error) if original_error else "Unknown error",
            "suggestion": "Check your internet connection and API credentials"
            }
        )

class VideoNotFoundError(APIError):
    def __init__(self, video_id: str):
        super().__init__(
            message = "Video not found or is private",
            details = {
                "video_id": video_id,
                "suggestion": "Try a different youtube video URL"
            }
        )

class CommentsDisabledError(APIError):
    def __init__(self, video_id: str):
        super().__init__(
            message = "Comments are disabled for this video",
            details = {"video_id": video_id
            }
        )

class AnalysisError(SentimentAnalyzerError):
    pass

class ModelLoadError(AnalysisError):
    def __init__(self, model_name: str, original_error: Exception):
        super().__init__(
            message = f"Failed to load sentiment analysis model",
            details = {
                "model": model_name,
                "error": str(original_error)
            }
        )

class AnalysisFailedError(AnalysisError):
    def __init__(self, comment_id: int, original_error: Exception):
        super().__init__(
            message = "Sentiment analysis failed for comment",
            details = {
                "comment_id": comment_id,
                "error": str(original_error)
            }
        )

class RepositoryError(SentimentAnalyzerError):
    pass

class CommentNotFoundError(RepositoryError):
    def __init__(self, comment_id: int):
        super().__init__(
            message = f"Comment not found in repository",
            details = {"comment_id": comment_id}
        )

class ValidationError(SentimentAnalyzerError):
    pass
        
class InvalidURLError(ValidationError):
    def __init__(self, url: str):
        super().__init__(
            message = "Invalid url",
            details = {
                "input_url" : url,
                "valid_formats": [
                    "https://www.youtube.com/watch?v=VIDEO_ID",
                    "https://youtu.be/VIDEO_ID"
                ]
            }
        )