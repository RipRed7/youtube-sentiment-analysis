from transformers import pipeline
from src.backend.analyzers.Isentiment_analyzer import ISentimentAnalyzer
from src.utils.logger import get_logger
from src.utils.exceptions import ModelLoadError, AnalysisFailedError
from typing import List, Dict

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
            result = self.sentiment_analyzer(text, truncation=True, max_length=128)[0]
            
            # Map RoBERTa labels to human-readable labels
            label_mapping = {
                'LABEL_0': 'NEGATIVE',
                'LABEL_1': 'NEUTRAL',
                'LABEL_2': 'POSITIVE'
            }
            
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
        

    def analyze_comments_batch(self, texts: List[str], batch_size: int = 32) -> List[Dict]:
            """
            Analyze multiple comments in batches for better performance
            
            Args:
                texts: List of text strings to analyze
                batch_size: Number of texts to process at once (default: 32)
                
            Returns:
                List of dicts with 'label' and 'score' keys
            """
            if not texts:
                self.logger.warning("Empty text list provided for batch analysis")
                return []
            
            self.logger.info(f"Starting batch analysis of {len(texts)} texts with batch_size={batch_size}")
            
            # Filter out empty texts and keep track of original indices
            valid_texts = []
            valid_indices = []
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            # Initialize results with neutral for all texts
            results = [{"label": "NEUTRAL", "score": 0.0} for _ in range(len(texts))]
            
            if not valid_texts:
                self.logger.warning("No valid texts to analyze after filtering")
                return results
            
            try:
                # Use the pipeline's batch processing capability with truncation
                batch_results = self.sentiment_analyzer(
                    valid_texts, 
                    batch_size=batch_size,
                    truncation=True,
                    max_length=128
                )
                
                # Map RoBERTa labels to human-readable labels
                label_mapping = {
                    'LABEL_0': 'NEGATIVE',
                    'LABEL_1': 'NEUTRAL',
                    'LABEL_2': 'POSITIVE'
                }
                
                # Map results back to original indices
                for idx, result in zip(valid_indices, batch_results):
                    raw_label = result['label']
                    mapped_label = label_mapping.get(raw_label, 'NEUTRAL')
                    results[idx] = {
                        'label': mapped_label,
                        'score': result['score']
                    }
                
                self.logger.info(f"Batch analysis complete: {len(valid_texts)} texts analyzed")
                return results
                
            except Exception as e:
                self.logger.exception(f"Batch sentiment analysis failed")
                raise AnalysisFailedError(comment_id=0, original_error=e)