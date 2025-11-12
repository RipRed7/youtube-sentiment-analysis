from typing import List, Optional
from src.repositories import Comment, ICommentRepository
from src.utils.logger import get_logger
from src.utils.exceptions import CommentNotFoundError

class InMemoryCommentRepo(ICommentRepository):
    #in-memory comment repo using a dict
    def __init__(self):
        self.comments: dict[int, Comment] = {}
        self.next_id: int = 1
        self.logger = get_logger()
        self.logger.info("InMemoryCommentRepo Initialized")


    def add(self, comment: Comment) -> None:
        #add a comment to repo
        if comment.id is None or comment.id == 0:
            comment.id = self.next_id
            self.next_id += 1
            self.logger.debug(f"Assigned new ID {comment.id} to comment")

        self.comments[comment.id] = comment
        self.logger.debug(f"Added comment {comment.id} to repo (total: {len(self.comments)})")

    def update(self, comment: Comment) -> None:
        #update an existing comment
        if comment.id in self.comments:
            self.comments[comment.id] = comment
            self.logger.debug(f"Updated comment {comment.id} to repo")
        else:
            self.logger.error(f"Attempted to update non-existent comment: {comment.id}")
            raise CommentNotFoundError(f"Comment with id {comment.id} does not exist")
    
    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        #get a comment by its id, return none if not found
        comment = self.comments.get(comment_id)

        if comment: 
            self.logger.debug(f"Retrieved comment {comment.id} from repo")
        else:
            self.logger.debug(f"Comment {comment_id} not found in repo")

        return comment

    def get_all(self) -> List[Comment]:
        #retrieve all comments as list
        comments = list(self.comments.values())
        self.logger.debug(f"Retrieved all {len(comments)} comemnts from repo")
        return comments

    def delete(self, comment_id):
        #delete a comment by its id
        if comment_id in self.comments:
            del self.comments[comment_id]
            self.logger.info(f"Deleted comment {comment_id} from repo (remaining: {len(self.comments)})")
        else:
            self.logger.error(f"Attempted to delete non-existent comment: {comment_id}")
            raise CommentNotFoundError(comment_id)