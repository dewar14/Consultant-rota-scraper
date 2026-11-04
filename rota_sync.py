#!/usr/bin/env python3
"""
Consultant Rota Scraper & Google Calendar Sync

Reads a Google Sheets consultant rota, identifies shifts for "Alex",
and creates/manages all-day events in Google Calendar.
"""

import os
import sys
import logging
from datetime import date, timedelta, datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SPREADSHEET_ID = "1KHA3mulQekbj8L1AiLTggcUjlqcm7-Z4TsNTgR_u_5s"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/calendar",
]
WEEKS_AHEAD = 16
EVENT_DESCRIPTION = "Scraped from RITA rota"

# Your first name as it appears in the rota. Override via MY_NAME env var.
# Note: use `or` rather than a default, so an empty-string env var (which is
# what GitHub Actions passes through when a secret is unset) still falls back.
MY_NAME = (os.environ.get("MY_NAME") or "Alex").strip()
if not MY_NAME:
    sys.exit("ERROR: MY_NAME is empty after stripping; refusing to run (would match every name).")

# Calendar ID: must be set to your actual Google account email address.
# "primary" would refer to the SERVICE ACCOUNT's own calendar, not yours.
# Override via the CALENDAR_ID environment variable.
CALENDAR_ID = os.environ.get("CALENDAR_ID", "primary")

# Google Calendar colour IDs
COLOR_SERVICE = "6"   # orange
COLOR_ONCALL = "11"   # red
COLOR_COMET = "5"     # yellow

# RGB thresholds for gold/amber/bronze text (planned shift)
# Actual observed value in this rota: (127, 96, 0)
GOLD_R_MIN, GOLD_R_MAX = 100, 220
GOLD_G_MIN, GOLD_G_MAX = 70, 180
GOLD_B_MIN, GOLD_B_MAX = 0, 80

# RGB threshold for black text (locum shift)
BLACK_MAX = 50

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def get_credentials():
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if not creds_path:
        sys.exit("ERROR: Set GOOGLE_CREDENTIALS_PATH to the service account JSON key file.")
    if not os.path.isfile(creds_path):
        sys.exit(f"ERROR: Credentials file not found: {creds_path}")
    return Credentials.from_service_account_file(creds_path, scopes=SCOPES)


# ---------------------------------------------------------------------------
# Sheets helpers
# ---------------------------------------------------------------------------

MONTH_ABBR = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def parse_date_cell(value: str) -> date | None:
    """Parse date string like 'Monday-28Apr26' into a date object."""
    if not value or "-" not in value:
        return None
    try:
        # Strip day name: take everything after the first hyphen
        after_dash = value.split("-", 1)[1]
        # Extract day digits, month abbreviation, year digits
        day_str = ""
        i = 0
        while i < len(after_dash) and after_dash[i].isdigit():
            day_str += after_dash[i]
            i += 1
        month_str = after_dash[i:i+3]
        year_str = after_dash[i+3:]
        day = int(day_str)
        month = MONTH_ABBR.get(month_str)
        if month is None:
            return None
        year = 2000 + int(year_str)
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def rank_tabs(tab_names: list[str]) -> list[str]:
    """Order tab names from most to least likely to hold the live rota.

    The rota itself lives on a tab called "RITA". Other tabs (e.g. "PLAN 2026")
    can carry the current year in their name but hold summaries, so a year in
    the name is only a weak hint. Every tab is returned; the caller validates
    each one in turn and uses the first that actually looks like the rota.
    """
    def score(name: str) -> int:
        lower = name.lower().strip()
        if lower == "rita":
            return 0
        if "rita" in lower:
            return 1
        if "rota" in lower:
            return 2
        if any(str(y) in lower for y in (date.today().year, date.today().year + 1)):
            return 3
        return 4

    # sorted() is stable, so ties keep the spreadsheet's own tab order.
    return sorted(tab_names, key=score)


