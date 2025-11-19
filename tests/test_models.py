import pytest 
from src.domain.models import SentimentLabel, Sentiment, Comment


class TestSentimentLabel:

    #test if sentiment labels exist
    def test_labels_exist(self):
        assert SentimentLabel.POSITIVE.value == "POSITIVE"
        assert SentimentLabel.NEGATIVE.value == "NEGATIVE"
        assert SentimentLabel.NEUTRAL.value == "NEUTRAL"

    #test to ensure that exactly 3 sentiment labels exist
    def test_label_count(self):
        assert len(SentimentLabel) == 3


class TestSentiment:
    
    def test_sentiment_creation(self):
        sentiment = Sentiment(label = SentimentLabel.POSITIVE, confidence = 0.95)
        assert sentiment.label == SentimentLabel.POSITIVE
        assert sentiment.confidence == 0.95

    def test_sentiment_immutability(self):
        sentiment = Sentiment(label = SentimentLabel.POSITIVE, confidence = 0.95)

        with pytest.raises(AttributeError):
            sentiment.label = SentimentLabel.NEGATIVE

    def test_sentiment_conf_lowercase(self):
        sentiment = Sentiment(label = SentimentLabel.POSITIVE, confidence = 0.95)

        assert hasattr(sentiment, 'confidence')
        assert sentiment.confidence == 0.95

class TestComment:

    def test_comment_creation_no_sentiment(self):
        comment = Comment(
            videoId = "dQw4w9Wsj01",
            id = 1,
            author = "user1",
            text = "loved the video!" 
        )

        assert comment.videoId == "dQw4w9Wsj01"
        assert comment.id == 1
        assert comment.author == "user1"
        assert comment.text == "loved the video!"
        assert comment.sentiment is None

    def test_comment_creation_with_sentiment(self):
        sentiment = Sentiment(label = SentimentLabel.POSITIVE, confidence = 0.95)
        comment = Comment(
            videoId = "dQw4w9Wsj01",
            id = 1,
            author = "user1",
            text = "loved the video!",
            sentiment = sentiment
        )

        assert comment.sentiment == sentiment