# Consultant Rota Scraper & Calendar Sync

Reads a Google Sheets consultant rota and creates/manages all-day events in Google Calendar.

## How It Works

1. Reads the rota spreadsheet (identifies the correct year tab automatically)
2. Finds rows where "Alex" is assigned a shift (Service, On Call, or CoMET)
3. Distinguishes planned shifts (gold/amber text) from locum shifts (black text or Bckp/CBCK columns)
4. Creates colour-coded all-day events in Google Calendar
5. Idempotent: re-running won't duplicate events; stale events are removed

## Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the following APIs:
   - **Google Sheets API** — search "Sheets" in the API Library
   - **Google Calendar API** — search "Calendar" in the API Library

### 2. Create a Service Account

1. Go to **IAM & Admin → Service Accounts**
2. Click **Create Service Account**
3. Give it a name (e.g. `rota-scraper`)
4. No additional roles are needed at project level
5. Click **Done**
6. Click on the service account → **Keys** tab → **Add Key → Create new key → JSON**
7. Save the downloaded JSON file somewhere secure (e.g. `~/.config/rota-scraper/credentials.json`)

### 3. Share the Spreadsheet

1. Open the rota spreadsheet in Google Sheets
2. Click **Share**
3. Add the service account email (found in the JSON key file as `client_email`, e.g. `rota-scraper@your-project.iam.gserviceaccount.com`)
4. Grant **Viewer** access

### 4. Share Your Google Calendar

This is the critical step for service accounts writing to your calendar:

1. Open [Google Calendar](https://calendar.google.com/)
2. Find your calendar in the left sidebar → click the three dots → **Settings and sharing**
3. Scroll to **Share with specific people or groups**
4. Add the service account email
5. Set permission to **Make changes to events**

> **Note:** If you'd rather not share your calendar with a service account, you can switch to OAuth2 user credentials instead. The script would need minor modifications to use `InstalledAppFlow` from `google_auth_oauthlib`.

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Set Environment Variable

```bash
export GOOGLE_CREDENTIALS_PATH="$HOME/.config/rota-scraper/credentials.json"
```

### 7. Run

```bash
python rota_sync.py
```

## Automated Daily Sync (Cron)

Edit your crontab:

```bash
crontab -e
```

Add a line to run daily at 7am:

```cron
0 7 * * * GOOGLE_CREDENTIALS_PATH=/home/youruser/.config/rota-scraper/credentials.json /usr/bin/python3 /path/to/rota_sync.py >> /var/log/rota_sync.log 2>&1
```

## Colour Coding

| Shift Type | Calendar Colour | colorId |
|---|---|---|
| Service / Service (Locum) | Orange | 6 |
| On Call / On Call (Locum) | Red | 11 |
| CoMET / CoMET (Locum) | Yellow | 5 |

## Troubleshooting

- **403 on Calendar write**: Ensure you shared the calendar with the service account email with "Make changes to events" permission.
- **403 on Sheets read**: Ensure you shared the spreadsheet with the service account email.
- **Wrong shifts detected**: On first run, the script logs RGB values for cells containing "Alex". Check these match the expected gold/amber range (R: 180-210, G: 130-160, B: 0-50). Adjust thresholds in the script if needed.
- **No tab found**: The script looks for tab names containing "25-26" or "2026". Check your spreadsheet tab names.

## Configuration

Key constants at the top of `rota_sync.py`:

- `SPREADSHEET_ID` — the Google Sheets document ID
- `WEEKS_AHEAD` — how far ahead to process (default: 8 weeks)
- `GOLD_R_MIN/MAX`, `GOLD_G_MIN/MAX`, `GOLD_B_MIN/MAX` — RGB thresholds for gold/amber text
- `MY_NAME` — the name to search for in the rota (default: "Alex")
