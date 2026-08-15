from abc import ABC, abstractmethod


class SearchAdapter(ABC):

    @abstractmethod
    def search(self, query: str) -> list[dict]:
        """
        Mencari sumber berdasarkan query.

        Return:
            list[dict]
        """
        pass