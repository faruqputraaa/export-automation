import csv
import io
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from activity_logging.activity_logger import ActivityLogger
from app import run_send
from classification.gemini_classifier import GeminiClassifier
from extraction.data_extractor import DataExtractor
from outreach.campaign_sender import CampaignSender
from reports.report_generator import ReportGenerator
from search.tavily_search import TavilySearch
from search.website_search import WebsiteSearch
from validation.email_validator import EmailValidator

app = FastAPI(
    title="Export Automation System API",
    description="REST API for buyer discovery and export outreach automation",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "api" / "templates")

latest_send_result = {
    "total": 0,
    "sent": 0,
    "skipped": 0,
    "failed": 0,
}


class SendRequest(BaseModel):
    audience: str = "business"
    subject: str
    body: str
    attachment: str | None = None
    dry_run: bool = True


class SearchRequest(BaseModel):
    query: str


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "export-automation-system",
    }


@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "stats": latest_send_result,
        },
    )


@app.post("/api/search")
def search_buyers(request: SearchRequest):
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty",
        )

    try:
        search = TavilySearch()
        results = search.search(query)

        return {
            "query": query,
            "total": len(results),
            "results": results,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.get("/search")
def search_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={},
    )


@app.post("/ui/search")
def ui_search(request: Request, query: str = Form(...)):
    query = query.strip()

    if not query:
        return """
        <div class="bg-red-50 text-red-700 rounded-xl p-5">
            Query cannot be empty.
        </div>
        """

    try:
        search = TavilySearch()
        results = search.search(query)

        return templates.TemplateResponse(
            request=request,
            name="partials/search_results.html",
            context={
                "query": query,
                "results": results,
            },
        )

    except Exception as error:
        return f"""
        <div class="bg-red-50 text-red-700 rounded-xl p-5">
            Search failed: {error}
        </div>
        """


@app.post("/api/discover")
def discover_buyers(request: SearchRequest):
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty",
        )

    try:
        tavily = TavilySearch()
        website_search = WebsiteSearch()
        extractor = DataExtractor()
        validator = EmailValidator()
        logger = ActivityLogger()

        search_results = tavily.search(query)

        total_records = 0
        total_valid = 0
        total_invalid = 0
        websites_processed = 0

        for search_result in search_results:
            url = search_result.get("url", "")

            if not url:
                continue

            try:
                website_results = website_search.search(url)
                websites_processed += 1

            except Exception:
                continue

            for result in website_results:
                records = extractor.extract_buyer(
                    content=result["content"],
                    html=result.get("html", ""),
                    website=result["url"],
                    source_platform="Tavily",
                )

                valid_records, invalid_records = validator.validate_records(records)

                logger.save_buyers(valid_records)

                total_records += len(records)
                total_valid += len(valid_records)
                total_invalid += len(invalid_records)

        return {
            "query": query,
            "search_results": len(search_results),
            "websites_processed": websites_processed,
            "total_records": total_records,
            "valid_emails": total_valid,
            "invalid_emails": total_invalid,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.post("/ui/upload")
async def ui_upload(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": "CSV file is required.",
            },
        )

    if not file.filename.lower().endswith(".csv"):
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": "Only CSV files are allowed.",
            },
        )

    try:
        content = await file.read()

        text = content.decode("utf-8-sig")

        rows = list(csv.DictReader(text.splitlines()))

        if not rows:
            raise ValueError("CSV file is empty.")

        if "email" not in rows[0]:
            raise ValueError("CSV must contain an email column.")

        buyers_file = Path("data/buyers.csv")

        buyers_file.parent.mkdir(parents=True, exist_ok=True)

        existing = []

        if buyers_file.exists():
            with buyers_file.open("r", encoding="utf-8", newline="") as existing_file:
                existing = list(csv.DictReader(existing_file))

        fieldnames = [
            "email",
            "buyer_name",
            "company_name",
            "website",
            "country",
            "source_platform",
        ]

        combined = existing.copy()

        for row in rows:
            email = row.get("email", "").strip().lower()

            if not email:
                continue

            combined.append(
                {
                    "email": email,
                    "buyer_name": (row.get("buyer_name", "") or "").strip(),
                    "company_name": (row.get("company_name", "") or "").strip(),
                    "website": (row.get("website", "") or "").strip(),
                    "country": (row.get("country", "") or "").strip(),
                    "source_platform": (
                        row.get("source_platform", "Upload") or "Upload"
                    ).strip(),
                }
            )

        unique = {}

        for row in combined:
            email = row["email"]

            if email not in unique:
                unique[email] = row

        with buyers_file.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(unique.values())

        result = {
            "filename": file.filename,
            "uploaded_records": len(rows),
            "total_records": len(unique),
            "duplicates_removed": (len(combined) - len(unique)),
        }

        return templates.TemplateResponse(
            request,
            name="partials/upload_result.html",
            context={
                "result": result,
            },
        )

    except UnicodeDecodeError:
        return templates.TemplateResponse(
            request,
            name="partials/error.html",
            context={
                "message": "CSV must use UTF-8 encoding.",
            },
        )

    except Exception as error:
        return templates.TemplateResponse(
            request,
            name="partials/error.html",
            context={
                "message": str(error),
            },
        )


