import requests

from bs4 import BeautifulSoup

from search.search_adapter import SearchAdapter


class WebsiteSearch(SearchAdapter):

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            )
        }

    def fetch(self, url: str) -> dict:
        """
        Mengambil konten dari website.
        """

        response = requests.get(
            url,
            headers=self.headers,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Ambil title
        title = ""

        if soup.title:
            title = soup.title.get_text(
                strip=True
            )

        # Hapus elemen yang tidak diperlukan
        for element in soup([
            "script",
            "style",
            "noscript"
        ]):
            element.decompose()

        content = soup.get_text(
            separator=" ",
            strip=True
        )

        return {
            "url": url,
            "title": title,
            "content": content,
            "html": response.text,
        }

    def search(self, query: str) -> list[dict]:
        """
        SearchAdapter implementation.

        Untuk WebsiteSearch, query dianggap
        sebagai URL website.
        """

        result = self.fetch(query)

        return [
            {
                "url": result["url"],
                "title": result["title"],
                "content": result["content"],
                "html": result["html"],
            }
        ]