# Export Automation System

Automation pipeline untuk membantu proses **buyer discovery dan export outreach** untuk produk.

Project ini menggabungkan pencarian buyer berbasis keyword, ekstraksi data kontak dari website, validasi email, klasifikasi email menggunakan Gemini, simulasi campaign, serta pengiriman email melalui Brevo SMTP.

> **Status:** Prototype / Internship Mini Project

## ✨ Fitur Utama

- 🔎 **Buyer Discovery** — mencari website berdasarkan keyword menggunakan Tavily.
- 📧 **Email Extraction** — mengekstrak alamat email dari konten website.
- 🏢 **Company Extraction** — mengambil nama perusahaan dari metadata/title website jika tersedia.
- ✅ **Email Validation** — memvalidasi format email sebelum masuk pipeline.
- 🤖 **AI Classification** — Gemini mengelompokkan email menjadi `business` atau `individual`.
- 📎 **PDF Attachment** — company presentation dapat dilampirkan pada campaign.
- 🛡️ **Duplicate Prevention** — email yang sudah berhasil dikirim dilewati berdasarkan `sent_log.csv`.
- 🧪 **Dry Run** — menguji target campaign tanpa mengirim email.
- 📊 **Reporting** — membuat laporan campaign sederhana.
- 📬 **Brevo SMTP** — digunakan sebagai SMTP provider pengiriman email.

## 🧩 Workflow

```text
Keyword
   ↓
Tavily Search
   ↓
Website Results
   ↓
Website Fetch
   ↓
Data Extraction
   ├── Email
   ├── Company
   └── Website
   ↓
Email Validation
   ↓
buyers.csv
   ↓
Gemini Classification
   ├── business_emails.csv
   └── individual_emails.csv
            ↓
        Campaign
            ↓
      ┌─────┴─────┐
      │           │
   Dry Run      Live
      │           │
      │        Brevo SMTP
      │           │
      └─────┬─────┘
            ↓
       sent_log.csv
            ↓
         Report
```

## 📁 Project Structure

```text
export-automation-system/
├── activity_logging/
├── classification/
├── extraction/
├── outreach/
├── reports/
├── search/
├── validation/
├── assets/
│   └── company_presentation.pdf
├── data/
│   ├── buyers.csv
│   ├── business_emails.csv
│   ├── individual_emails.csv
│   └── sent_log.csv
├── app.py
├── config.py
├── main.py
├── requirements.txt
├── .env
└── README.md
```

## ⚙️ Requirements

- Python 3.10+
- Internet connection
- Tavily API key
- Gemini API key
- Brevo SMTP account

Project ini menggunakan Python virtual environment (`.venv`).

## 🚀 Installation

### 1. Clone repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd export-automation-system
```

### 2. Buat virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔐 Environment Variables

copy file `.env.example` ke `.env` dan isi sesuai kebutuhan .


# 🖥️ CLI

Untuk melihat command yang tersedia:

```bash
python main.py
```

## 🔎 1. Search Buyer

Cari buyer berdasarkan keyword:

```bash
python main.py search --query "singing bowls suppliers"
```

Hasil discovery disimpan ke:

```text
data/buyers.csv
```

Schema:

```text
email
buyer_name
company_name
website
country
source_platform
```

Contoh output:

```text
Mencari: singing bowls suppliers
Menggunakan Tavily...

[1/5] Mengambil: https://example.com
  Email ditemukan : 1
  Email valid     : 1

=== SEARCH RESULT ===
Search results : 5
Total records  : 3
Valid emails   : 3
Invalid emails : 0
```

## 🤖 2. Classify Email

```bash
python main.py classify
```

Gemini mengklasifikasikan email menjadi:

```text
business
individual
```

Output:

```text
data/business_emails.csv
data/individual_emails.csv
```

## 🧪 3. Dry Run

Disarankan menjalankan dry-run sebelum campaign live.

```bash
python main.py send --audience business --dry-run
python main.py send --audience individual --dry-run
python main.py send --audience all --dry-run
```

Contoh:

```text
[DRY RUN] Would send to: buyer@example.com