@app.get("/classify")
def classify_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="classify.html",
        context={},
    )


@app.post("/ui/classify")
def ui_classify(request: Request):
    try:
        classifier = GeminiClassifier()

        emails = classifier.load_emails_from_csv("data/buyers.csv")

        if not emails:
            return templates.TemplateResponse(
                request,
                name="partials/error.html",
                context={
                    "message": "No emails found in buyers.csv.",
                },
            )

        classifications = classifier.classify_in_batches(emails)

        business_emails = []
        individual_emails = []

        for email, category in classifications.items():
            if category == "business":
                business_emails.append(email)

            elif category == "individual":
                individual_emails.append(email)

        Path("data").mkdir(parents=True, exist_ok=True)

        with open(
            "data/business_emails.csv", "w", encoding="utf-8", newline=""
        ) as file:
            writer = csv.writer(file)

            writer.writerow(["email"])

            for email in business_emails:
                writer.writerow([email])

        with open(
            "data/individual_emails.csv", "w", encoding="utf-8", newline=""
        ) as file:
            writer = csv.writer(file)

            writer.writerow(["email"])

            for email in individual_emails:
                writer.writerow([email])

        result = {
            "total": len(emails),
            "business": len(business_emails),
            "individual": len(individual_emails),
        }

        return templates.TemplateResponse(
            request=request,
            name="partials/classify_result.html",
            context={
                "result": result,
            },
        )

    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": str(error),
            },
        )


