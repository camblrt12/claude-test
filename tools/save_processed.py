"""
Usage: python tools/save_processed.py '<json_array_of_ids>'
Appends the given IDs to .tmp/processed_ids.json.
Creates the file and .tmp/ directory if they don't exist.
"""

import json
import sys
from pathlib import Path

LEDGER = Path("processed_ids.json")


def main():
    if len(sys.argv) < 2:
        return

    new_ids = json.loads(sys.argv[1])
    if not new_ids:
        return

    existing = set()
    if LEDGER.exists():
        with open(LEDGER) as f:
            existing = set(json.load(f))

    merged = list(existing | set(new_ids))

    with open(LEDGER, "w") as f:
        json.dump(merged, f, indent=2)


if __name__ == "__main__":
    main()
