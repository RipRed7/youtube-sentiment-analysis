import os
#supress tensorflow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppresses all TF logging
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Stops the oneDNN messages

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

from src.backend.YoutubeAPIHandler import APIHandler
from src.backend.sentiment_analyzer import SentimentAnalyzer



# Replace with your API key
API_KEY = "placeholder"

# replace with youtube video ID
VIDEO_ID = "placeholder"

bert = SentimentAnalyzer()
youtube = APIHandler(API_KEY, VIDEO_ID)
comments = youtube.get_comments()

analysis = {}
for i, comment in enumerate(comments.values()):
    temp_analysis = bert.analyze(comment)
    analysis[i] = temp_analysis

#print comment id and analysis prediction
for key, value in analysis.items():
    print(f"{key}: {value}")

