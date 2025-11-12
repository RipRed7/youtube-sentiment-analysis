from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.backend.api.Icomment_fetcher import ICommentFetcher
from src.utils.exceptions import APIConnectionError, APIQuotaExceededError, CommentsDisabledError, VideoNotFoundError
from src.utils.logger import get_logger

class APIError(Exception):
    pass

class YoutubeCommentFetcher(ICommentFetcher):
    # Youtube API implementation of comment fetcher
    def __init__(self, API_KEY: str, VIDEO_ID: str) -> None:
        self.VIDEO_ID = VIDEO_ID
        self.youtube = build("youtube", "v3", developerKey=API_KEY)
        self.logger = get_logger()
        self.logger.info(f"Initialized YoutubeCommentFetcher for video: {VIDEO_ID}")


    def get_comments(self) -> list[dict[str, str]]:
        self.logger.debug(f"Starting comment fetch for video: {self.VIDEO_ID}")

        #fetch comments from youtube API
        try:
            request = self.youtube.commentThreads().list(
                part ="snippet",  # required paramater for api
                videoId = self.VIDEO_ID, 
                maxResults = 1000, # max comments
                textFormat = "plainText"
            ) 
            response = request.execute()
            self.logger.debug(f"API request successful for video: {self.VIDEO_ID}")
    
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            status_code = e.resp.status if hasattr(e, 'resp') else None
            self.logger.error(f"HttpError fetching comments for video {self.VIDEO_ID}: status = {status_code}, details = {error_details}")

            if status_code == 403:
                if "quotaExceeded" in str(error_details):
                    self.logger.critical("Youtube API quota exceeded")
                    raise APIQuotaExceededError()
                elif "commentsDisabled" in str(error_details):
                    self.logger.warning(f"Comments are disabled for video: {self.VIDEO_ID}")
                    raise CommentsDisabledError(self.VIDEO_ID)
                
            if status_code == 404:
                self.logger.warning(f"Video not found: {self.VIDEO_ID}")
                raise VideoNotFoundError(self.VIDEO_ID)
            raise APIConnectionError()
        except Exception as e:
            raise APIQuotaExceededError(f"Failed to fetch comments: {e}")
        
        comments = []
        
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": comment["authorDisplayName"]
                ,"text": comment["textDisplay"]
                ,"video_id": self.VIDEO_ID
                })
        return comments
