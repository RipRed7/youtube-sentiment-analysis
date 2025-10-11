#must import every class, also include __init__.py files in each folder to make them packages
from src.backend.YoutubeAPIHandler import APIHandler

# Replace with your API key
API_KEY = "***API KEY GOES HERE***"

# replace with youtube video ID
VIDEO_ID = "***YOUTUBE VIDEO ID GOES HERE***"

youtube = APIHandler(API_KEY, VIDEO_ID)
comments = youtube.get_comments()
