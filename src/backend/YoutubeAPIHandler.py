from googleapiclient.discovery import build

class APIHandler:
    # Initialize the YouTube service
    def __init__(self, API_KEY, VIDEO_ID) -> None:
        self.VIDEO_ID = VIDEO_ID
        self.youtube = build("youtube", "v3", developerKey=API_KEY)

    # fetch comments
    def get_comments(self) -> dict:
        request = self.youtube.commentThreads().list(
        part ="snippet",  # required paramater for api
        videoId = self.VIDEO_ID, 
        maxResults = 50, # max comments
        textFormat = "plainText"   
)
        response = request.execute()
        
        comments = {} 
        
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]
            author = comment["authorDisplayName"]
            text = comment["textDisplay"]
            comments[author] = text
        return comments
