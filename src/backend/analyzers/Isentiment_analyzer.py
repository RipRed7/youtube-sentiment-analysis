from abc import ABC, abstractmethod

class ISentimentAnalyzer(ABC):
    #interface for sentiment analysis
    @abstractmethod
    def analyze(self, text: str) -> dict:
        #analyze comment and return result in a dict
        pass


