import torch
from transformers import pipeline
from src.backend.analyzers.Isentiment_analyzer import ISentimentAnalyzer
from src.utils.logger import get_logger
from src.utils.exceptions import ModelLoadError, AnalysisFailedError

class BertSentimentAnalyzer(ISentimentAnalyzer):
    #bert sentiment analyzer
    _pipeline = None # Class-level attribute for the pipeline
    _logger = None # Class-level attribute for the logger

    def __init__(self):
        if BertSentimentAnalyzer._logger is None:
            BertSentimentAnalyzer._logger = get_logger()

        self.logger = BertSentimentAnalyzer._logger

        if BertSentimentAnalyzer._pipeline is None: # check if pipeline exists, if created already, reuse instead of reloading
            self.load_model()
        else:
            self.logger.debug("Reusing existing BERT model pipeline")

        self.sentiment_analyzer = BertSentimentAnalyzer._pipeline # Instance level attribute pointing to shared class-level attribute

    def load_model(self) -> None:
        # Load the RoBERTa model pipeline
        model_name = 'cardiffnlp/twitter-roberta-base-sentiment'

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
            raise ModelLoadError(model_name, e)

    def analyze(self, text: str) -> dict:
        #analyze comment and return result in a dict
        if not text or not text.strip():
            self.logger.warning("Attempted to analyze empty text")
            return {"label": "NEUTRAL", "score": 0.0}
        
        try:
            self.logger.debug(f"Analyzing text: {text[:50]}...")
            result = self.sentiment_analyzer(text)[0]
            
            # Map RoBERTa labels to human-readable labels
            # cardiffnlp/twitter-roberta-base-sentiment returns:
            # LABEL_0 = Negative
            # LABEL_1 = Neutral
            # LABEL_2 = Positive
            label_mapping = {
                'LABEL_0': 'NEGATIVE',
                'LABEL_1': 'NEUTRAL',
                'LABEL_2': 'POSITIVE'
            }
            
            # Get the raw label and map it
            raw_label = result['label']
            mapped_label = label_mapping.get(raw_label, 'NEUTRAL')
            
            mapped_result = {
                'label': mapped_label,
                'score': result['score']
            }
            
            self.logger.debug(f"Analysis result: {mapped_label} (confidence: {result['score']:.3f})")
            return mapped_result

        except Exception as e:
            self.logger.exception(f"Sentiment analysis failed for text: {text[:100]}")
            raise AnalysisFailedError(comment_id=0, original_error=e)
        

    def analyze_comments_batch(self, comments: list[dict], batch_size: int = 64) -> list[dict]:
        """
        Batch analyze a list of comments.

        Args:
            comments: list of dicts with 'text' key
            batch_size: number of comments to process at once

        Returns:
            list of dicts with 'label' and 'score' for each comment
        """
        results = []

        # Extract only the text
        texts = [c["text"] for c in comments]

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]

            # Hugging Face expects a list of strings
            batch_results = self.sentiment_analyzer(batch_texts)

            label_mapping = {'LABEL_0': 'NEGATIVE', 'LABEL_1': 'NEUTRAL', 'LABEL_2': 'POSITIVE'}
            for r in batch_results:
                raw_label = r['label']
                mapped_label = label_mapping.get(raw_label, 'NEUTRAL')
                results.append({'label': mapped_label, 'score': r['score']})

        return results
