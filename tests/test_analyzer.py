import pytest
from unittest.mock import Mock, patch, MagicMock
from src.backend.analyzers.bert_sentiment_analyzer import BertSentimentAnalyzer
from src.utils.exceptions import ModelLoadError, AnalysisFailedError


class TestBertSentimentAnalyzer:
    """Unit tests for BertSentimentAnalyzer with mocked BERT pipeline"""
    
    @pytest.fixture(autouse=True)
    def reset_class_attributes(self):
        """Reset class-level attributes before each test"""
        BertSentimentAnalyzer._pipeline = None
        BertSentimentAnalyzer._logger = None
        yield
        BertSentimentAnalyzer._pipeline = None
        BertSentimentAnalyzer._logger = None
    
    @pytest.fixture
    def mock_pipeline(self):
        """Fixture providing a mocked BERT pipeline"""
        mock = Mock()
        mock.return_value = [{"label": "POSITIVE", "score": 0.95}]
        return mock
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyzer_initialization_loads_model(self, mock_logger, mock_pipeline_func):
        """Test that analyzer loads BERT model on first initialization"""
        mock_pipeline_func.return_value = Mock()
        
        analyzer = BertSentimentAnalyzer()
        
        mock_pipeline_func.assert_called_once_with(
            'sentiment-analysis',
            model='distilbert-base-uncased-finetuned-sst-2-english'
        )
        assert BertSentimentAnalyzer._pipeline is not None
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyzer_reuses_existing_pipeline(self, mock_logger, mock_pipeline_func):
        """Test that subsequent analyzers reuse existing pipeline"""
        mock_pipeline_func.return_value = Mock()
        
        analyzer1 = BertSentimentAnalyzer()
        analyzer2 = BertSentimentAnalyzer()
        
        mock_pipeline_func.assert_called_once()
        assert analyzer1.sentiment_analyzer is analyzer2.sentiment_analyzer
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_positive_sentiment(self, mock_logger, mock_pipeline_func):
        """Test analyzing text with positive sentiment"""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.95}]
        mock_pipeline_func.return_value = mock_pipeline
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze("This is great!")
        
        assert result["label"] == "POSITIVE"
        assert result["score"] == 0.95
        mock_pipeline.assert_called_once_with("This is great!")
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_negative_sentiment(self, mock_logger, mock_pipeline_func):
        """Test analyzing text with negative sentiment"""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "NEGATIVE", "score": 0.89}]
        mock_pipeline_func.return_value = mock_pipeline
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze("This is terrible!")
        
        assert result["label"] == "NEGATIVE"
        assert result["score"] == 0.89
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_neutral_sentiment(self, mock_logger, mock_pipeline_func):
        """Test analyzing text with neutral sentiment"""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "NEUTRAL", "score": 0.65}]
        mock_pipeline_func.return_value = mock_pipeline
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze("It's okay")
        
        assert result["label"] == "NEUTRAL"
        assert result["score"] == 0.65
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_empty_string(self, mock_logger, mock_pipeline_func):
        """Test analyzing empty string returns neutral sentiment"""
        mock_pipeline_func.return_value = Mock()
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze("")
        
        assert result["label"] == "NEUTRAL"
        assert result["score"] == 0.0
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_whitespace_only(self, mock_logger, mock_pipeline_func):
        """Test analyzing whitespace-only string returns neutral sentiment"""
        mock_pipeline_func.return_value = Mock()
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze("   ")
        
        assert result["label"] == "NEUTRAL"
        assert result["score"] == 0.0
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_none_input(self, mock_logger, mock_pipeline_func):
        """Test analyzing None input returns neutral sentiment"""
        mock_pipeline_func.return_value = Mock()
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze(None)
        
        assert result["label"] == "NEUTRAL"
        assert result["score"] == 0.0
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_long_text(self, mock_logger, mock_pipeline_func):
        """Test analyzing long text"""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.88}]
        mock_pipeline_func.return_value = mock_pipeline
        
        long_text = "This is a very long comment. " * 50
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze(long_text)
        
        assert result["label"] == "POSITIVE"
        assert result["score"] == 0.88
        mock_pipeline.assert_called_once_with(long_text)
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_special_characters(self, mock_logger, mock_pipeline_func):
        """Test analyzing text with special characters"""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.92}]
        mock_pipeline_func.return_value = mock_pipeline
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze("Amazing!!! 😊 @user #hashtag")
        
        assert result["label"] == "POSITIVE"
        assert result["score"] == 0.92
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_raises_analysis_failed_error(self, mock_logger, mock_pipeline_func):
        """Test that analyzer errors raise AnalysisFailedError"""
        mock_pipeline = Mock()
        mock_pipeline.side_effect = Exception("BERT model error")
        mock_pipeline_func.return_value = mock_pipeline
        
        analyzer = BertSentimentAnalyzer()
        
        with pytest.raises(AnalysisFailedError) as exc_info:
            analyzer.analyze("Test text")
        
        assert exc_info.value.details["comment_id"] == 0
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_load_model_success(self, mock_logger, mock_pipeline_func):
        """Test successful model loading"""
        mock_pipeline_func.return_value = Mock()
        
        analyzer = BertSentimentAnalyzer()
        analyzer.load_model()
        
        assert mock_pipeline_func.call_count >= 1
        assert BertSentimentAnalyzer._pipeline is not None
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_load_model_failure_raises_error(self, mock_logger, mock_pipeline_func):
        """Test that model loading errors raise ModelLoadError"""
        mock_pipeline_func.side_effect = Exception("Failed to load model")
        
        analyzer = BertSentimentAnalyzer()
        
        with pytest.raises(ModelLoadError) as exc_info:
            analyzer.load_model()
        
        assert "distilbert-base-uncased-finetuned-sst-2-english" in str(exc_info.value.details)
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_multiple_calls(self, mock_logger, mock_pipeline_func):
        """Test multiple analyze calls work correctly"""
        mock_pipeline = Mock()
        mock_pipeline.side_effect = [
            [{"label": "POSITIVE", "score": 0.9}],
            [{"label": "NEGATIVE", "score": 0.85}],
            [{"label": "NEUTRAL", "score": 0.6}]
        ]
        mock_pipeline_func.return_value = mock_pipeline
        
        analyzer = BertSentimentAnalyzer()
        
        result1 = analyzer.analyze("Great!")
        result2 = analyzer.analyze("Bad!")
        result3 = analyzer.analyze("Okay")
        
        assert result1["label"] == "POSITIVE"
        assert result2["label"] == "NEGATIVE"
        assert result3["label"] == "NEUTRAL"
        assert mock_pipeline.call_count == 3
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyzer_logger_initialized(self, mock_logger, mock_pipeline_func):
        """Test that logger is initialized properly"""
        mock_pipeline_func.return_value = Mock()
        mock_logger_instance = Mock()
        mock_logger.return_value = mock_logger_instance
        
        analyzer = BertSentimentAnalyzer()
        
        assert analyzer.logger is not None
        mock_logger.assert_called()
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_confidence_scores_range(self, mock_logger, mock_pipeline_func):
        """Test that confidence scores are within valid range"""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.75}]
        mock_pipeline_func.return_value = mock_pipeline
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze("Test")
        
        assert 0.0 <= result["score"] <= 1.0
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_analyze_returns_dict_format(self, mock_logger, mock_pipeline_func):
        """Test that analyze returns proper dict format"""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.95}]
        mock_pipeline_func.return_value = mock_pipeline
        
        analyzer = BertSentimentAnalyzer()
        result = analyzer.analyze("Test")
        
        assert isinstance(result, dict)
        assert "label" in result
        assert "score" in result
    
    @patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
    @patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
    def test_singleton_pattern_pipeline(self, mock_logger, mock_pipeline_func):
        """Test that pipeline follows singleton pattern"""
        mock_pipeline_func.return_value = Mock()
        
        analyzer1 = BertSentimentAnalyzer()
        pipeline1 = BertSentimentAnalyzer._pipeline
        
        analyzer2 = BertSentimentAnalyzer()
        pipeline2 = BertSentimentAnalyzer._pipeline
        
        assert pipeline1 is pipeline2
        mock_pipeline_func.assert_called_once()