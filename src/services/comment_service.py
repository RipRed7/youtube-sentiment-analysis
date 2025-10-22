from typing import List, Dict
from src.domain.models import Comment, Sentiment, SentimentLabel
from src.repositories.icommentRepository import ICommentRepository
from src.backend.analyzers.Isentiment_analyzer import ISentimentAnalyzer
from src.backend.api.Icomment_fetcher import ICommentFetcher
"""fix these file names""" 

class CommentService:
    #service layer for comment business logic
    def __init__(self,
                 comment_repository: ICommentRepository,
                 sentiment_analyzer: ISentimentAnalyzer,
                 comment_fetcher: ICommentFetcher):
                self.comment_repo = comment_repository
                self.analyzer = sentiment_analyzer
                self.comment_fetcher = comment_fetcher

    def fetch_and_store_comments(self) -> List[Comment]:
        #fetch comments and store in repo
        raw_comments = self.comment_fetcher.get_comments()

        stored_comments = []
        for comment_data in raw_comments:
               comment = Comment(id = 0
                                 , author = comment_data["author"] 
                                 , text = comment_data["text"]
                                 , videoId = comment_data["video_id"]
                                 )
               self.comment_repo.add(comment)
               stored_comments.append(comment)
        return stored_comments


    def analyze_comment_sentiment(self, comment_id: int) -> Sentiment:
           #analyze sentiment of a comment
           comment = self.comment_repo.get_by_id(comment_id)
           if comment is None:
            raise ValueError(f"Comment with id {comment_id} not found")
           raw_result = self.analyzer.analyze(comment.text)

           label_map = {
                 "POSITIVE": SentimentLabel.POSTIVE,
                 "NEGATIVE": SentimentLabel.NEGATIVE,
                 "NETURAL": SentimentLabel.NEUTRAL
           }

           sentiment_label = label_map.get(raw_result['label'], SentimentLabel.NEUTRAL)
           sentiment = Sentiment(label = sentiment_label, Confidence = raw_result['score'])
           comment.sentiment = sentiment
           self.comment_repo.update(comment)
           return sentiment

    def analyze_all_comments(self) -> Dict[int, Sentiment]:
        #analyze sentiment for all comments
        comments = self.comment_repo.get_all()
        results = {}
        for comment in comments:
            sentiment = self.analyze_comment_sentiment(comment.id)
            results[comment.id] = sentiment
        return results

    def get_sentiment_distrib(self) -> Dict[SentimentLabel, int]:
        #calculate sentiment distribution for all comments
        comments = self.comment_repo.get_all()
        distribution = {label: 0 for label in SentimentLabel}
        for comment in comments:
             if comment.sentiment:
                  distribution[comment.sentiment.label] += 1
        return distribution

    def get_comment(self, comment_id: int) -> Comment:
         #retrieve a comment by id
        comment = self.comment_repo.get_by_id(comment_id)
        if comment is None:
            raise ValueError(f"Comment with id {comment_id} not found")
        return comment
    
    def get_all_comments(self) -> List[Comment]:
        #retrieve all comments
        return self.comment_repo.get_all()
    


