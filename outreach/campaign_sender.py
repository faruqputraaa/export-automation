import csv
from pathlib import Path


class CampaignSender:
    def __init__(
        self,
        sender,
        logger,
        daily_limit: int = 100
    ):
        self.sender = sender
        self.logger = logger
        self.daily_limit = daily_limit

    def load_emails(self, file_path: str) -> list[str]:
        """
        Membaca email dari file CSV.
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

        # Deduplicate
        return list(dict.fromkeys(emails))

    def send_campaign(
        self,
        file_path: str,
        subject: str,
        body: str,
        attachment=None,
        dry_run: bool = False
    ) -> dict:
    
        emails = self.load_emails(file_path)
    
        result = {
            "total": len(emails),
            "sent": 0,
            "skipped": 0,
            "failed": 0,
            "dry_run": dry_run,
        }
    
        for email in emails:
    
            if result["sent"] >= self.daily_limit:
                print("Daily send limit tercapai.")
                break
    
            if self.logger.was_sent(email):
                print(
                    f"SKIP: {email} sudah pernah dikirim."
                )
    
                result["skipped"] += 1
                continue
    
            # =========================
            # DRY RUN
            # =========================
    
            if dry_run:
                print(
                    f"[DRY RUN] Would send to: {email}"
                )
    
                result["sent"] += 1
                continue
    
            # =========================
            # REAL SEND
            # =========================
    
            print(f"SENDING: {email}")
    
            success = self.sender.send(
                receiver=email,
                subject=subject,
                body=body,
                attachment=attachment
            )
    
            if success:
                self.logger.log_send(
                    email,
                    "sent"
                )
    
                result["sent"] += 1
    
                print(f"SENT: {email}")
    
            else:
                self.logger.log_send(
                    email,
                    "failed"
                )
    
                result["failed"] += 1
    
                print(f"FAILED: {email}")
    
        return result