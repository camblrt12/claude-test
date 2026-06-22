#!/usr/bin/env python3
"""One-time script to authorize Google Calendar access and generate token.json."""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


def main():
    with open(CREDS_FILE) as f:
        raw = json.load(f)

    # InstalledAppFlow expects "installed" key; remap "web" if needed
    if "web" in raw and "installed" not in raw:
        client_config = {"installed": raw["web"]}
    else:
        client_config = raw

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"token.json saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