def find_header_row(row_data: list[dict]) -> int | None:
    """Return the index of the first row (within 50) that has a 'Service' cell."""
    for scan_idx in range(min(50, len(row_data))):
        scan_cells = row_data[scan_idx].get("values", [])
        scan_texts = [get_cell_text(c).lower().strip() for c in scan_cells]
        if "service" in scan_texts:
            return scan_idx
    return None


def load_rota_tab(sheets_service, today: date, end_date: date):
    """Find and load the tab holding the rota.

    A tab only counts if its header row has Service, OnCall and CoMET columns
    AND it has at least one parseable date inside the sync window. This stops a
    look-alike tab (a summary, last year's plan) from being used, which would
    otherwise make every existing calendar event look stale.

    Returns (tab_name, row_data, header_row_idx, columns) or None.
    """
    meta = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    tab_names = [s["properties"]["title"] for s in meta.get("sheets", [])]
    log.info(f"Available tabs: {tab_names}")

    for tab_name in rank_tabs(tab_names):
        resp = sheets_service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID,
            ranges=[tab_name],
            includeGridData=True,
        ).execute()
        row_data = resp["sheets"][0]["data"][0].get("rowData", [])

        header_row_idx = find_header_row(row_data)
        if header_row_idx is None:
            log.info(f"Skipping tab '{tab_name}': no header row containing 'Service'")
            continue

        columns = identify_columns(row_data[header_row_idx].get("values", []))
        missing = [k for k in ("service", "oncall_cols", "comet_cols") if k not in columns]
        if missing:
            log.info(f"Skipping tab '{tab_name}': header row lacks {missing}")
            continue

        dated_rows = 0
        for row in row_data[header_row_idx + 1:]:
            cells = row.get("values", [])
            row_date = parse_date_cell(get_cell_text(cells[0])) if cells else None
            if row_date and today <= row_date < end_date:
                dated_rows += 1
        if dated_rows == 0:
            log.info(f"Skipping tab '{tab_name}': no dates between {today} and {end_date}")
            continue

        log.info(f"Selected tab: {tab_name} ({dated_rows} dated rows in range)")
        return tab_name, row_data, header_row_idx, columns

    return None


def get_rgb(color_dict: dict) -> tuple[int, int, int]:
    """Extract RGB 0-255 from Sheets API color object (0.0-1.0 floats)."""
    r = int(color_dict.get("red", 0) * 255)
    g = int(color_dict.get("green", 0) * 255)
    b = int(color_dict.get("blue", 0) * 255)
    return r, g, b


def is_gold(r, g, b) -> bool:
    return GOLD_R_MIN <= r <= GOLD_R_MAX and GOLD_G_MIN <= g <= GOLD_G_MAX and GOLD_B_MIN <= b <= GOLD_B_MAX


def is_black(r, g, b) -> bool:
    return r < BLACK_MAX and g < BLACK_MAX and b < BLACK_MAX


def has_strikethrough(cell_data: dict) -> bool:
    """Check if any text run in a cell has strikethrough."""
    fmt = cell_data.get("effectiveFormat", {}).get("textFormat", {})
    if fmt.get("strikethrough"):
        return True
    # Check text format runs
    for run in cell_data.get("textFormatRuns", []):
        if run.get("format", {}).get("strikethrough"):
            return True
    return False


def get_cell_text(cell_data: dict) -> str:
    """Get the plain text value from a cell."""
    return (cell_data.get("effectiveValue", {}).get("stringValue", "") or
            cell_data.get("formattedValue", "") or "").strip()


def get_cell_text_color(cell_data: dict) -> tuple[int, int, int]:
    """Get the foreground text colour of a cell."""
    fmt = cell_data.get("effectiveFormat", {})
    color = fmt.get("textFormat", {}).get("foregroundColorStyle", {}).get("rgbColor",
            fmt.get("textFormat", {}).get("foregroundColor", {}))
    return get_rgb(color)


