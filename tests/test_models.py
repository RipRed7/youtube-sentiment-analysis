import pytest 
from unittest.mock import Mock, patch
from src.database.models import Sentiment, SentimentLabel, Comment

def test_sentiment_label_values():
    """Test that sentiment labels have correct string values"""
    
    assert SentimentLabel.POSITIVE.value == "POSITIVE"
    assert SentimentLabel.NEGATIVE.value == "NEGATIVE"
    assert SentimentLabel.NEUTRAL.value == "NEUTRAL"


def test_comment_stores_basic_info():
    """Test that Comment stores author, text, and video ID"""
    
    comment = Comment(
        videoId="abc123",
        id=1,
        author="TestUser",
        text="Great video!"
    )
    
    assert comment.videoId == "abc123"
    assert comment.author == "TestUser"
    assert comment.text == "Great video!"


def test_sentiment_stores_label_and_confidence():
    """Test that Sentiment stores label and confidence score"""
    
    sentiment = Sentiment(label=SentimentLabel.POSITIVE, Confidence=0.95)
    
    assert sentiment.label == SentimentLabel.POSITIVE
    assert sentiment.Confidence == 0.95