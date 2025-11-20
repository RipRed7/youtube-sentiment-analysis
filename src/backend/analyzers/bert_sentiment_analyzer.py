import torch
from transformers import pipeline
from src.backend.analyzers.Isentiment_analyzer import ISentimentAnalyzer
from src.utils.logger import get_logger
from src.utils.exceptions import ModelLoadError, AnalysisFailedError

class BertSentimentAnalyzer(ISentimentAnalyzer):
    #bert sentiment analyzer
    _pipeline = None # Class-level attribute for the pipeline
    _logger = None # Class-level attribute for the logger

    def __init__(self, batch ):
        if BertSentimentAnalyzer._logger is None:
            BertSentimentAnalyzer._logger = get_logger()

        self.logger = BertSentimentAnalyzer._logger

        if BertSentimentAnalyzer._pipeline is None: # check if pipeline exists, if created already, reuse instead of reloading
            BertSentimentAnalyzer._pipeline = pipeline('sentiment-analysis', model='mervp/SentimentBERT') #load model
        else:
            self.logger.debug("Reusing existing BERT model pipeline")

        self.sentiment_analyzer = BertSentimentAnalyzer._pipeline # Instance level attribute pointing to shared class-level attribute

    def load_model(self) -> None:
        # Load the BERT model pipeline
            # Smaller and faster version of the BERT model
        model_name = 'mervp/SentimentBERT'

        try:
            self.logger.info(f"Loading BERT model: {model_name}")
            self.logger.info("This may take a few seconds on first load...")

            BertSentimentAnalyzer._pipeline = pipeline(
                'sentiment-analysis', 
                model=model_name
            )

            self.logger.info(f"Successfully loaded BERT model: {model_name}")

        except Exception as e:
            self.logger.exception(f"Failed to load BERT model: {model_name}")
            raise ModelLoadError(model_name) from e

    def analyze(self, text: str) -> dict:
        #analyze comment and return result in a dict
        if not text or not text.strip():
            self.logger.warning("Attempted to analyze empty text")
            return {"label": "NEUTRAL", "score": 0.0}
        
        try:
            self.logger.debug(f"Analyzing text: {text[: 50]}...")
            result = self.sentiment_analyzer(text)[0]
            self.logger.debug(f"Analysis result: {result['label']} (confidence: {result['score']:.3f})")
            return result

        except Exception as e:
            self.logger.exception(f"Sentiment analysis failed for text: {text[:100]}")
            raise AnalysisFailedError(comment_id = 0, original_error = e)