def identify_columns(header_cells: list[dict]) -> dict:
    """Map column header names to indices."""
    columns = {}
    for idx, cell in enumerate(header_cells):
        text = get_cell_text(cell).lower().strip()
        if text == "service":
            columns["service"] = idx
        elif text == "oncall" or text == "on call" or text == "on-call":
            columns.setdefault("oncall_cols", []).append(idx)
        elif text == "weekend":
            # Weekend on-calls sit in their own column, labelled "weekend"
            # in the RITA tab header row.
            columns.setdefault("oncall_cols", []).append(idx)
        elif "comet" in text:
            columns.setdefault("comet_cols", []).append(idx)
        elif text == "bckp":
            columns["bckp"] = idx
        elif text == "cbck":
            columns["cbck"] = idx

    # Treat any unlabeled column immediately following OnCall as a
    # secondary OnCall column (used for weekend on-calls in the RITA tab).
    if "oncall_cols" in columns:
        primary_oncall = columns["oncall_cols"][0]
        next_idx = primary_oncall + 1
        if next_idx < len(header_cells):
            next_text = get_cell_text(header_cells[next_idx]).strip()
            if not next_text and next_idx not in columns["oncall_cols"]:
                columns["oncall_cols"].append(next_idx)

    # Likewise, weekend CoMET shifts are written one column to the right of
    # the labelled CoMET columns (into the unlabeled spacer columns). Add the
    # unlabeled column immediately following each CoMET column so they're
    # scanned too. Mirrors the weekend on-call handling above.
    if "comet_cols" in columns:
        for comet_idx in list(columns["comet_cols"]):
            next_idx = comet_idx + 1
            if next_idx >= len(header_cells):
                continue
            next_text = get_cell_text(header_cells[next_idx]).strip()
            if not next_text and next_idx not in columns["comet_cols"]:
                columns["comet_cols"].append(next_idx)

    log.info(f"Identified columns: {columns}")
    return columns


def contains_alex(text: str) -> bool:
    """Check if cell text contains MY_NAME (case-insensitive partial match)."""
    if not MY_NAME or not text:
        return False
    return MY_NAME.lower() in text.lower()


# ---------------------------------------------------------------------------
# Shift detection
# ---------------------------------------------------------------------------


def detect_shift(row_cells: list[dict], columns: dict, row_date: date) -> tuple[str, str] | None:
    """
    Detect if Alex has a shift on this row.

    Returns (event_title, color_id) or None.
    """
    shift_type_map = {
        "service": ("Service", COLOR_SERVICE),
        "oncall": ("On Call", COLOR_ONCALL),
    }

    # 1. Check Service, OnCall, CoMET columns for Alex's name
    check_cols = []
    if "service" in columns:
        check_cols.append(("service", columns["service"]))
    for oncall_idx in columns.get("oncall_cols", []):
        check_cols.append(("oncall", oncall_idx))
    for comet_idx in columns.get("comet_cols", []):
        check_cols.append(("comet", comet_idx))

    for col_type, col_idx in check_cols:
        if col_idx >= len(row_cells):
            continue
        cell = row_cells[col_idx]
        text = get_cell_text(cell)
        if not contains_alex(text):
            continue

        r, g, b = get_cell_text_color(cell)
        log.info(f"  {row_date}: Found '{text}' in {col_type} col, RGB=({r},{g},{b})")

        if col_type == "comet":
            base_title = "CoMET"
            color_id = COLOR_COMET
        else:
            base_title, color_id = shift_type_map[col_type]

        if is_gold(r, g, b):
            return (base_title, color_id)
        elif is_black(r, g, b):
            return (f"{base_title} (Locum)", color_id)
        else:
            # Unknown colour - log and treat as planned
            log.warning(f"  {row_date}: Unexpected text colour RGB=({r},{g},{b}) for '{text}', treating as planned shift")
            return (base_title, color_id)

    # 2. Check Bckp column
    if "bckp" in columns:
        bckp_idx = columns["bckp"]
        if bckp_idx < len(row_cells):
            cell = row_cells[bckp_idx]
            text = get_cell_text(cell)
            if contains_alex(text):
                log.info(f"  {row_date}: Found '{text}' in Bckp column")
                # Determine which shift is being covered by checking strikethrough
                # in Service and OnCall columns
                covered_type = None
                if "service" in columns and columns["service"] < len(row_cells):
                    if has_strikethrough(row_cells[columns["service"]]):
                        covered_type = "Service"
                if covered_type is None:
                    for oncall_idx in columns.get("oncall_cols", []):
                        if oncall_idx < len(row_cells) and has_strikethrough(row_cells[oncall_idx]):
                            covered_type = "On Call"
                            break
                if covered_type is None:
                    # Default to Service if can't determine
                    covered_type = "Service"
                    log.warning(f"  {row_date}: Could not determine covered shift type from strikethrough, defaulting to Service")
                color_id = COLOR_SERVICE if covered_type == "Service" else COLOR_ONCALL
                return (f"{covered_type} (Locum)", color_id)

    # 3. Check CBCK column
    if "cbck" in columns:
        cbck_idx = columns["cbck"]
        if cbck_idx < len(row_cells):
            cell = row_cells[cbck_idx]
            text = get_cell_text(cell)
            if contains_alex(text):
                log.info(f"  {row_date}: Found '{text}' in CBCK column")
                return ("CoMET (Locum)", COLOR_COMET)

    return None


