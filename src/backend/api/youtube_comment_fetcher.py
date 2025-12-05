from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from src.backend.api.Icomment_fetcher import ICommentFetcher
from src.utils.exceptions import APIConnectionError, APIQuotaExceededError, CommentsDisabledError, VideoNotFoundError
from src.utils.logger import get_logger
from src.config.constants import YOUTUBE_API_MAX_RESULTS

class APIError(Exception):
    pass

class YoutubeCommentFetcher(ICommentFetcher):
    """
    YouTube API implementation of comment fetcher
    Uses OAuth access token for authentication
    """
    def __init__(self, access_token: str, VIDEO_ID: str) -> None:
        self.VIDEO_ID = VIDEO_ID
        self.logger = get_logger()
        self.logger.info(f"Initialized YoutubeCommentFetcher for video: {VIDEO_ID}")
        
        # Create credentials from access token
        credentials = Credentials(token=access_token)
        
        # Build YouTube API engine with OAuth credentials
        self.youtube = build("youtube", "v3", credentials=credentials)

    def get_comments(self) -> list[dict[str, str]]:
        self.logger.debug(f"Starting comment fetch for video: {self.VIDEO_ID}")

        comments = []
        next_page_token = None  # start with no page token

        try:
            while True:
                request = self.youtube.commentThreads().list(
                    part="snippet",  # required parameter for api
                    videoId=self.VIDEO_ID,
                    maxResults=YOUTUBE_API_MAX_RESULTS,
                    textFormat="plainText",
                    pageToken=next_page_token  # handle pagination
                )
                response = request.execute()
                self.logger.debug(f"API request successful for video: {self.VIDEO_ID}, fetched {len(response.get('items', []))} comments")
            
                for item in response.get("items", []):
                    comment = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "author": comment["authorDisplayName"],
                        "text": comment["textDisplay"],
                        "video_id": self.VIDEO_ID
                    })

                # Check if there is another page
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break  # exit loop if no more pages

        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            status_code = e.resp.status if hasattr(e, 'resp') else None
            self.logger.error(f"HttpError fetching comments for video {self.VIDEO_ID}: status = {status_code}, details = {error_details}")

            if status_code == 403:
                if "quotaExceeded" in str(error_details): # if youtube api qouta has been exceded
                    self.logger.critical("Youtube API quota exceeded")
                    raise APIQuotaExceededError()
                elif "commentsDisabled" in str(error_details): # if comments are disabled
                    self.logger.warning(f"Comments are disabled for video: {self.VIDEO_ID}")
                    raise CommentsDisabledError(self.VIDEO_ID)
            
            if status_code == 404:
                self.logger.warning(f"Video not found: {self.VIDEO_ID}")
                raise VideoNotFoundError(self.VIDEO_ID)
        
            self.logger.error(f"Unexpected HTTP error: {e}")
            raise APIConnectionError(e)
        
        except Exception as e:
            self.logger.exception(f"Unexpected error fetching comments: {e}")
            raise APIConnectionError(e)
    
        self.logger.info(f"Successfully fetched {len(comments)} comments")
        return comments
