#add type hinting across entire project
from abc import ABC, abstractmethod
from typing import List, Optional
from src.repositories import Comment

class ICommentRepository(ABC):
    #Interface defining contract for comment data access
    
    @abstractmethod
    def add(self, comment: Comment) -> None:
        pass #add a comment to the repository

    @abstractmethod
    def get_by_id(self,comment_id: int) -> Optional[Comment]:
        pass #retrieve a comment by its ID

    @abstractmethod
    def update(self, comment: Comment) -> None:
        #update an existing comment
        pass

    @abstractmethod
    def get_all(self) -> List[Comment]:
        pass #get all comments
