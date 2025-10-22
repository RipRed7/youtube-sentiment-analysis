import torch
from transformers import pipeline
from src.backend.analyzers.Isentiment_analyzer import ISentimentAnalyzer

class BertSentimentAnalyzer(ISentimentAnalyzer):
    #bert sentiment analyzer
    _pipeline = None # Class-level attribute for the pipeline

    def __init__(self):
        if BertSentimentAnalyzer._pipeline is None: # check if pipeline exists, if created already, reuse instead of reloading
            print("Loading BERT model... may take a few seconds... :D")
            BertSentimentAnalyzer._pipeline = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english') #load model
        self.sentiment_analyzer = BertSentimentAnalyzer._pipeline # Instance level attribute pointing to shared class-level attribute

    def analyze(self, text: str) -> dict:
                #analyze comment and return result in a dict
        return self.sentiment_analyzer(text)[0]