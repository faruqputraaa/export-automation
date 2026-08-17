import os

from tavily import TavilyClient
from dotenv import load_dotenv

from search.search_adapter import SearchAdapter
from typing import Any


class TavilySearch(SearchAdapter):

    def __init__(self):
        load_dotenv()

        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY belum ditemukan di .env"
            )

        self.client = TavilyClient(
            api_key=api_key
        )

    def search(self, query: str) -> list[dict[str, Any]]:
        response = self.client.search(
            query=query,
            search_depth="basic",
            max_results=5
        )

        results = []

        for item in response.get(
            "results",
            []
        ):
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
            })

        return results