@app.post("/api/classify")
def classify_buyers():
    try:
        classifier = GeminiClassifier()

        emails = classifier.load_emails_from_csv("data/buyers.csv")

        if not emails:
            return {
                "total": 0,
                "business": 0,
                "individual": 0,
            }

        classifications = classifier.classify_in_batches(emails)

        business_emails = []
        individual_emails = []

        for email, category in classifications.items():
            if category == "business":
                business_emails.append(email)

            elif category == "individual":
                individual_emails.append(email)

        with open(
            "data/business_emails.csv",
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow(["email"])

            for email in business_emails:
                writer.writerow([email])

        with open(
            "data/individual_emails.csv",
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow(["email"])

            for email in individual_emails:
                writer.writerow([email])

        return {
            "total": len(emails),
            "business": len(business_emails),
            "individual": len(individual_emails),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.get("/send")
def send_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="send.html",
        context={},
    )


@app.post("/ui/send")
async def ui_send(
    request: Request,
    audience: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    dry_run: bool = Form(False),
    attachment: UploadFile | None = File(None),
):
    if audience not in [
        "business",
        "individual",
        "all",
    ]:
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": ("Audience must be business, individual, or all."),
            },
        )

    attachment_path = None

    try:
        # =========================
        # ATTACHMENT
        # =========================

        if attachment and attachment.filename:
            if not attachment.filename.lower().endswith(".pdf"):
                return templates.TemplateResponse(
                    request=request,
                    name="partials/error.html",
                    context={
                        "message": ("Only PDF attachments are currently supported."),
                    },
                )

            upload_dir = Path("data/uploads")

            upload_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            attachment_path = upload_dir / attachment.filename

            content = await attachment.read()

            attachment_path.write_bytes(content)

        # =========================
        # SMTP
        # =========================

        smtp = None
        sender = None
        auth = None

        if not dry_run:
            from outreach.brevo_auth import BrevoAuth
            from outreach.brevo_sender import BrevoSender

            auth = BrevoAuth()

            smtp = auth.connect()

            sender = BrevoSender(
                smtp=smtp,
                sender_email=os.getenv("BREVO_SENDER_EMAIL"),
                sender_name=os.getenv(
                    "BREVO_SENDER_NAME",
                    "Export Automation",
                ),
                auth=auth,
            )

        # =========================
        # LOGGER
        # =========================

        activity_logger = ActivityLogger()

        # =========================
        # CAMPAIGN
        # =========================

        campaign = CampaignSender(
            sender=sender,
            logger=activity_logger,
            daily_limit=int(
                os.getenv(
                    "DAILY_SEND_LIMIT",
                    "100",
                )
            ),
            send_delay=float(
                os.getenv(
                    "SEND_DELAY",
                    "0",
                )
            ),
        )

        # =========================
        # EMAIL FILES
        # =========================

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
        # SEND
        # =========================

        for email_file in email_files:
            if not Path(email_file).exists():
                continue

            result = campaign.send_campaign(
                file_path=email_file,
                subject=subject,
                body=body,
                attachment=attachment_path,
                dry_run=dry_run,
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

        latest_send_result.update(total_result)

        return templates.TemplateResponse(
            request=request,
            name="partials/send_result.html",
            context={
                "result": total_result,
                "dry_run": dry_run,
            },
        )

    except Exception as error:
        if smtp:
            try:
                smtp.quit()
            except Exception:
                pass

        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": str(error),
            },
        )


