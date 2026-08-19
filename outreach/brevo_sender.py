from email.message import EmailMessage
from pathlib import Path
import smtplib


class BrevoSender:

    def __init__(
        self,
        smtp,
        sender_email: str,
        sender_name: str,
        auth=None
    ):
        self.smtp = smtp
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.auth = auth

    def send(
        self,
        receiver: str,
        subject: str,
        body: str,
        attachment: Path | None = None
    ) -> bool:

        message = EmailMessage()

        message["From"] = (
            f"{self.sender_name} <{self.sender_email}>"
        )
        message["To"] = receiver
        message["Subject"] = subject

        message.set_content(body)

        if attachment:
            with attachment.open("rb") as file:
                file_data = file.read()

            message.add_attachment(
                file_data,
                maintype="application",
                subtype="pdf",
                filename=attachment.name
            )

        try:
            self.smtp.send_message(message)
            return True

        except smtplib.SMTPServerDisconnected as error:
            print(
                f"SMTP disconnected "
                f"while sending to {receiver}: {error}"
            )

            if not self.auth:
                return False

            try:
                print("Reconnecting to Brevo SMTP...")

                self.smtp = self.auth.connect()

                print("Retrying send...")

                self.smtp.send_message(message)

                return True

            except Exception as retry_error:
                print(
                    f"Retry failed for {receiver}: "
                    f"{retry_error}"
                )

                return False

        except Exception as error:
            print(
                f"Gagal mengirim ke "
                f"{receiver}: {error}"
            )

            return False