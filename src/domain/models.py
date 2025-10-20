from enum import Enum
from dataclasses import dataclass


class SentimentLabel (Enum):
    POSTIVE = "POSTIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


@dataclass (frozen = True) #immutable after creation (read-only)
class Sentiment:
    label: SentimentLabel
    Confidence: float

    def is_positive(self) -> bool:
        return self.label == SentimentLabel.POSTIVE
    
    def is_neutral(self) -> bool:
        return self.label == SentimentLabel.NEUTRAL
    
    def is_confident(self, threshold: float = 0.8) -> bool:
        return self.confidence >= threshold

@dataclass
class Comment: #entity
    id: int
    author: str
    text: str
    sentiment: Sentiment | None = None

    def analyze_sentiment(self, text, analyzer) -> None:
        """Domain logic: a comment can be analyzed"""
        self.sentiment = analyzer.analyze(self)


@dataclass
class Video: #aggregate root
    id: str
    comments: list[Comment]
    
    def add_comment(self, comment: Comment) -> None:
        self.comments.append(comment)

    def get_sentiment_distribution(self) -> dict[SentimentLabel, int]:
        """Business logic, needs to be moved to service layer later"""
        distribution = {label:0 for label in SentimentLabel}
        for comment in self.comments:
            if comment.sentiment:
                distribution[comment.sentiment.label] += 1
        return distribution