=== SEND RESULT ===
Mode    : DRY RUN
Total   : 1
Sent    : 1
Skipped : 0
Failed  : 0
```

Dry run **tidak mengirim email** dan tidak mencatat recipient sebagai `sent`.

## 📬 4. Live Send

Jika sudah melakukan review dan memang siap mengirim:

```bash
python main.py send --audience business
python main.py send --audience individual
python main.py send --audience all
```

Pengiriman menggunakan Brevo SMTP.

Histori pengiriman disimpan di:

```text
data/sent_log.csv
```

## 📊 5. Report

```bash
python main.py report
```

Report tersimpan di:

```text
reports/latest_report.txt
```

## 🛡️ Duplicate Prevention

Sistem menggunakan `data/sent_log.csv` sebagai histori pengiriman.

Contoh:

```csv
email,status,timestamp
buyer@example.com,sent,2026-08-15T22:48:46
```

Jika email yang sama muncul lagi:

```text
SKIP: buyer@example.com sudah pernah dikirim.
```

## 📎 Company Presentation

Attachment campaign berada di:

```text
assets/company_presentation.pdf
```

Path dapat dikonfigurasi melalui:

```env
PRESENTATION_PATH=assets/company_presentation.pdf
```

## 🧱 Architecture

Project menggunakan pendekatan modular agar komponen dapat diuji dan diganti secara independen.

```text
Search
  ↓
Extraction
  ↓
Validation
  ↓
Classification
  ↓
Campaign
  ↓
Logging
  ↓
Reporting
```

Search menggunakan adapter sehingga provider dapat dikembangkan tanpa mengubah seluruh pipeline:

```text
SearchAdapter
     │
     ├── TavilySearch
     └── WebsiteSearch
```

## ⚠️ Limitations

Versi saat ini masih merupakan prototype.

- Tidak semua website menyediakan email publik.
- Struktur HTML website berbeda-beda.
- `buyer_name` belum selalu tersedia.
- Informasi `country` masih membutuhkan enrichment yang lebih akurat.
- Hasil klasifikasi AI tetap perlu direview.
- CSV kurang ideal untuk data skala besar.
- Search result bergantung pada provider dan struktur website.
- Belum terdapat dashboard web.
- Belum terdapat CRM integration.
- Belum terdapat reply tracking.
- Belum terdapat unsubscribe/consent workflow.

Untuk penggunaan commercial outreach skala besar, sistem perlu dilengkapi mekanisme compliance, consent/unsubscribe, dan pengelolaan data yang sesuai regulasi.

## 🔮 Future Improvements

- [ ] Google Search adapter
- [ ] Business directory adapter
- [ ] Additional search sources
- [ ] Contact/About page enrichment
- [ ] Buyer name extraction
- [ ] Country extraction yang lebih akurat
- [ ] Personalized email generation
- [ ] Web dashboard
- [ ] Campaign scheduling
- [ ] Reply tracking
- [ ] CRM export
- [ ] SQLite/PostgreSQL storage
- [ ] Background task queue
- [ ] Authentication dan role management
- [ ] Unsubscribe dan consent management

## 🧪 Development Workflow

```text
1. Search
   ↓
2. Review buyers.csv
   ↓
3. Classify
   ↓
4. Review business/individual CSV
   ↓
5. Dry Run
   ↓
6. Review target recipients
   ↓
7. Live Send
   ↓
8. Report
```

Untuk testing, gunakan `--dry-run` terlebih dahulu sebelum campaign live.

## 📌 Project Goal

Project ini dibuat sebagai **mini project internship** untuk menunjukkan kemampuan dalam:

- Python development
- API integration
- Web data extraction
- Email validation
- AI API integration
- SMTP integration
- CSV data processing
- Modular software architecture
- CLI application development
- Automation workflow

## License

This project is developed for educational purposes.
