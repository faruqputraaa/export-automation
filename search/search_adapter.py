from abc import ABC, abstractmethod
from typing import Any


class SearchAdapter(ABC):

    @abstractmethod
    def search(self, query: str) -> list[dict[str, Any]]:
        """
        Mencari sumber berdasarkan query.

        Return:
            list[dict[str, Any]]
        """
        pass