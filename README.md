# Ganesh Utsav 2026 — Donation Management App

A lightweight Streamlit application for collecting and managing Ganesh Utsav donations in a housing society. Designed to be fast and easy to use on a mobile phone.

---

## Features

- **Collect Donation** — Fill a simple form, generate a receipt instantly
- **Auto-numbered receipts** — `GU2026-0001`, `GU2026-0002`, …
- **Google Sheets records** — All donations saved to a Google Sheet (persists across restarts/redeploys)
- **PDF receipt** — Professional A5 receipt, downloadable on-screen
- **SMS with receipt link** — Donor receives a link to view their receipt anytime
- **Donation Records** — Searchable table with summary stats and Excel export

---

## Project Structure

```
ganesh-donations/
├── app.py                      # Entry point & router
├── views/
│   ├── collect_donation.py     # Donation form
│   ├── donation_records.py     # Records table & stats
│   └── receipt_view.py         # Digital receipt (SMS link target)
├── utils/
│   ├── sheets_manager.py       # Read/write the Google Sheet
│   ├── pdf_generator.py        # ReportLab PDF generation
│   ├── sms_service.py          # MSG91 / Twilio SMS
│   └── receipt_generator.py    # Receipt number & URL helpers
├── receipts/                   # Generated PDF receipts (auto-created)
├── assets/                     # Optional: place society logo here
├── .env                        # Your credentials (never commit this)
├── .env.example                # Template — copy to .env
├── .streamlit/
│   ├── secrets.toml            # Google service account + sheet ID (never commit this)
│   └── secrets.toml.example    # Template — copy to secrets.toml
└── requirements.txt
```

---

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the app

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```env
SOCIETY_NAME=Shree XYZ Housing Society
APP_BASE_URL=http://localhost:8501    # Change this for production
SMS_PROVIDER=none                     # Set to msg91 or twilio when ready
```

### 3. Connect Google Sheets (donation storage)

Donation records are stored in a Google Sheet via a service account, so they
persist across app restarts/redeploys.

1. In the [Google Cloud Console](https://console.cloud.google.com/), create
   a project (or use an existing one) and enable the **Google Sheets API**
   and **Google Drive API**.
2. Create a **Service Account** (IAM & Admin → Service Accounts), then
   create a JSON key for it and download it.
3. Create a new Google Sheet (any name). Share it with the service
   account's `client_email` (found in the JSON key) as **Editor**.
4. Copy the spreadsheet ID from its URL:
   `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`
5. Copy the template and fill in your values:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
   Paste the fields from your downloaded JSON key into `[gcp_service_account]`,
   and your spreadsheet ID into `[sheets] spreadsheet_id`.

The app creates a `Donations` worksheet with the correct headers
automatically on first use — no manual header setup needed.

### 4. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser (or share the LAN IP with volunteers).

---

## SMS Setup

### Option A — MSG91 (Recommended for India)

1. Sign up at [msg91.com](https://msg91.com)
2. Create an SMS Flow template with these variables:
   - `{{receipt_number}}`
   - `{{amount}}`
   - `{{receipt_url}}`

   Example template:
   ```
   Thank you for your contribution towards Ganesh Utsav 2026!
   Receipt No: {{receipt_number}}
   Amount: {{amount}}
   View your receipt: {{receipt_url}}
   ```

3. Set in `.env`:
   ```env
   SMS_PROVIDER=msg91
   MSG91_AUTH_KEY=your_auth_key
   MSG91_SENDER_ID=GNUTSV
   MSG91_TEMPLATE_ID=your_template_id
   ```

### Option B — Twilio

1. Sign up at [twilio.com](https://twilio.com)
2. Get a Twilio phone number
3. Install the SDK: `pip install twilio`
4. Set in `.env`:
   ```env
   SMS_PROVIDER=twilio
   TWILIO_ACCOUNT_SID=ACxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_FROM_NUMBER=+1234567890
   ```

---

## Receipt URL

When a donation is collected, an SMS is sent with a link like:

```
http://localhost:8501/?receipt=GU2026-0001
```

For production, replace `APP_BASE_URL` in `.env` with your public domain:

```env
APP_BASE_URL=https://donations.yoursociety.com
```

The receipt page shows all donation details and a **Download PDF** button.
The link works permanently as long as the Google Sheet record is not deleted.

---

## Running on a Local Network (for volunteers)

To let multiple volunteers use the app from their phones on the same Wi-Fi:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Share your machine's local IP (e.g. `http://192.168.1.10:8501`) with volunteers.

---

## Production Deployment

For 24/7 availability so SMS receipt links always work, deploy to:

- **Streamlit Community Cloud** — free, simple
- **Railway / Render** — easy Docker-based hosting
- **Any VPS** — run with `nohup streamlit run app.py &`

Wherever you deploy, set the contents of `.streamlit/secrets.toml` as that
platform's secrets (on Streamlit Community Cloud: App settings → Secrets).
Donation data itself lives in Google Sheets, so it survives restarts/redeploys
without any extra file syncing. PDF receipts in `receipts/` are still local
to the server's filesystem and won't survive a redeploy on ephemeral hosts.

---

## Notes

- The `Donations` worksheet and `receipts/` are created automatically on first run.
- PDF receipts are stored in `receipts/GU2026-XXXX.pdf`.
- Never commit `.env` or `.streamlit/secrets.toml` to version control. Both are in `.gitignore`.
- If two volunteers submit at the exact same millisecond, there is a small
  risk of a duplicate receipt number. For a society event, this is negligible.
