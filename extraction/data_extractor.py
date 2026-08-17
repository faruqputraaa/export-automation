import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from typing import Any


class DataExtractor:

    EMAIL_PATTERN = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    def extract_emails(
        self,
        content: str
    ) -> list[str]:
        """
        Mengambil semua alamat email dari raw content.
        """

        emails = re.findall(
            self.EMAIL_PATTERN,
            content
        )

        return list(
            dict.fromkeys(
                emails
            )
        )

    def extract_company_name(
        self,
        html: str,
        website: str
    ) -> str:
        """
        Mencoba mengambil nama perusahaan
        dari metadata HTML.
        """

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # 1. Open Graph site name
        og_site = soup.find(
            "meta",
            attrs={
                "property": "og:site_name"
            }
        )

        if og_site:
            name = og_site.get("content", "").strip()

            if name:
                return name

        # 2. Application name
        app_name = soup.find(
            "meta",
            attrs={
                "name": "application-name"
            }
        )

        if app_name:
            name = app_name.get("content", "").strip()

            if name:
                return name

        # 3. HTML title
        if soup.title:
            title = soup.title.get_text(
                strip=True
            )

            if title:
                # Bersihkan title umum
                for separator in [
                    " | ",
                    " - ",
                    " — ",
                    " – "
                ]:
                    if separator in title:
                        title = title.split(
                            separator
                        )[0].strip()
                        break

                if title:
                    return title

        # 4. Fallback dari domain
        hostname = urlparse(
            website
        ).hostname

        if hostname:
            hostname = hostname.replace(
                "www.",
                ""
            )

            domain_name = hostname.split(
                "."
            )[0]

            if domain_name:
                return domain_name.replace(
                    "-",
                    " "
                ).title()

        return ""

    def extract_country(self, content: str) -> str:
        countries = [
            "Nepal",
            "India",
            "Indonesia",
            "United States",
            "United Kingdom",
            "Canada",
            "Australia",
            "Germany",
            "France",
        ]
    
        content_lower = content.lower()
    
        for country in countries:
            if country.lower() in content_lower:
                return country
    
        return ""

    def extract_buyer(
        self,
        content: str,
        website: str,
        source_platform: str,
        html: str = "",
        buyer_name: str = "",
        company_name: str = "",
        country: str = "",
    ) -> list[dict[str, Any]]:

        emails = self.extract_emails(
            content
        )

        if not company_name and html:
            company_name = self.extract_company_name(
                html,
                website
            )
        
        if not country:
            country = self.extract_country(content)

        records = []

        for email in emails:
            records.append({
                "buyer_name": buyer_name,
                "company_name": company_name,
                "email": email,
                "website": website,
                "country": country,
                "source_platform": source_platform,
            })

        return records