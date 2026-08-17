import csv
from pathlib import Path
from datetime import datetime
from typing import Any


class ActivityLogger:
    BUYERS_FILE = Path("data/buyers.csv")
    SENT_LOG_FILE = Path("data/sent_log.csv")

    BUYER_FIELDS = [
        "email",
        "buyer_name",
        "company_name",
        "website",
        "country",
        "source_platform",
    ]

    SENT_FIELDS = [
        "email",
        "status",
        "timestamp",
    ]

    def __init__(self):
        self.BUYERS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    def save_buyers(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return

        file_exists = self.BUYERS_FILE.exists()

        with self.BUYERS_FILE.open(
            mode="a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=self.BUYER_FIELDS
            )

            if not file_exists:
                writer.writeheader()

            for record in records:
                writer.writerow({
                    field: record.get(field, "")
                    for field in self.BUYER_FIELDS
                })

    def log_send(
        self,
        email: str,
        status: str
    ) -> None:

        file_exists = self.SENT_LOG_FILE.exists()

        with self.SENT_LOG_FILE.open(
            mode="a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=self.SENT_FIELDS
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                "email": email,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            })

    def was_sent(self, email: str) -> bool:
        """
        Mengecek apakah email sudah pernah berhasil dikirim.
        """
    
        if not self.SENT_LOG_FILE.exists():
            return False
    
        with self.SENT_LOG_FILE.open(
            mode="r",
            newline="",
            encoding="utf-8"
        ) as file:
    
            reader = csv.DictReader(file)
    
            for row in reader:
                if (
                    row.get("email", "").strip().lower()
                    == email.strip().lower()
                    and row.get("status") == "sent"
                ):
                    return True
    
        return False