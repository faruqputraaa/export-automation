import os
from typing import Any

import requests
from dotenv import load_dotenv

from search.search_adapter import SearchAdapter


class FoursquareSearch(SearchAdapter):

    BASE_URL = (
        "https://places-api.foursquare.com/places/search"
    )

    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv(
            "FOURSQUARE_API_KEY"
        )

        if not self.api_key:
            raise ValueError(
                "FOURSQUARE_API_KEY "
                "belum ditemukan di .env"
            )

    def search(
        self,
        query: str
    ) -> list[dict[str, Any]]:

        headers = {
            "Accept": "application/json",
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "X-Places-Api-Version": "2025-06-17",
        }

        params = {
            "query": query,
            "limit": 10,
            "fields": (
                "fsq_place_id,"
                "name,"
                "location,"
                "website,"
                "email,"
                "categories"
            ),
        }

        response = requests.get(
            self.BASE_URL,
            headers=headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for place in data.get("results", []):
            name = place.get("name", "")
            website = place.get("website", "")
            email = place.get("email", "")

            location = place.get(
                "location",
                {}
            )

            address = location.get(
                "formatted_address",
                ""
            )

            categories = place.get(
                "categories",
                []
            )

            category_names = [
                category.get("name", "")
                for category in categories
            ]

            content_parts = [
                name,
                address,
                email,
                ", ".join(category_names),
            ]

            content = "\n".join(
                part
                for part in content_parts
                if part
            )

            results.append({
                "url": website,
                "title": name,
                "content": content,
            })

        return results