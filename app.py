import os
from pathlib import Path

from dotenv import load_dotenv

from activity_logging.activity_logger import ActivityLogger
from classification.classification_logger import ClassificationLogger
from classification.gemini_classifier import GeminiClassifier
from extraction.data_extractor import DataExtractor
from outreach.brevo_auth import BrevoAuth
from outreach.brevo_sender import BrevoSender
from outreach.campaign_sender import CampaignSender
from reports.report_generator import ReportGenerator
from search.website_search import WebsiteSearch
from validation.email_validator import EmailValidator

from search.tavily_search import TavilySearch


def run_search(query: str):
    tavily_search = TavilySearch()
    website_search = WebsiteSearch()

    extractor = DataExtractor()
    validator = EmailValidator()
    logger = ActivityLogger()

    if not query:
        print("Query tidak boleh kosong.")
        return

    print(f"\nMencari: {query}")
    print("Menggunakan Tavily...\n")

    search_results = tavily_search.search(query)

    if not search_results:
        print("Tidak ada hasil pencarian.")
        return

    total_records = 0
    total_valid = 0
    total_invalid = 0

    for index, search_result in enumerate(
        search_results,
        start=1
    ):
        url = search_result["url"]

        print(
            f"[{index}/{len(search_results)}] "
            f"Mengambil: {url}"
        )

        try:
            website_results = website_search.search(
                url
            )

        except Exception as error:
            print(
                f"  Gagal mengambil website: {error}"
            )
            continue

        for result in website_results:

            records = extractor.extract_buyer(
                content=result["content"],
                html=result.get("html", ""),
                website=result["url"],
                source_platform="Tavily",
            )

            valid_records, invalid_records = (
                validator.validate_records(records)
            )

            logger.save_buyers(valid_records)

            total_records += len(records)
            total_valid += len(valid_records)
            total_invalid += len(invalid_records)

            print(
                f"  Email ditemukan : {len(records)}"
            )
            print(
                f"  Email valid     : {len(valid_records)}"
            )

    print("\n=== SEARCH RESULT ===")
    print(
        f"Search results : {len(search_results)}"
    )
    print(
        f"Total records  : {total_records}"
    )
    print(
        f"Valid emails   : {total_valid}"
    )
    print(
        f"Invalid emails : {total_invalid}"
    )


def run_classification():
    classifier = GeminiClassifier()
    logger = ClassificationLogger()

    emails = classifier.load_emails_from_csv("data/buyers.csv")

    if not emails:
        print("Tidak ada email di buyers.csv.")
        return

    print(f"Classifying {len(emails)} unique emails...")

    classifications = classifier.classify_in_batches(emails, batch_size=20)

    logger.save(classifications)

    business = sum(1 for category in classifications.values() if category == "business")

    individual = sum(
        1 for category in classifications.values() if category == "individual"
    )

    print("\n=== CLASSIFICATION RESULT ===")
    print(f"Business   : {business}")
    print(f"Individual : {individual}")


def run_send(
    audience: str,
    dry_run: bool = False
):
    load_dotenv()

    files = {
        "business": "data/business_emails.csv",
        "individual": "data/individual_emails.csv",
    }

    if audience == "all":
        email_files = [
            files["business"],
            files["individual"],
        ]
    else:
        email_files = [files[audience]]

    # =========================
    # RESULT
    # =========================

    total_result = {
        "total": 0,
        "sent": 0,
        "skipped": 0,
        "failed": 0,
    }

    # =========================
    # SMTP
    # =========================

    smtp = None
    sender = None

    if not dry_run:
        auth = BrevoAuth()
        smtp = auth.connect()

        sender = BrevoSender(
            smtp=smtp,
            sender_email=os.getenv(
                "BREVO_SENDER_EMAIL"
            ),
            sender_name=os.getenv(
                "BREVO_SENDER_NAME",
                "Export Automation"
            )
        )

    # =========================
    # LOGGER
    # =========================

    activity_logger = ActivityLogger()

    campaign = CampaignSender(
        sender=sender,
        logger=activity_logger,
        daily_limit=int(
            os.getenv(
                "DAILY_SEND_LIMIT",
                "100"
            )
        )
    )

    # =========================
    # ATTACHMENT
    # =========================

    attachment = Path(
        "assets/company_presentation.pdf"
    )

    if not attachment.exists():
        raise FileNotFoundError(
            f"Attachment tidak ditemukan: {attachment}"
        )

    # =========================
    # CAMPAIGN
    # =========================

    for email_file in email_files:

        if not Path(email_file).exists():
            print(
                f"File tidak ditemukan: {email_file}"
            )
            continue

        result = campaign.send_campaign(
            file_path=email_file,
            subject="Singing Bowls Company Presentation",
            body="""\
Hello,

We are an export supplier of Himalayan Singing Bowls.

Please find our company presentation attached.

If you are interested in our products,
please feel free to contact us.

Best regards,
Export Automation
""",
            attachment=attachment,
            dry_run=dry_run
        )

        for key in [
            "total",
            "sent",
            "skipped",
            "failed",
        ]:
            total_result[key] += result[key]

    # =========================
    # CLOSE SMTP
    # =========================

    if smtp:
        smtp.quit()

    # =========================
    # RESULT
    # =========================

    print("\n=== SEND RESULT ===")

    if dry_run:
        print("Mode    : DRY RUN")
    else:
        print("Mode    : LIVE")

    print(f"Total   : {total_result['total']}")
    print(f"Sent    : {total_result['sent']}")
    print(f"Skipped : {total_result['skipped']}")
    print(f"Failed  : {total_result['failed']}")

    return total_result


def run_report():
    report_path = Path("reports/latest_report.txt")

    if not report_path.exists():
        print("Belum ada report.")
        return

    print(report_path.read_text(encoding="utf-8"))
