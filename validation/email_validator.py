import re
from typing import Any


class EmailValidator:
    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    IMAGE_EXTENSIONS = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
    )

    def is_valid(self, email: str) -> bool:
        """
        Mengecek apakah email memiliki format yang valid.
        """
    
        if not email:
            return False
    
        email = email.strip().lower()
    
        # Buang kandidat yang sebenarnya nama file gambar
        if email.endswith(self.IMAGE_EXTENSIONS):
            return False
    
        # Validasi format dasar
        if not self.EMAIL_PATTERN.match(email):
            return False
    
        # Pisahkan local-part dan domain
        try:
            local_part, domain = email.split("@", 1)
        except ValueError:
            return False
    
        # Domain terlalu panjang
        if len(domain) > 50:
            return False
    
        return True

    def validate_records(self, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Memisahkan record valid dan invalid.

        Returns:
            valid_records, invalid_records
        """

        valid_records = []
        invalid_records = []

        for record in records:
            email = record.get("email", "")

            if self.is_valid(email):
                record["email"] = email.strip().lower()
                valid_records.append(record)
            else:
                invalid_records.append(record)

        return valid_records, invalid_records