# ---------------------------------------------------------------------------
# Calendar helpers
# ---------------------------------------------------------------------------


def get_existing_rota_events(cal_service, start_date: date, end_date: date) -> dict[str, list[dict]]:
    """
    Fetch all calendar events in the date range that have our description.
    Returns a dict mapping ISO date string -> list of matching events.
    """
    events_by_date: dict[str, list[dict]] = {}
    time_min = datetime(start_date.year, start_date.month, start_date.day).isoformat() + "Z"
    time_max = datetime(end_date.year, end_date.month, end_date.day).isoformat() + "Z"

    page_token = None
    while True:
        result = cal_service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            maxResults=250,
            pageToken=page_token,
        ).execute()
        for event in result.get("items", []):
            if event.get("description") == EVENT_DESCRIPTION:
                event_date = event.get("start", {}).get("date")
                if event_date:
                    events_by_date.setdefault(event_date, []).append(event)
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return events_by_date


def create_event(cal_service, event_date: date, title: str, color_id: str):
    """Create an all-day calendar event."""
    body = {
        "summary": title,
        "description": EVENT_DESCRIPTION,
        "start": {"date": event_date.isoformat()},
        "end": {"date": (event_date + timedelta(days=1)).isoformat()},
        "colorId": color_id,
    }
    cal_service.events().insert(calendarId=CALENDAR_ID, body=body).execute()
    log.info(f"  CREATED: {event_date} - {title}")


def delete_event(cal_service, event: dict):
    """Delete a calendar event."""
    cal_service.events().delete(calendarId=CALENDAR_ID, eventId=event["id"]).execute()
    log.info(f"  DELETED: {event.get('start', {}).get('date')} - {event.get('summary')}")


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------


