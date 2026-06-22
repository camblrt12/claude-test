"""
Usage: python tools/check_processed.py '<json_array_of_ids>'
Prints a JSON array of IDs from the input that have NOT been processed before.
Creates .tmp/processed_ids.json if it doesn't exist.
"""

import json
import sys
from pathlib import Path

LEDGER = Path("processed_ids.json")


def load_ledger() -> set:
    if not LEDGER.exists():
        return set()
    with open(LEDGER) as f:
        return set(json.load(f))


def main():
    if len(sys.argv) < 2:
        print("[]")
        return

    input_ids = json.loads(sys.argv[1])
    seen = load_ledger()
    new_ids = [id_ for id_ in input_ids if id_ not in seen]
    print(json.dumps(new_ids))


if __name__ == "__main__":
    main()
