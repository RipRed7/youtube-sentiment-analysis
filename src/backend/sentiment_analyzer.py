import torch
from transformers import pipeline

class SentimentAnalyzer:
    _pipeline = None # Class-level attribute for the pipeline

    def __init__(self):
        if SentimentAnalyzer._pipeline is None: # check if pipeline exists, if created already, reuse instead of reloading
            print("Loading BERT model... may take a few seconds... :D")
            SentimentAnalyzer._pipeline = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english') #load model
        self.sentiment_analyzer = SentimentAnalyzer._pipeline # Instance level attribute pointing to shared class-level attribute

    def analyze(self, text):
        return self.sentiment_analyzer(text)