@app.post("/api/send")
def send_campaign(request: SendRequest):
    attachment_path = None

    if request.attachment:
        attachment_path = Path(request.attachment)

        if attachment_path.suffix.lower() != ".pdf":
            raise HTTPException(
                status_code=400,
                detail="Attachment must be a PDF file",
            )

    if request.audience not in [
        "business",
        "individual",
        "all",
    ]:
        raise HTTPException(
            status_code=400,
            detail=("Audience must be 'business', 'individual', or 'all'"),
        )

    try:
        result = run_send(
            audience=request.audience,
            subject=request.subject,
            body=request.body,
            attachment_path=(str(attachment_path) if attachment_path else None),
            dry_run=request.dry_run,
        )

        latest_send_result.update(result)

        return {
            "audience": request.audience,
            "subject": request.subject,
            "body": request.body,
            "attachment": request.attachment,
            "dry_run": request.dry_run,
            **result,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.get("/upload")
def upload_page(request: Request):
    return templates.TemplateResponse(
        request,
        name="upload.html",
        context={
            "request": request,
        },
    )


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="CSV file is required",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed",
        )

    try:
        content = await file.read()

        text = content.decode("utf-8-sig")

        rows = list(csv.DictReader(text.splitlines()))

        if not rows:
            raise HTTPException(
                status_code=400,
                detail="CSV file is empty",
            )

        required_columns = {
            "email",
        }

        columns = set(rows[0].keys())

        missing = required_columns - columns

        if missing:
            raise HTTPException(
                status_code=400,
                detail=("Missing required column(s): " + ", ".join(missing)),
            )

        buyers_file = Path("data/buyers.csv")

        buyers_file.parent.mkdir(parents=True, exist_ok=True)

        existing = []

        if buyers_file.exists():
            with buyers_file.open("r", encoding="utf-8", newline="") as existing_file:
                existing = list(csv.DictReader(existing_file))

        fieldnames = [
            "email",
            "buyer_name",
            "company_name",
            "website",
            "country",
            "source_platform",
        ]

        combined = existing.copy()

        for row in rows:
            email = row.get("email", "").strip().lower()

            if not email:
                continue

            combined.append(
                {
                    "email": email,
                    "buyer_name": (row.get("buyer_name", "") or "").strip(),
                    "company_name": (row.get("company_name", "") or "").strip(),
                    "website": (row.get("website", "") or "").strip(),
                    "country": (row.get("country", "") or "").strip(),
                    "source_platform": (
                        row.get("source_platform", "Upload") or "Upload"
                    ).strip(),
                }
            )

        # Deduplicate by email
        unique = {}

        for row in combined:
            email = row["email"]

            if email not in unique:
                unique[email] = row

        with buyers_file.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fieldnames)

            writer.writeheader()

            writer.writerows(unique.values())

        return {
            "filename": file.filename,
            "uploaded_records": len(rows),
            "total_records": len(unique),
            "duplicates_removed": (len(combined) - len(unique)),
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV must use UTF-8 encoding",
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.get("/report")
def report_page(request: Request):
    try:
        generator = ReportGenerator()

        report = generator.generate(latest_send_result)

        send_history = []

        log_file = Path("data/sent_log.csv")

        if log_file.exists():
            with log_file.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)

                send_history = list(reader)

        return templates.TemplateResponse(
            request=request,
            name="report.html",
            context={
                "report": report,
                "result": latest_send_result,
                "send_history": send_history,
            },
        )

    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": str(error),
            },
        )


@app.get("/api/report")
def get_report():

    try:
        generator = ReportGenerator()

        report = generator.generate(latest_send_result)

        send_history = []

        log_file = Path("data/sent_log.csv")

        if log_file.exists():
            with log_file.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)

                send_history = list(reader)

        return {
            "result": latest_send_result,
            "report": report,
            "send_history": send_history,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.get("/download-report")
def download_report():

    log_file = Path("data/sent_log.csv")

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        [
            "email",
            "status",
            "timestamp",
        ]
    )

    if log_file.exists():
        with log_file.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                writer.writerow(
                    [
                        row.get("email", ""),
                        row.get("status", ""),
                        row.get("timestamp", ""),
                    ]
                )

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=campaign_report.csv"},
    )


@app.get("/settings")
def settings_page(request: Request):
    load_dotenv()

    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "daily_limit": os.getenv(
                "DAILY_SEND_LIMIT",
                "100",
            ),
            "send_delay": os.getenv(
                "SEND_DELAY",
                "2",
            ),
            "subject": os.getenv(
                "DEFAULT_EMAIL_SUBJECT",
                "Singing Bowls Company Presentation",
            ),
            "body": os.getenv(
                "DEFAULT_EMAIL_BODY",
                """Hello,

We are an export supplier of Himalayan Singing Bowls.

Please find our company presentation attached.

If you are interested in our products,
please feel free to contact us.

Best regards,
Export Automation""",
            ),
        },
    )


@app.post("/ui/settings")
def save_settings(
    request: Request,
    daily_limit: int = Form(...),
    send_delay: float = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
):
    if daily_limit < 1:
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": "Daily send limit must be at least 1.",
            },
        )

    if send_delay < 0:
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": "Send delay cannot be negative.",
            },
        )

    if not subject.strip():
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": "Subject cannot be empty.",
            },
        )

    if not body.strip():
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={
                "message": "Email body cannot be empty.",
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="partials/settings_result.html",
        context={
            "message": ("Settings are ready to be saved."),
        },
    )
