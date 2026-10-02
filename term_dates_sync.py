#!/usr/bin/env python3
"""
School Term Dates -> Google Calendar Sync

Scrapes the Nottingham Girls' High School term-dates page and keeps all-day
events in Google Calendar up to date. Every academic year listed on the page is
synced, so new years appear automatically once the school publishes them.

Idempotent: events are tagged with a private extended property and matched by
key, so re-running creates nothing new, updates anything the school has changed,
and removes future events that have disappeared from the page. Past events are
never deleted.

Fails loudly (non-zero exit) if the page layout changes in a way we can't parse,
rather than silently syncing wrong dates.

Usage: python term_dates_sync.py [--dry-run]
"""

import html
import os
import re
import sys
import logging
from datetime import date, datetime, timedelta

import requests

TERM_DATES_URL = "https://nottinghamgirls.gdst.net/admissions/term-dates"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.environ.get("CALENDAR_ID", "primary")

EVENT_PREFIX = "School: "
EVENT_DESCRIPTION = f"Scraped from {TERM_DATES_URL}"
MARKER_PROP = "schoolTermDates"   # private extended property: marks our events
KEY_PROP = "schoolTermKey"        # private extended property: stable identity
COLOR_TERM = "10"                 # basil green

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DAY = r"(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day"
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_TOKEN = re.compile(rf"({DAY})\s+(\d{{1,2}})\s+({MONTH})(?:\s+(\d{{4}}))?")
YEAR_HEADING = re.compile(r"^Term Dates\s+(\d{4})\s*[-–]\s*(\d{4})$")
NOTE = re.compile(r"\(([^)]*)\)\s*$")

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


def fetch_lines() -> list[str]:
    resp = requests.get(TERM_DATES_URL, timeout=30, headers={"User-Agent": "term-dates-sync/1.0"})
    resp.raise_for_status()
    text = re.sub(r"(?s)<(script|style).*?</\1>", "", resp.text)
    text = re.sub(r"(?i)<(br|/p|/li|/tr|/h\d|/div|/td)[^>]*>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    text = text.replace(" ", " ")
    return [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]


def parse_entry(line: str, academic_year: str) -> dict:
    """Parse e.g. 'Autumn Half-TermMonday 19 October – Friday 30 October 2026 inclusive'."""
    tokens = list(DATE_TOKEN.finditer(line))
    if not tokens or len(tokens) > 2:
        raise ValueError(f"Cannot find 1-2 dates in: {line!r}")

    label = line[: tokens[0].start()].strip()
    if not label:
        raise ValueError(f"No label before date in: {line!r}")

    fallback_year = next((t.group(4) for t in reversed(tokens) if t.group(4)), None)
    if not fallback_year:
        raise ValueError(f"No year in: {line!r}")

    dates = []
    for t in tokens:
        weekday, d, month, year = t.groups()
        parsed = datetime.strptime(f"{d} {month} {year or fallback_year}", "%d %B %Y").date()
        if parsed.strftime("%A") != weekday:
            raise ValueError(f"Weekday mismatch ({weekday} vs {parsed}) in: {line!r}")
        dates.append(parsed)

    note_match = NOTE.search(line)
    note = note_match.group(1) if note_match else ""
    start, end = dates[0], dates[-1]
    if end < start:
        raise ValueError(f"End before start in: {line!r}")

    title = f"{EVENT_PREFIX}{label}" + (f" ({note})" if note else "")
    return {
        "key": f"{academic_year}|{label}",
        "title": title,
        "start": start,
        "end": end,  # inclusive
    }


def scrape_term_dates() -> list[dict]:
    lines = fetch_lines()

    entries: list[dict] = []
    academic_year = None
    pending = ""  # label text whose date sits on the next line
    for line in lines:
        m = YEAR_HEADING.match(line)
        if m:
            if pending:
                raise ValueError(f"Label with no date: {pending!r}")
            academic_year = f"{m.group(1)}-{m.group(2)}"
            continue
        if academic_year is None:
            continue
        if line.lower().startswith("any questions about term dates"):
            break
        line = f"{pending} {line}".strip() if pending else line
        if not DATE_TOKEN.search(line):
            pending = line
            continue
        pending = ""
        # Everything between the year headings and the footer must parse.
        entries.append(parse_entry(line, academic_year))
    if pending:
        raise ValueError(f"Label with no date: {pending!r}")

    if not entries:
        raise RuntimeError("No term-date entries found; page layout may have changed.")

    keys = [e["key"] for e in entries]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Duplicate event keys parsed; page layout may have changed.")
    return entries


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------


def get_calendar_service():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if not creds_path or not os.path.isfile(creds_path):
        sys.exit("ERROR: Set GOOGLE_CREDENTIALS_PATH to the service account JSON key file.")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds)


def event_body(entry: dict) -> dict:
    return {
        "summary": entry["title"],
        "description": EVENT_DESCRIPTION,
        "start": {"date": entry["start"].isoformat()},
        "end": {"date": (entry["end"] + timedelta(days=1)).isoformat()},
        "colorId": COLOR_TERM,
        "extendedProperties": {"private": {MARKER_PROP: "1", KEY_PROP: entry["key"]}},
    }


def get_existing_events(cal) -> dict[str, dict]:
    existing: dict[str, dict] = {}
    page_token = None
    while True:
        result = cal.events().list(
            calendarId=CALENDAR_ID,
            privateExtendedProperty=f"{MARKER_PROP}=1",
            maxResults=250,
            pageToken=page_token,
        ).execute()
        for ev in result.get("items", []):
            key = ev.get("extendedProperties", {}).get("private", {}).get(KEY_PROP)
            if key:
                existing[key] = ev
        page_token = result.get("nextPageToken")
        if not page_token:
            return existing


def main():
    dry_run = "--dry-run" in sys.argv
    entries = scrape_term_dates()
    log.info(f"Parsed {len(entries)} term-date entries")
    for e in entries:
        span = e["start"] if e["start"] == e["end"] else f"{e['start']} to {e['end']}"
        log.info(f"  {e['key']}: {span}")
    if dry_run:
        return

    cal = get_calendar_service()
    existing = get_existing_events(cal)
    wanted = {e["key"]: e for e in entries}
    today = date.today().isoformat()

    created = updated = deleted = 0
    for key, entry in wanted.items():
        body = event_body(entry)
        ev = existing.get(key)
        if ev is None:
            cal.events().insert(calendarId=CALENDAR_ID, body=body).execute()
            log.info(f"  CREATED: {entry['title']} ({entry['start']})")
            created += 1
        elif (
            ev.get("summary") != body["summary"]
            or ev.get("start", {}).get("date") != body["start"]["date"]
            or ev.get("end", {}).get("date") != body["end"]["date"]
        ):
            cal.events().patch(calendarId=CALENDAR_ID, eventId=ev["id"], body=body).execute()
            log.info(f"  UPDATED: {entry['title']} ({entry['start']})")
            updated += 1

    for key, ev in existing.items():
        # Only remove future events that vanished from the page; keep history.
        if key not in wanted and ev.get("start", {}).get("date", "") >= today:
            cal.events().delete(calendarId=CALENDAR_ID, eventId=ev["id"]).execute()
            log.info(f"  DELETED: {ev.get('summary')} ({ev['start']['date']})")
            deleted += 1

    log.info(f"Done: {created} created, {updated} updated, {deleted} deleted")


if __name__ == "__main__":
    main()
