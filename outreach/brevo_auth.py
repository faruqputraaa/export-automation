import os
import smtplib

from dotenv import load_dotenv


class BrevoAuth:
    def __init__(self):
        load_dotenv()

        self.host = os.getenv("BREVO_SMTP_HOST")
        self.port = int(os.getenv("BREVO_SMTP_PORT", "587"))
        self.login = os.getenv("BREVO_SMTP_LOGIN")
        self.password = os.getenv("BREVO_SMTP_PASSWORD")

        if not self.host:
            raise ValueError("BREVO_SMTP_HOST belum ditemukan")

        if not self.login:
            raise ValueError("BREVO_SMTP_LOGIN belum ditemukan")

        if not self.password:
            raise ValueError("BREVO_SMTP_PASSWORD belum ditemukan")

    def connect(self):
        smtp = smtplib.SMTP(
            self.host,
            self.port,
            timeout=30
        )

        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(
            self.login,
            self.password
        )

        return smtp