from enum import Enum
from dataclasses import dataclass


class SentimentLabel (Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


@dataclass (frozen = True) #immutable after creation (read-only)
class Sentiment:
    label: SentimentLabel
    Confidence: float

    def is_positive(self) -> bool:
        return self.label == SentimentLabel.POSITIVE
    
    def is_neutral(self) -> bool:
        return self.label == SentimentLabel.NEUTRAL
    
    def is_confident(self, threshold: float = 0.8) -> bool:
        return self.confidence >= threshold

@dataclass
class Comment:#entity
    videoId: str
    id: int
    author: str
    text: str
    sentiment: Sentiment | None = None

    def analyze_sentiment(self, text, analyzer) -> None:
        """Domain logic: a comment can be analyzed"""
        self.sentiment = analyzer.analyze(self)

