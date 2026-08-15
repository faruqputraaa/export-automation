from email.message import EmailMessage
from pathlib import Path


class BrevoSender:
    def __init__(
        self,
        smtp,
        sender_email: str,
        sender_name: str
    ):
        self.smtp = smtp
        self.sender_email = sender_email
        self.sender_name = sender_name

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

        except Exception as error:
            print(f"Gagal mengirim ke {receiver}: {error}")
            return False