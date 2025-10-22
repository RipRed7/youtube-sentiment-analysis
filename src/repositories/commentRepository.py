from typing import List, Optional
from src.repositories import Comment, ICommentRepository

class InMemoryCommentRepo(ICommentRepository):
    #in-memory comment repo using a dict
    def __init__(self):
        self.comments: dict[int, Comment] = {}
        self.next_id: int = 1


    def add(self, comment: Comment) -> None:
        #add a comment to repo
        if comment.id is None or comment.id == 0:
            comment.id = self.next_id
            self.next_id += 1

        self.comments[comment.id] = comment

    def update(self, comment: Comment) -> None:
        #update an existing comment
        if comment.id in self.comments:
            self.comments[comment.id] = comment
        else:
            raise ValueError(f"Comment with id {comment.id} does not exist")
    
    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        #get a comment by its id, return none if not found
        return self.comments.get(comment_id)

    def get_all(self) -> List[Comment]:
        #retrieve all comments as list
        return list(self.comments.values())

    def delete(self, comment_id):
        #delete a comment by its id
        if comment_id in self.comments:
            del self.comments[comment_id]
        else:
            raise ValueError(f"Comment with id {comment_id} does not exist")