import pytest
from unittest.mock import Mock, patch
from src.backend.analyzers.bert_sentiment_analyzer import BertSentimentAnalyzer

@patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
@patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
def test_analyzer_returns_dict_with_label_and_score(mock_logger, mock_pipeline):
    """Test that analyzer returns dict with 'label' and 'score' keys"""
    
    # Reset singleton
    BertSentimentAnalyzer._pipeline = None
    BertSentimentAnalyzer._logger = None
    
    # Mock the pipeline
    mock_pipe = Mock()
    mock_pipe.return_value = [{"label": "LABEL_2", "score": 0.95}]
    mock_pipeline.return_value = mock_pipe
    
    analyzer = BertSentimentAnalyzer()
    result = analyzer.analyze("This is great!")
    
    assert "label" in result
    assert "score" in result


@patch('src.backend.analyzers.bert_sentiment_analyzer.pipeline')
@patch('src.backend.analyzers.bert_sentiment_analyzer.get_logger')
def test_analyzer_handles_empty_text(mock_logger, mock_pipeline):
    """Test that analyzer handles empty text gracefully"""

    BertSentimentAnalyzer._pipeline = None
    BertSentimentAnalyzer._logger = None
    
    mock_pipeline.return_value = Mock()
    
    analyzer = BertSentimentAnalyzer()
    result = analyzer.analyze("")
    
    assert result["label"] == "NEUTRAL"
    assert result["score"] == 0.0
