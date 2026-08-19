from typing import Any

from search.search_adapter import SearchAdapter


class SourceManager:

    def __init__(
        self,
        adapters: list[SearchAdapter]
    ):
        self.adapters = adapters

    def search(
        self,
        query: str
    ) -> list[dict[str, Any]]:

        results = []

        for adapter in self.adapters:

            try:
                adapter_results = adapter.search(
                    query
                )

                results.extend(
                    adapter_results
                )

            except Exception as error:
                print(
                    f"Source error: "
                    f"{adapter.__class__.__name__}: "
                    f"{error}"
                )

        return self._deduplicate(results)

    def _deduplicate(
        self,
        results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:

        seen = set()
        unique_results = []

        for result in results:

            url = result.get("url", "").strip()

            if not url:
                continue

            if url in seen:
                continue

            seen.add(url)
            unique_results.append(result)

        return unique_results