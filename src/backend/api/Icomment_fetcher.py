from abc import ABC, abstractmethod

class ICommentFetcher(ABC):
    #interface for fetching comments

    @abstractmethod
    def get_comments(self) -> list[dict[str,str]]:
        #fetch comments and returns comments in a list of dicts with author, text, video_id
        pass