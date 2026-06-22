#!/usr/bin/env python3
"""
Fetch upcoming Google Calendar events within CALENDAR_PREP_LEAD_DAYS.

Usage:
    python3 tools/fetch_calendar_events.py

Output:
    JSON array of events to stdout:
    [{"id": "cal:<event_id>", "title": "...", "start": "YYYY-MM-DDTHH:MM:SS",
      "end": "...", "attendees": 3, "description": "...", "link": "..."}]

Exits with code 1 on auth/API error.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
CREDS_FILE = os.path.join(BASE_DIR, "credentials.json")


def load_credentials():
    if not os.path.exists(TOKEN_FILE):
        print("ERROR: token.json not found. Run tools/auth_google.py first.", file=sys.stderr)
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def main():
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    lead_days = int(os.getenv("CALENDAR_PREP_LEAD_DAYS", "2"))

    creds = load_credentials()
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=lead_days)).isoformat()

    try:
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            )
            .execute()
        )
    except HttpError as e:
        print(f"ERROR: Google Calendar API error: {e}", file=sys.stderr)
        sys.exit(1)

    raw_events = result.get("items", [])
    events = []

    for ev in raw_events:
        start = ev.get("start", {})
        start_str = start.get("dateTime") or start.get("date", "")
        end = ev.get("end", {})
        end_str = end.get("dateTime") or end.get("date", "")
        attendees = ev.get("attendees", [])
        link = ev.get("htmlLink", "")

        events.append(
            {
                "id": f"cal:{ev['id']}",
                "title": ev.get("summary", "(sans titre)"),
                "start": start_str,
                "end": end_str,
                "attendees": len(attendees),
                "is_all_day": "date" in start and "dateTime" not in start,
                "description": ev.get("description", ""),
                "link": link,
            }
        )

    print(json.dumps(events, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
