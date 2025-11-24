from typing import List, Dict
from src.domain.models import Comment, Sentiment, SentimentLabel
from src.repositories.icommentRepository import ICommentRepository
from src.backend.analyzers.Isentiment_analyzer import ISentimentAnalyzer
from src.backend.api.Icomment_fetcher import ICommentFetcher
from src.utils.logger import get_logger
from src.utils.exceptions import CommentNotFoundError, AnalysisFailedError

class CommentService:
    #service layer for comment business logic
    def __init__(self,
                 comment_repository: ICommentRepository,
                 sentiment_analyzer: ISentimentAnalyzer,
                 comment_fetcher: ICommentFetcher):
                self.comment_repo = comment_repository
                self.analyzer = sentiment_analyzer
                self.comment_fetcher = comment_fetcher
                self.logger = get_logger()
                self.logger.info("CommentService initialized")

    def fetch_and_store_comments(self) -> List[Comment]:
        #fetch comments and store in repo
        self.logger.info("Starting comment fetch and storage process")

        try:
            raw_comments = self.comment_fetcher.get_comments()
            self.logger.debug(f"Received {len(raw_comments)} raw comments from fetcher")
        except Exception as e:
            self.logger.exception("Failed to fetch comments from API")
            raise        


        stored_comments = []
        for i, comment_data in enumerate(raw_comments):
            try:
               comment = Comment(id = 0
                                 , author = comment_data["author"] 
                                 , text = comment_data["text"]
                                 , videoId = comment_data["video_id"]
                                 )
               self.comment_repo.add(comment)
               stored_comments.append(comment)
               self.logger.debug(f"Stored comment {i + 1}/{len(raw_comments)} from {comment.author}")
               
            except Exception as e:
                self.logger.error(f"Failed to store comment {i + 1}: {e}")
                continue

        self.logger.info(f"Successfully stored {len(stored_comments)} comments in repository")
        return stored_comments


    def analyze_comment_sentiment(self, comment_id: int) -> Sentiment:
        #analyze sentiment of a comment
        self.logger.debug(f"Analyzing sentiment for comment ID: {comment_id}")

        comment = self.comment_repo.get_by_id(comment_id)
        if comment is None:
            self.logger.warning(f"Comment not found: {comment_id}")
            raise CommentNotFoundError(comment_id)

        try:
            raw_result = self.analyzer.analyze(comment.text)
            self.logger.debug(f"Raw analysis result for comment {comment_id}: {raw_result}")
        except Exception as e:
           self.logger.exception(f"Sentiment analysis failed comment {comment_id}")
           raise AnalysisFailedError(comment_id, e)
        
        label_map = {
              "POSITIVE": SentimentLabel.POSITIVE,
              "NEGATIVE": SentimentLabel.NEGATIVE,
              "NEUTRAL": SentimentLabel.NEUTRAL
        }

        sentiment_label = label_map.get(raw_result['label'], SentimentLabel.NEUTRAL)
        sentiment = Sentiment(label = sentiment_label, Confidence = raw_result['score'])
        comment.sentiment = sentiment
        self.comment_repo.update(comment)

        self.logger.info(f"Comment {comment_id} analyzed: {sentiment_label.value} (confidence: {sentiment.Confidence:.3f})")
        return sentiment

    def analyze_all_comments(self) -> Dict[int, Sentiment]:
        # analyze sentiment for all comments
        comments = self.comment_repo.get_all()
        total_comments = len(comments)

        self.logger.info(f"Starting batch sentiment analysis for {total_comments} comments")

        results = {}
        successes = 0
        failures = 0


        for i, comment in enumerate(comments):
            try:
                sentiment = self.analyze_comment_sentiment(comment.id)
                results[comment.id] = sentiment
                successes += 1

                if i % 10 == 0:
                    self.logger.info(f"Progress: {i}/{total_comments} comments analyzed")

            except Exception as e:
                failures += 1
                self.logger.error(f"Failed to analyze comment {comment.id}: {e}")
                continue

        self.logger.info(f"Batch analysis complete: {successes} succeeded, {failures} failed")
        return results

    def get_sentiment_distrib(self) -> Dict[SentimentLabel, int]:
        #calculate sentiment distribution for all comments
        self.logger.debug("Calculating sentiment distribution")

        comments = self.comment_repo.get_all()
        distribution = {label: 0 for label in SentimentLabel}

        for comment in comments:
             if comment.sentiment:
                  distribution[comment.sentiment.label] += 1

        self.logger.info(f"Sentiment distribution: {distribution}")
        return distribution

    def get_comment(self, comment_id: int) -> Comment:
         # retrieve a comment by id
        self.logger.debug(f"Retrieving comment ID: {comment_id}")
        
        comment = self.comment_repo.get_by_id(comment_id)
        if comment is None:
            self.logger.warning(f"Comment not found: {comment_id}")
            raise CommentNotFoundError(f"Comment with id {comment_id} not found")
        
        return comment
    
    def get_all_comments(self) -> List[Comment]:
        # retrieve all comments 
        comments = self.comment_repo.get_all()
        self.logger.debug(f"Retrieved {len(comments)} comments from repository")
        return comments
    