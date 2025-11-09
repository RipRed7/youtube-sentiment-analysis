from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.backend.api.Icomment_fetcher import ICommentFetcher
from src.utils.exceptions import APIConnectionError, APIQuotaExceededError

class APIError(Exception):
    pass

class YoutubeCommentFetcher(ICommentFetcher):
    # Youtube API implementation of comment fetcher
    def __init__(self, API_KEY: str, VIDEO_ID: str) -> None:
        self.VIDEO_ID = VIDEO_ID
        self.youtube = build("youtube", "v3", developerKey=API_KEY)


    def get_comments(self) -> list[dict[str, str]]:
        #fetch comments from youtube API
        try:
            request = self.youtube.commentThreads().list(
                part ="snippet",  # required paramater for api
                videoId = self.VIDEO_ID, 
                maxResults = 50, # max comments
                textFormat = "plainText"
            ) 
            response = request.execute()

        except HttpError as e:
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
