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