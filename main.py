import os
#supress tensorflow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppresses all TF logging
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Stops the oneDNN messages

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

from src.repositories import InMemoryCommentRepo
from src.backend.analyzers import BertSentimentAnalyzer
from src.backend.api import YoutubeCommentFetcher
from src.services import CommentService

# Replace with your API key
API_KEY = "placeholder"

# replace with youtube video ID
VIDEO_ID = "placeholder"

def main():
    #init backend components
    comment_repo = InMemoryCommentRepo()
    sentiment_analyzer = BertSentimentAnalyzer()
    comment_fetcher = YoutubeCommentFetcher(API_KEY, VIDEO_ID)

    #init services
    comment_service = CommentService(comment_repository = comment_repo
                                     ,sentiment_analyzer = sentiment_analyzer
                                     ,comment_fetcher = comment_fetcher
                                    )

    print("Fetching comments from Youtube...")
    comments = comment_service.fetch_and_store_comments()
    print(f"Fetched {len(comments)} comments\n")

    #analyze all fetched comments
    print("Analyzing sentiment for all comments...")
    results = comment_service.analyze_all_comments()
    print("Analysis complete!\n")

    #Display results
    print("=" * 50)
    print("SENTIMENT ANALYSIS RESULTS")
    print("=" * 50)

    for comment_id, sentiment in results.items():
        comment = comment_service.get_comment(comment_id)
        print(f"\nComment #{comment_id} by {comment.author}:")
        print(f"Text: {comment.text[:100]}...")
        print(f"Sentiment: {sentiment.label.value} (Confidence: {sentiment.Confidence:.2f})")

    #display distribution
    print("\n" + "=" * 50)
    print("SENTIMENT DISTRIBUTION")
    print("=" * 50)
    distribution = comment_service.get_sentiment_distrib()
    for label, count in distribution.items():
        print(f"{label.value}: {count}")
        
if __name__ == "__main__":
    main()