def main():
    log.info("=" * 60)
    log.info("Consultant Rota Sync - Starting")
    log.info("=" * 60)

    creds = get_credentials()
    sheets_service = build("sheets", "v4", credentials=creds)
    cal_service = build("calendar", "v3", credentials=creds)

    # Determine date range
    today = date.today()
    end_date = today + timedelta(weeks=WEEKS_AHEAD)
    log.info(f"Processing date range: {today} to {end_date}")

    # Find and load the tab holding the rota (validated, see load_rota_tab)
    loaded = load_rota_tab(sheets_service, today, end_date)
    if loaded is None:
        log.error(
            "No tab looks like the rota (needs Service/OnCall/CoMET headers and "
            "dates in range). Calendar left untouched."
        )
        sys.exit(1)
    tab_name, row_data, header_row_idx, columns = loaded

    header_texts = [get_cell_text(c) for c in row_data[header_row_idx].get("values", [])]
    log.info(f"Header row index: {header_row_idx}")
    log.info(f"Header row: {header_texts}")

    # Log first 5 data rows after header for debugging
    data_start = header_row_idx + 1
    for dbg_idx in range(data_start, min(data_start + 5, len(row_data))):
        dbg_row = row_data[dbg_idx]
        dbg_cells = dbg_row.get("values", [])
        if dbg_cells:
            col_a = get_cell_text(dbg_cells[0])
            log.info(f"  Row {dbg_idx} col A: '{col_a}'")

    # Process each row to find Alex's shifts
    shifts: dict[date, tuple[str, str]] = {}  # date -> (title, color_id)
    unparsed_dates = 0

    for row_idx in range(data_start, len(row_data)):
        row = row_data[row_idx]
        cells = row.get("values", [])
        if not cells:
            continue

        # Parse date from column A
        date_text = get_cell_text(cells[0]) if cells else ""
        row_date = parse_date_cell(date_text)
        if row_date is None:
            if date_text.strip():
                unparsed_dates += 1
            continue

        # Only process dates in our window
        if row_date < today or row_date >= end_date:
            continue

        shift = detect_shift(cells, columns, row_date)
        if shift:
            shifts[row_date] = shift
        else:
            # Diagnostic safety net: if our name appears anywhere on a row we
            # didn't classify as a shift, log which column it's in. This makes
            # mis-placed entries (e.g. unexpected weekend layouts) obvious from
            # the logs instead of silently vanishing.
            for ci, cell in enumerate(cells):
                cell_text = get_cell_text(cell)
                if contains_alex(cell_text):
                    log.warning(
                        f"  {row_date}: '{cell_text}' present in UNMATCHED column "
                        f"{ci} - not classified as a shift (check column mapping)"
                    )

    if unparsed_dates > 0:
        log.warning(f"Could not parse {unparsed_dates} non-empty date cells - date format may differ from expected 'Monday-28Apr26'")
    log.info(f"\nFound {len(shifts)} shifts in date range")

    # Fetch existing rota events from calendar
    existing = get_existing_rota_events(cal_service, today, end_date)

    # Safety net: finding no shifts at all over the whole window while the
    # calendar has rota events almost always means the sheet was misread
    # (wrong tab, moved columns, renamed person), not that every shift was
    # cancelled. Refuse to wipe the calendar in that case.
    if not shifts and any(existing.values()):
        log.error(
            f"Found 0 shifts for '{MY_NAME}' but the calendar has existing rota "
            "events. Refusing to delete them - check the tab, column headers and "
            "MY_NAME. Calendar left untouched."
        )
        sys.exit(1)

    # Sync: iterate over each date in the window
    current = today
    while current < end_date:
        date_str = current.isoformat()
        existing_events = existing.get(date_str, [])
        desired = shifts.get(current)

        if desired:
            title, color_id = desired
            # Find matching events and stale events on this date
            matching = [ev for ev in existing_events
                        if ev.get("summary") == title and ev.get("colorId") == color_id]
            stale = [ev for ev in existing_events if ev not in matching]

            # Delete all stale rota events
            for ev in stale:
                delete_event(cal_service, ev)

            if matching:
                # Keep one matching event, delete duplicates
                log.info(f"  SKIPPED (exists): {date_str} - {title}")
                for dup in matching[1:]:
                    delete_event(cal_service, dup)
            else:
                # Create the correct event
                create_event(cal_service, current, title, color_id)
        else:
            # No shift on this date - delete any stale rota events
            for ev in existing_events:
                delete_event(cal_service, ev)
                log.info(f"  REMOVED stale event: {date_str} - {ev.get('summary')}")

        current += timedelta(days=1)

    log.info("\nSync complete.")


if __name__ == "__main__":
    main()
