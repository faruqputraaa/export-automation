import csv
from pathlib import Path


class ClassificationLogger:
    BUSINESS_FILE = Path("data/business_emails.csv")
    INDIVIDUAL_FILE = Path("data/individual_emails.csv")

    def __init__(self):
        self.BUSINESS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    def save(
        self,
        classifications: dict[str, str]
    ) -> None:

        business_emails = []
        individual_emails = []

        for email, category in classifications.items():

            if category == "business":
                business_emails.append(email)

            elif category == "individual":
                individual_emails.append(email)

        self._write(
            self.BUSINESS_FILE,
            business_emails
        )

        self._write(
            self.INDIVIDUAL_FILE,
            individual_emails
        )

    def _write(
        self,
        file_path: Path,
        emails: list[str]
    ) -> None:

        with file_path.open(
            mode="w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow(["email"])

            for email in emails:
                writer.writerow([email])