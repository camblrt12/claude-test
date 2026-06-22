"""
Usage: python tools/merge_tasks.py '<json_array_of_tasks>'
Fuzzy-deduplicates tasks by title across sources.
When two tasks have near-identical titles (edit distance < 15% of longer title),
they are merged into one entry with combined source info.
Prints the deduplicated JSON array.
"""

import json
import sys


def edit_distance(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def are_duplicates(title_a: str, title_b: str) -> bool:
    longer = max(len(title_a), len(title_b))
    if longer == 0:
        return True
    dist = edit_distance(title_a, title_b)
    return dist / longer < 0.15


def merge_pair(a: dict, b: dict) -> dict:
    merged = dict(a)
    sources = set()
    for s in [a.get("source", ""), b.get("source", "")]:
        sources.update(s.split(" + "))
    sources.discard("")
    merged["source"] = " + ".join(sorted(sources))
    if not merged.get("due_date") and b.get("due_date"):
        merged["due_date"] = b["due_date"]
    if not merged.get("from") and b.get("from"):
        merged["from"] = b["from"]
    return merged


def main():
    if len(sys.argv) < 2:
        print("[]")
        return

    tasks = json.loads(sys.argv[1])
    if not tasks:
        print("[]")
        return

    merged: list[dict] = []
    for task in tasks:
        matched = False
        for i, existing in enumerate(merged):
            if are_duplicates(task.get("tache", ""), existing.get("tache", "")):
                merged[i] = merge_pair(existing, task)
                matched = True
                break
        if not matched:
            merged.append(task)

    print(json.dumps(merged, ensure_ascii=False))


if __name__ == "__main__":
    main()
