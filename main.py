#must import every class, also include __init__.py files in each folder to make them packages
from src.backend.YoutubeAPIHandler import APIHandler
from src.backend.sentiment_analyzer import SentimentAnalyzer

# Replace with your API key
API_KEY = "***API KEY GOES HERE***"

# replace with youtube video ID
VIDEO_ID = "***YOUTUBE VIDEO ID GOES HERE***"

bert = SentimentAnalyzer()
youtube = APIHandler(API_KEY, VIDEO_ID)
comments = youtube.get_comments()

analysis = {}
for i, comment in enumerate(comments.values()):
    single_analysis = bert.analyze(comment)
    analysis[i] = single_analysis

for key, value in analysis.items():
    print(f"{key}: {value}")

