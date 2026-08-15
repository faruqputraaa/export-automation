import os
import json
import requests
import csv
from dotenv import load_dotenv


class GeminiClassifier:
    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY belum ditemukan di .env"
            )

        self.model = "gemini-2.5-flash"

        self.url = (
            f"https://generativelanguage.googleapis.com/"
            f"v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )

    def classify(self, emails: list[str]) -> dict[str, str]:
        """
        Mengklasifikasikan email menjadi business atau individual.
        """

        email_list = "\n".join(
            f"- {email}"
            for email in emails
        )

        prompt = f"""
Classify each email address into exactly one category:

- business
- individual

Rules:
- business: email appears to represent a company,
  organization, business, sales, support, info, contact,
  or corporate domain.
- individual: email appears to represent a personal
  email account.

Return ONLY valid JSON.
Do not include markdown.

Format:
{{
  "email@example.com": "business",
  "person@gmail.com": "individual"
}}

Emails:
{email_list}
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            self.url,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        text = (
            data["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        return json.loads(text)

    def classify_in_batches(
        self,
        emails: list[str],
        batch_size: int = 20
    ) -> dict[str, str]:
    
        unique_emails = list(
            dict.fromkeys(emails)
        )
    
        results = {}
    
        for i in range(
            0,
            len(unique_emails),
            batch_size
        ):
            batch = unique_emails[
                i:i + batch_size
            ]
    
            batch_result = self.classify(batch)
    
            results.update(batch_result)
    
        return results

    def load_emails_from_csv(self, file_path: str) -> list[str]:
        """
        Membaca email dari buyers.csv.
        """
    
        emails = []
    
        with open(
            file_path,
            mode="r",
            encoding="utf-8"
        ) as file:
    
            reader = csv.DictReader(file)
    
            for row in reader:
                email = row.get("email", "").strip().lower()
    
                if email:
                    emails.append(email)
    
        return list(dict.fromkeys(emails))